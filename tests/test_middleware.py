"""Tests for the tool-call middleware."""

from __future__ import annotations

import json
import logging

import httpx
import pytest
from fastmcp import Client
from fastmcp.tools import ToolResult
from mcp.types import CallToolRequestParams, CallToolResult
from mcp_server_check.errors import CheckToolError
from mcp_server_check.middleware import (
    ResponseSize,
    ResponseSizeLimitMiddleware,
    ToolCall,
)
from mcp_server_check.server import CheckMCP, lifespan, setup_tools
from mcp_server_check.tool_filter import ToolFilter

JOURNAL_ARGUMENTS = {
    "company_id": "com_001",
    "report_type": "payroll_journal",
    "start_date": "2026-09-13",
    "end_date": "2026-09-19",
}
SMALL_LIMIT = "2000"


def journal(rows: int) -> dict:
    return {
        "results": [
            {"employee": f"emp_{row:06d}", "name": 'Jane "JD" Doe', "gross": "1000.00"}
            for row in range(rows)
        ]
    }


@pytest.fixture
def journal_route(mock_api):
    return mock_api.get("/companies/com_001/reports/payroll_journal")


@pytest.fixture
def make_server(monkeypatch):
    monkeypatch.setenv("CHECK_API_KEY", "test-key")
    monkeypatch.delenv("CHECK_API_BASE_URL", raising=False)
    monkeypatch.delenv(ResponseSizeLimitMiddleware.ENV_VAR, raising=False)

    def make(tool_mode: str, tool_filter: ToolFilter | None = None) -> CheckMCP:
        server = CheckMCP("Test", lifespan=lifespan)
        if tool_filter is not None:
            server._static_filter = tool_filter
        setup_tools(server, tool_mode=tool_mode)
        return server

    return make


async def call(server: CheckMCP, tool_mode: str, name: str, arguments: dict):
    if tool_mode == "dynamic":
        name, arguments = ToolCall.RUN_TOOL, {"tool_name": name, "arguments": arguments}
    async with Client(server) as client:
        return await client.call_tool(name, arguments, raise_on_error=False)


def error_of(result) -> dict:
    assert result.is_error is True, "error_of: Expected a tool error"
    return json.loads(result.content[0].text)


class TestToolCall:
    @pytest.mark.parametrize(
        "inner_arguments",
        [JOURNAL_ARGUMENTS, json.dumps(JOURNAL_ARGUMENTS)],
        ids=["dict", "json string"],
    )
    def test_unwraps_run_tool(self, inner_arguments):
        params = CallToolRequestParams(
            name="run_tool",
            arguments={"tool_name": "get_company_report", "arguments": inner_arguments},
        )

        assert ToolCall.from_request(params) == ToolCall(
            "get_company_report", JOURNAL_ARGUMENTS
        )

    def test_keeps_direct_call(self):
        params = CallToolRequestParams(
            name="get_company", arguments={"company_id": "com_001"}
        )

        assert ToolCall.from_request(params) == ToolCall(
            "get_company", {"company_id": "com_001"}
        )

    @pytest.mark.parametrize(
        ("arguments", "expected"),
        [
            pytest.param(
                {"tool_name": "get_company", "arguments": "{"},
                ToolCall("get_company", {}),
                id="malformed json",
            ),
            pytest.param(
                {"tool_name": "get_company", "arguments": "[1]"},
                ToolCall("get_company", {}),
                id="json array",
            ),
            pytest.param({}, ToolCall("run_tool", {}), id="no tool name"),
        ],
    )
    def test_request_with_bad_run_tool_arguments_reads_as_none(
        self, arguments, expected
    ):
        params = CallToolRequestParams(name="run_tool", arguments=arguments)

        assert ToolCall.from_request(params) == expected

    @pytest.mark.parametrize(
        ("arguments", "message"),
        [
            ("{", "Invalid JSON arguments"),
            ("[1]", "Arguments must be a JSON object"),
            (7, "Arguments must be a JSON string or object"),
        ],
    )
    def test_from_run_tool_rejects_bad_arguments(self, arguments, message):
        with pytest.raises(CheckToolError) as excinfo:
            ToolCall.from_run_tool("get_company", arguments)

        assert excinfo.value.payload["error"].startswith(message)


class TestResponseSize:
    @pytest.mark.parametrize(
        "content", ['say "hi"', "back\\slash", "new\nline", "é", '{"a": [1]}']
    )
    def test_lambda_proxy_matches_escaping_the_body_again(self, content):
        result = ToolResult(content=content)
        body = CallToolResult(content=result.content).model_dump_json(
            by_alias=True, exclude_none=True
        )

        assert ResponseSize.lambda_proxy(result) == len(
            json.dumps(body, ensure_ascii=False).encode()
        )

    def test_non_ascii_counts_as_utf8(self):
        ascii_size = ResponseSize.lambda_proxy(ToolResult(content="e"))

        assert ResponseSize.lambda_proxy(ToolResult(content="é")) == ascii_size + 1


class TestResponseSizeLimitMiddleware:
    @pytest.mark.anyio
    @pytest.mark.parametrize("tool_mode", ["all", "dynamic"])
    async def test_oversized_report_is_explained_tool_error(
        self, journal_route, make_server, monkeypatch, caplog, tool_mode
    ):
        journal_route.mock(return_value=httpx.Response(200, json=journal(100)))
        monkeypatch.setenv(ResponseSizeLimitMiddleware.ENV_VAR, SMALL_LIMIT)

        with caplog.at_level(logging.WARNING, logger="mcp_server_check.middleware"):
            result = await call(
                make_server(tool_mode),
                tool_mode,
                "get_company_report",
                JOURNAL_ARGUMENTS,
            )

        error = error_of(result)
        assert caplog.messages == [
            "Tool result exceeds the response size limit: "
            f"tool=get_company_report size={error['size']} limit={SMALL_LIMIT}"
        ]
        assert error["response_too_large"] is True
        assert error["size"] > error["limit"] == int(SMALL_LIMIT)
        assert [a["tool"] for a in error["alternatives"]] == [
            "create_report_run",
            "get_company_report",
        ]
        assert error["alternatives"][1]["arguments"] == {
            **JOURNAL_ARGUMENTS,
            "response_format": "csv",
        }
        assert len(error["hints"]) == 2

    @pytest.mark.anyio
    @pytest.mark.parametrize("tool_mode", ["all", "dynamic"])
    async def test_result_under_limit_is_returned(
        self, journal_route, make_server, tool_mode
    ):
        journal_route.mock(return_value=httpx.Response(200, json=journal(10)))

        result = await call(
            make_server(tool_mode), tool_mode, "get_company_report", JOURNAL_ARGUMENTS
        )

        assert result.is_error is False
        assert len(json.loads(result.content[0].text)["results"]) == 10

    @pytest.mark.anyio
    async def test_oversized_result_of_other_tool_has_no_remedies(
        self, mock_api, make_server, monkeypatch
    ):
        monkeypatch.setenv(ResponseSizeLimitMiddleware.ENV_VAR, "200")
        mock_api.get("/companies/com_001").mock(
            return_value=httpx.Response(200, json={"id": "com_001", "notes": "x" * 500})
        )

        result = await call(
            make_server("all"), "all", "get_company", {"company_id": "com_001"}
        )

        error = error_of(result)
        assert error["detail"].startswith("The get_company result is")
        assert "alternatives" not in error
        assert "hints" not in error

    def test_default_limit(self, make_server):
        limits = [
            middleware.max_bytes
            for middleware in make_server("all").middleware
            if isinstance(middleware, ResponseSizeLimitMiddleware)
        ]

        assert limits == [ResponseSizeLimitMiddleware.DEFAULT_MAX_BYTES]

    def test_zero_disables_the_limit(self, monkeypatch):
        monkeypatch.setenv(ResponseSizeLimitMiddleware.ENV_VAR, "0")

        assert ResponseSizeLimitMiddleware.from_env() is None

    def test_non_integer_limit_names_the_variable(self, monkeypatch):
        monkeypatch.setenv(ResponseSizeLimitMiddleware.ENV_VAR, "6MB")

        with pytest.raises(ValueError, match="CHECK_MAX_RESPONSE_BYTES must be"):
            ResponseSizeLimitMiddleware.from_env()

    def test_rejects_non_positive_limit(self):
        with pytest.raises(ValueError, match="max_bytes must be positive"):
            ResponseSizeLimitMiddleware(max_bytes=0)


class TestRecoveryMiddleware:
    @pytest.mark.anyio
    @pytest.mark.parametrize("tool_mode", ["all", "dynamic"])
    async def test_timeout_offers_report_run(
        self, journal_route, make_server, tool_mode
    ):
        journal_route.mock(side_effect=httpx.ReadTimeout("timed out"))

        result = await call(
            make_server(tool_mode), tool_mode, "get_company_report", JOURNAL_ARGUMENTS
        )

        error = error_of(result)
        assert error["timeout"] is True
        assert error["detail"] == "timed out"
        assert [a["tool"] for a in error["alternatives"]] == ["create_report_run"]
        assert len(error["hints"]) == 2

    @pytest.mark.anyio
    async def test_read_only_keeps_only_hints(self, journal_route, make_server):
        journal_route.mock(side_effect=httpx.ReadTimeout("timed out"))
        server = make_server("dynamic", ToolFilter(read_only=True))

        result = await call(server, "dynamic", "get_company_report", JOURNAL_ARGUMENTS)

        error = error_of(result)
        assert error["alternatives"] == []
        assert len(error["hints"]) == 2

    @pytest.mark.anyio
    async def test_timeout_without_remedies_is_unchanged(self, mock_api, make_server):
        mock_api.get("/companies/com_001/reports/applied_for_ids_detailed").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )

        result = await call(
            make_server("all"),
            "all",
            "get_company_report",
            {"company_id": "com_001", "report_type": "applied_for_ids_detailed"},
        )

        assert error_of(result) == {
            "error": True,
            "timeout": True,
            "detail": "timed out",
        }

    @pytest.mark.anyio
    async def test_other_api_errors_pass_through(self, journal_route, make_server):
        journal_route.mock(
            return_value=httpx.Response(400, json={"error": "Bad range"})
        )

        result = await call(
            make_server("all"), "all", "get_company_report", JOURNAL_ARGUMENTS
        )

        assert error_of(result) == {
            "error": True,
            "status_code": 400,
            "detail": {"error": "Bad range"},
        }


class TestIsToolAvailable:
    @pytest.mark.parametrize("tool_mode", ["all", "dynamic"])
    @pytest.mark.parametrize(
        ("tool_filter", "tool", "expected"),
        [
            pytest.param(ToolFilter(), "create_report_run", True, id="allowed"),
            pytest.param(
                ToolFilter(read_only=True), "create_report_run", False, id="read-only"
            ),
            pytest.param(
                ToolFilter(toolsets=frozenset({"companies"})),
                "create_report_run",
                False,
                id="other toolset",
            ),
            pytest.param(ToolFilter(), "no_such_tool", False, id="unknown"),
        ],
    )
    def test_follows_the_active_filter(
        self, make_server, tool_mode, tool_filter, tool, expected
    ):
        server = make_server(tool_mode, tool_filter)

        assert server.is_tool_available(tool) is expected


class TestToolResultShape:
    @pytest.mark.anyio
    @pytest.mark.parametrize("tool_mode", ["all", "dynamic"])
    async def test_result_is_sent_once(self, journal_route, make_server, tool_mode):
        journal_route.mock(return_value=httpx.Response(200, json=journal(10)))

        result = await call(
            make_server(tool_mode), tool_mode, "get_company_report", JOURNAL_ARGUMENTS
        )

        assert result.structured_content is None
        assert len(result.content) == 1
        assert len(json.loads(result.content[0].text)["results"]) == 10

    @pytest.mark.anyio
    async def test_run_tool_invalid_arguments_are_a_json_error(self, make_server):
        result = await call(make_server("dynamic"), "dynamic", "get_company", {})

        assert "validation error" in error_of(result)["error"]

    @pytest.mark.anyio
    @pytest.mark.parametrize("tool_mode", ["all", "dynamic"])
    async def test_api_error_logged_as_warning(
        self, mock_api, make_server, caplog, tool_mode
    ):
        mock_api.get("/companies/com_404").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )

        # fastmcp's logger does not propagate to the root logger caplog watches.
        fastmcp_logger = logging.getLogger("fastmcp.server.server")
        fastmcp_logger.addHandler(caplog.handler)
        try:
            await call(
                make_server(tool_mode),
                tool_mode,
                "get_company",
                {"company_id": "com_404"},
            )
        finally:
            fastmcp_logger.removeHandler(caplog.handler)

        tool_logs = [r for r in caplog.records if "Error calling tool" in r.message]
        assert [r.levelno for r in tool_logs] == [logging.WARNING]
