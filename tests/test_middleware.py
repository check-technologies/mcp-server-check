"""Tests for the tool-call middleware."""

from __future__ import annotations

import json

import httpx
import pytest
from fastmcp import Client
from mcp.types import CallToolRequestParams
from mcp_server_check.middleware import ResponseSizeLimitMiddleware, ToolCall
from mcp_server_check.server import CheckMCP, lifespan, setup_tools
from mcp_server_check.tool_filter import ToolFilter

JOURNAL_ARGUMENTS = {
    "company_id": "com_001",
    "report_type": "payroll_journal",
    "start_date": "2026-09-13",
    "end_date": "2026-09-19",
}


def journal(rows: int) -> dict:
    return {
        "results": [
            {
                "employee": f"emp_{row:06d}",
                "name": 'Jane "JD" Doe',
                "gross_pay": "1000.00",
                "taxes": [{"name": "FICA", "amount": "62.00"}],
            }
            for row in range(rows)
        ]
    }


def tool_call(tool_mode: str, name: str, arguments: dict) -> tuple[str, dict]:
    if tool_mode == "all":
        return name, arguments
    return "run_tool", {"tool_name": name, "arguments": arguments}


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
    async with Client(server) as client:
        return await client.call_tool(
            *tool_call(tool_mode, name, arguments), raise_on_error=False
        )


class TestToolCall:
    @pytest.mark.parametrize(
        "inner_arguments",
        [JOURNAL_ARGUMENTS, json.dumps(JOURNAL_ARGUMENTS)],
        ids=["dict", "json string"],
    )
    def test_unwraps_run_tool(self, inner_arguments):
        params = CallToolRequestParams(
            name="run_tool",
            arguments={
                "tool_name": "get_company_report",
                "arguments": inner_arguments,
            },
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

    def test_ignores_malformed_run_tool_arguments(self):
        params = CallToolRequestParams(
            name="run_tool", arguments={"tool_name": "get_company", "arguments": "{"}
        )

        assert ToolCall.from_request(params) == ToolCall("get_company", {})


class TestResponseSizeLimitMiddleware:
    @pytest.mark.anyio
    @pytest.mark.parametrize("tool_mode", ["all", "dynamic"])
    async def test_oversized_report_is_explained_tool_error(
        self, mock_api, make_server, tool_mode
    ):
        mock_api.get("/companies/com_001/reports/payroll_journal").mock(
            return_value=httpx.Response(200, json=journal(50_000))
        )

        result = await call(
            make_server(tool_mode), tool_mode, "get_company_report", JOURNAL_ARGUMENTS
        )

        error = json.loads(result.content[0].text)
        assert result.is_error is True
        assert error["response_too_large"] is True
        assert (
            error["size"]
            > error["limit"]
            == (ResponseSizeLimitMiddleware.DEFAULT_MAX_BYTES)
        )
        assert [alternative["tool"] for alternative in error["alternatives"]] == [
            "create_report_run",
            "get_company_report",
            "get_company_report",
            "get_company_report",
        ]

    @pytest.mark.anyio
    @pytest.mark.parametrize("tool_mode", ["all", "dynamic"])
    async def test_result_under_limit_is_returned(
        self, mock_api, make_server, tool_mode
    ):
        mock_api.get("/companies/com_001/reports/payroll_journal").mock(
            return_value=httpx.Response(200, json=journal(10))
        )

        result = await call(
            make_server(tool_mode), tool_mode, "get_company_report", JOURNAL_ARGUMENTS
        )

        assert result.is_error is False
        assert len(json.loads(result.content[0].text)["results"]) == 10

    @pytest.mark.anyio
    async def test_oversized_result_of_other_tool_has_no_alternatives(
        self, mock_api, make_server, monkeypatch
    ):
        monkeypatch.setenv(ResponseSizeLimitMiddleware.ENV_VAR, "200")
        mock_api.get("/companies/com_001").mock(
            return_value=httpx.Response(200, json={"id": "com_001", "notes": "x" * 500})
        )

        result = await call(
            make_server("all"), "all", "get_company", {"company_id": "com_001"}
        )

        error = json.loads(result.content[0].text)
        assert result.is_error is True
        assert error["detail"].startswith("The get_company result is")
        assert "alternatives" not in error

    @pytest.mark.anyio
    async def test_zero_disables_the_limit(self, mock_api, make_server, monkeypatch):
        monkeypatch.setenv(ResponseSizeLimitMiddleware.ENV_VAR, "0")
        mock_api.get("/companies/com_001/reports/payroll_journal").mock(
            return_value=httpx.Response(200, json=journal(100))
        )
        server = make_server("all")

        result = await call(server, "all", "get_company_report", JOURNAL_ARGUMENTS)

        assert result.is_error is False
        assert not any(
            isinstance(middleware, ResponseSizeLimitMiddleware)
            for middleware in server.middleware
        )

    def test_rejects_non_positive_limit(self):
        with pytest.raises(ValueError, match="max_bytes must be positive"):
            ResponseSizeLimitMiddleware(max_bytes=0)


class TestReportAlternativesMiddleware:
    @pytest.mark.anyio
    @pytest.mark.parametrize("tool_mode", ["all", "dynamic"])
    async def test_timeout_offers_report_run(self, mock_api, make_server, tool_mode):
        mock_api.get("/companies/com_001/reports/payroll_journal").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )

        result = await call(
            make_server(tool_mode), tool_mode, "get_company_report", JOURNAL_ARGUMENTS
        )

        error = json.loads(result.content[0].text)
        assert result.is_error is True
        assert error["timeout"] is True
        assert error["detail"] == "timed out"
        assert [alternative["tool"] for alternative in error["alternatives"]] == [
            "create_report_run",
            "get_company_report",
            "get_company_report",
        ]

    @pytest.mark.anyio
    async def test_read_only_timeout_skips_report_run(self, mock_api, make_server):
        mock_api.get("/companies/com_001/reports/payroll_journal").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        server = make_server("dynamic", ToolFilter(read_only=True))

        result = await call(server, "dynamic", "get_company_report", JOURNAL_ARGUMENTS)

        error = json.loads(result.content[0].text)
        assert "create_report_run" not in {
            alternative["tool"] for alternative in error["alternatives"]
        }

    @pytest.mark.anyio
    async def test_other_api_errors_pass_through(self, mock_api, make_server):
        mock_api.get("/companies/com_001/reports/payroll_journal").mock(
            return_value=httpx.Response(400, json={"error": "Bad range"})
        )

        result = await call(
            make_server("all"), "all", "get_company_report", JOURNAL_ARGUMENTS
        )

        assert json.loads(result.content[0].text) == {
            "error": True,
            "status_code": 400,
            "detail": {"error": "Bad range"},
        }


class TestRunToolResult:
    @pytest.mark.anyio
    async def test_result_is_sent_once(self, mock_api, make_server):
        mock_api.get("/companies/com_001/reports/payroll_journal").mock(
            return_value=httpx.Response(200, json=journal(10))
        )

        result = await call(
            make_server("dynamic"), "dynamic", "get_company_report", JOURNAL_ARGUMENTS
        )

        assert result.structured_content is None
        assert len(result.content) == 1
        assert len(json.loads(result.content[0].text)["results"]) == 10
