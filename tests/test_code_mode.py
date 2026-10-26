"""Tests for code mode: run_code, get_stubs, and stub rendering."""

from __future__ import annotations

import json

import httpx
import pytest
from fastmcp import Client
from mcp.server.lowlevel.server import Server
from mcp_server_check.code_mode import (
    CodeModeSettings,
    render_signature,
    render_stub,
    render_stubs,
)
from mcp_server_check.server import (
    CheckMCP,
    lifespan,
    resolve_tool_mode,
    setup_tools,
)
from mcp_server_check.tool_filter import ToolFilter
from mcp_server_check.tool_index import ToolIndex

COMPANIES = {
    "results": [
        {"id": "com_1", "legal_name": "Acme", "secret_field": "x"},
        {"id": "com_2", "legal_name": "Beta", "secret_field": "y"},
    ],
    "next": None,
    "previous": None,
}


@pytest.fixture(scope="module")
def index() -> ToolIndex:
    idx = ToolIndex()
    idx.build()
    return idx


@pytest.fixture
def code_server(monkeypatch):
    monkeypatch.setenv("CHECK_API_KEY", "test-key")
    monkeypatch.delenv("CHECK_API_BASE_URL", raising=False)
    monkeypatch.setenv("CHECK_CODE_TIMEOUT_SECS", "20")
    server = CheckMCP("Test Code", lifespan=lifespan)
    setup_tools(server, tool_mode="code")
    return server


@pytest.fixture
def dynamic_server(monkeypatch):
    """A plain dynamic-mode server: code mode is off unless a request opts in."""
    monkeypatch.setenv("CHECK_API_KEY", "test-key")
    monkeypatch.delenv("CHECK_API_BASE_URL", raising=False)
    monkeypatch.delenv("CHECK_CODE_MODE", raising=False)
    monkeypatch.delenv("CHECK_TOOL_MODE", raising=False)
    monkeypatch.setenv("CHECK_CODE_TIMEOUT_SECS", "20")
    server = CheckMCP("Test Dynamic", lifespan=lifespan)
    setup_tools(server, tool_mode="dynamic")
    return server


class _FakeRequest:
    """The parts of a Starlette request the server and fastmcp read."""

    def __init__(self, headers=None, query_params=None):
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.scope: dict = {}


class _WithRequest:
    """A real request context whose request is replaced."""

    def __init__(self, real, request):
        self._real = real
        self.request = request

    def __getattr__(self, name):
        return getattr(self._real, name)


def _attach_request(monkeypatch, request: _FakeRequest) -> None:
    """Make every request context in this test carry the given HTTP request."""
    real = Server.request_context
    monkeypatch.setattr(
        Server,
        "request_context",
        property(lambda self: _WithRequest(real.fget(self), request)),
    )


async def _run(server: CheckMCP, code: str, writes: list[str] | None = None):
    """Call run_code and return (is_error, parsed payload)."""
    arguments: dict = {"code": code}
    if writes is not None:
        arguments["writes"] = writes
    async with Client(server) as client:
        result = await client.call_tool("run_code", arguments, raise_on_error=False)
    return result.is_error, json.loads(result.content[0].text)


# --- stub rendering ---


class TestStubs:
    def test_signature_skips_context_and_keeps_defaults(self, index):
        sig = render_signature(index.get_entry("list_companies"))
        assert sig.startswith("async def list_companies(")
        assert "ctx" not in sig
        assert "limit: int | None = None" in sig
        assert sig.endswith(") -> Any")

    def test_factory_generated_tool_renders_real_types(self, index):
        sig = render_signature(index.get_entry("get_benefit"))
        assert "ctx" not in sig
        assert "benefit_id: str" in sig

    def test_stub_carries_docstring(self, index):
        stub = render_stub(index.get_entry("list_companies"))
        assert "List companies in your Check account." in stub
        assert "cursor: Pagination cursor" in stub
        assert stub.rstrip().endswith("...")

    def test_write_tools_are_marked_only_when_asked(self, index):
        entry = index.get_entry("create_company")
        assert "# write tool" in render_stub(entry, mark_writes=True)
        assert "# write tool" not in render_stub(entry)
        read = index.get_entry("get_company")
        assert "# write tool" not in render_stub(read, mark_writes=True)

    def test_stubs_group_by_toolset_and_declare_typed_dicts(self, index):
        stubs = render_stubs(index.entries.values())
        assert "# ---- companies ----" in stubs
        assert "class Address(TypedDict, total=False):" in stubs
        assert "from typing import Any" in stubs


# --- mode resolution ---


class TestResolveToolMode:
    def test_default_is_dynamic(self, monkeypatch):
        monkeypatch.delenv("CHECK_TOOL_MODE", raising=False)
        monkeypatch.delenv("CHECK_CODE_MODE", raising=False)
        assert resolve_tool_mode() == "dynamic"

    def test_tool_mode_code(self, monkeypatch):
        monkeypatch.setenv("CHECK_TOOL_MODE", "code")
        monkeypatch.delenv("CHECK_CODE_MODE", raising=False)
        assert resolve_tool_mode() == "code"

    def test_code_mode_flag_wins(self, monkeypatch):
        monkeypatch.setenv("CHECK_TOOL_MODE", "all")
        monkeypatch.setenv("CHECK_CODE_MODE", "1")
        assert resolve_tool_mode() == "code"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("CHECK_CODE_TIMEOUT_SECS", "5")
    monkeypatch.setenv("CHECK_CODE_MAX_CALLS", "7")
    monkeypatch.setenv("CHECK_CODE_MAX_MEMORY_MB", "1")
    monkeypatch.setenv("CHECK_CODE_CONCURRENCY", "2")
    monkeypatch.setenv("CHECK_CODE_MAX_RETRIES", "1")
    settings = CodeModeSettings.from_env()
    assert settings == CodeModeSettings(
        timeout_secs=5,
        max_calls=7,
        max_memory_bytes=1024 * 1024,
        concurrency=2,
        max_retries=1,
    )


# --- server surface ---


@pytest.mark.anyio
async def test_code_mode_exposes_meta_tools(code_server):
    async with Client(code_server) as client:
        names = {t.name for t in await client.list_tools()}
    assert names == {
        "search_tools",
        "list_toolsets",
        "run_tool",
        "get_stubs",
        "run_code",
    }


# --- enabling code mode per request ---


class TestCodeModeFlag:
    def test_header(self):
        assert ToolFilter.from_headers({"x-mcp-code-mode": "1"}).code_mode is True
        assert ToolFilter.from_headers({"x-mcp-code-mode": "0"}).code_mode is False
        assert ToolFilter.from_headers({}).code_mode is False

    def test_query_param(self):
        assert ToolFilter.from_query_params({"code_mode": "true"}).code_mode is True
        assert ToolFilter.from_query_params({}).code_mode is False

    def test_env_shorthand_and_tool_mode(self, monkeypatch):
        monkeypatch.delenv("CHECK_CODE_MODE", raising=False)
        monkeypatch.delenv("CHECK_TOOL_MODE", raising=False)
        assert ToolFilter.from_env().code_mode is False
        monkeypatch.setenv("CHECK_CODE_MODE", "1")
        assert ToolFilter.from_env().code_mode is True
        monkeypatch.delenv("CHECK_CODE_MODE")
        monkeypatch.setenv("CHECK_TOOL_MODE", "code")
        assert ToolFilter.from_env().code_mode is True

    def test_either_side_can_opt_in(self):
        on = ToolFilter(code_mode=True)
        off = ToolFilter()
        assert off.merge(on).code_mode is True
        assert on.merge(off).code_mode is True
        assert off.merge(off).code_mode is False

    def test_opt_in_does_not_relax_policy(self):
        policy = ToolFilter(read_only=True)
        merged = policy.merge(ToolFilter(code_mode=True))
        assert merged.read_only is True
        assert merged.code_mode is True


@pytest.mark.anyio
async def test_dynamic_mode_hides_code_tools_by_default(dynamic_server):
    async with Client(dynamic_server) as client:
        names = {t.name for t in await client.list_tools()}
        assert names == {"search_tools", "list_toolsets", "run_tool"}
        result = await client.call_tool("run_code", {"code": "1"}, raise_on_error=False)
        assert result.is_error
        assert "X-MCP-Code-Mode" in result.content[0].text
        result = await client.call_tool("get_stubs", {}, raise_on_error=False)
        assert result.is_error
        # Without the flag, search results are schemas, not stubs.
        result = await client.call_tool("search_tools", {"query": "list companies"})
        assert "parameters" in json.loads(result.content[0].text)[0]


@pytest.mark.anyio
async def test_header_enables_code_tools_per_request(
    mock_api, monkeypatch, dynamic_server
):
    mock_api.get("/companies").mock(return_value=httpx.Response(200, json=COMPANIES))
    _attach_request(monkeypatch, _FakeRequest(headers={"x-mcp-code-mode": "1"}))
    async with Client(dynamic_server) as client:
        names = {t.name for t in await client.list_tools()}
        assert {"get_stubs", "run_code"} <= names
        result = await client.call_tool(
            "run_code",
            {"code": "page = await check.list_companies()\nlen(page['results'])"},
        )
        assert json.loads(result.content[0].text)["result"] == 2
        result = await client.call_tool("search_tools", {"query": "list companies"})
        assert "stub" in json.loads(result.content[0].text)[0]


@pytest.mark.anyio
async def test_query_param_enables_code_tools_per_request(monkeypatch, dynamic_server):
    _attach_request(monkeypatch, _FakeRequest(query_params={"code_mode": "1"}))
    async with Client(dynamic_server) as client:
        result = await client.call_tool("get_stubs", {"toolset": "workplaces"})
    assert "async def list_workplaces(" in result.content[0].text


@pytest.mark.anyio
async def test_other_headers_leave_code_mode_off(monkeypatch, dynamic_server):
    _attach_request(monkeypatch, _FakeRequest(headers={"x-mcp-readonly": "1"}))
    async with Client(dynamic_server) as client:
        names = {t.name for t in await client.list_tools()}
        assert names == {"search_tools", "list_toolsets", "run_tool"}
        result = await client.call_tool("run_code", {"code": "1"}, raise_on_error=False)
    assert result.is_error
    assert "code mode is off" in result.content[0].text


@pytest.mark.anyio
async def test_header_cannot_relax_server_policy(monkeypatch, dynamic_server):
    """Opting into code mode by header still runs under the env filter."""
    dynamic_server._static_filter = ToolFilter(read_only=True)
    _attach_request(monkeypatch, _FakeRequest(headers={"x-mcp-code-mode": "1"}))
    is_error, payload = await _run(dynamic_server, "1", writes=["create_workplace"])
    assert is_error
    assert "not available" in payload["detail"]


@pytest.mark.anyio
async def test_get_stubs_by_toolset(code_server):
    async with Client(code_server) as client:
        result = await client.call_tool("get_stubs", {"toolset": "workplaces"})
    stubs = result.content[0].text
    assert "async def list_workplaces(" in stubs
    assert "# write tool" in stubs  # create_workplace
    assert "async def list_companies(" not in stubs


@pytest.mark.anyio
async def test_search_tools_returns_stubs_in_code_mode(code_server):
    async with Client(code_server) as client:
        result = await client.call_tool("search_tools", {"query": "list companies"})
    results = json.loads(result.content[0].text)
    assert results[0]["name"] == "list_companies"
    assert results[0]["stub"].startswith("async def list_companies(")
    assert "parameters" not in results[0]


# --- run_code ---


@pytest.mark.anyio
async def test_run_code_chains_calls_in_one_turn(mock_api, code_server):
    mock_api.get("/companies").mock(return_value=httpx.Response(200, json=COMPANIES))
    for cid, state in (("com_1", "CA"), ("com_2", "NY")):
        mock_api.get(f"/companies/{cid}").mock(
            return_value=httpx.Response(
                200, json={"id": cid, "legal_name": "x", "address": {"state": state}}
            )
        )
    code = """
import asyncio
import check

page = await check.list_companies(limit=2)
details = await asyncio.gather(
    *[check.get_company(company_id=c["id"]) for c in page["results"]]
)
print("fetched", len(details))
{"count": page["result_count"], "states": sorted(d["address"]["state"] for d in details)}
"""
    is_error, payload = await _run(code_server, code)

    assert not is_error, payload
    assert payload["result"] == {"count": 2, "states": ["CA", "NY"]}
    assert payload["logs"] == "fetched 2\n"
    assert [c["tool"] for c in payload["calls"]] == [
        "list_companies",
        "get_company",
        "get_company",
    ]
    assert all(c["status"] == "ok" for c in payload["calls"])
    assert payload["calls"][0]["arguments"] == {"limit": 2}
    assert mock_api.calls.call_count == 3


@pytest.mark.anyio
async def test_run_code_needs_no_import(mock_api, code_server):
    mock_api.get("/companies/com_1").mock(
        return_value=httpx.Response(200, json={"id": "com_1"})
    )
    is_error, payload = await _run(
        code_server, '(await check.get_company(company_id="com_1"))["id"]'
    )
    assert not is_error, payload
    assert payload["result"] == "com_1"


@pytest.mark.anyio
async def test_run_code_type_error_line_numbers_match_the_program(
    mock_api, code_server
):
    is_error, payload = await _run(
        code_server, "x = 1\nawait check.get_compny(company_id='com_1')"
    )
    assert is_error
    assert payload["kind"] == "type_check_failed"
    assert "main.py:2:" in payload["detail"]


@pytest.mark.anyio
async def test_run_code_accepts_positional_arguments(mock_api, code_server):
    mock_api.get("/companies/com_1").mock(
        return_value=httpx.Response(200, json={"id": "com_1"})
    )
    is_error, payload = await _run(
        code_server, 'import check\n(await check.get_company("com_1"))["id"]'
    )
    assert not is_error, payload
    assert payload["result"] == "com_1"
    assert payload["calls"][0]["arguments"] == {"company_id": "com_1"}


@pytest.mark.anyio
async def test_run_code_type_error_runs_nothing(mock_api, code_server):
    mock_api.get("/companies/com_1").mock(
        return_value=httpx.Response(200, json={"id": "com_1"})
    )
    is_error, payload = await _run(
        code_server, "import check\nawait check.get_company(compny_id='com_1')"
    )
    assert is_error
    assert payload["kind"] == "type_check_failed"
    assert "company_id" in payload["detail"]
    assert payload["calls"] == []
    assert mock_api.calls.call_count == 0


@pytest.mark.anyio
async def test_run_code_ignores_type_errors_about_its_own_data(mock_api, code_server):
    """Only diagnostics about the check module block a program."""
    mock_api.get("/companies/com_1").mock(
        return_value=httpx.Response(200, json={"id": "com_1"})
    )
    code = """
x: int = "not an int"
(await check.get_company(company_id="com_1"))["id"]
"""
    is_error, payload = await _run(code_server, code)
    assert not is_error, payload
    assert payload["result"] == "com_1"


def test_signature_errors_keep_only_check_module_lines():
    from mcp_server_check.code_mode import signature_errors

    diagnostics = (
        "main.py:1:7: error[unresolved-attribute] Module `check` has no member `x`\n"
        "main.py:2:1: error[invalid-assignment] Object of type `str` is not assignable\n"
        "main.py:3:1: error[unknown-argument] Argument `foo` does not match any known "
        "parameter of function `get_company`\n"
        "main.py:4:1: error[missing-argument] No argument provided for required "
        "parameter `x` of function `page_all`\n"
    )
    errors = signature_errors(diagnostics, ["get_company"])
    assert [e.split("error")[1][:22] for e in errors] == [
        "[unresolved-attribute]",
        "[unknown-argument] Arg",
    ]


@pytest.mark.anyio
async def test_run_code_api_error_is_catchable(mock_api, code_server):
    mock_api.get("/companies/com_missing").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )
    code = """
import json
import check
try:
    await check.get_company(company_id="com_missing")
    outcome = "found"
except RuntimeError as e:
    outcome = json.loads(str(e))["status_code"]
outcome
"""
    is_error, payload = await _run(code_server, code)
    assert not is_error, payload
    assert payload["result"] == 404
    assert payload["calls"][0]["status"] == "error"
    assert payload["calls"][0]["error"]["status_code"] == 404


THROTTLED = httpx.Response(
    429,
    json={
        "error": {
            "type": "throttled",
            "message": "Request was throttled. Expected available in 0 second.",
        }
    },
)


@pytest.mark.anyio
async def test_run_code_retries_throttled_calls(mock_api, code_server):
    mock_api.get("/companies/com_1").mock(
        side_effect=[THROTTLED, THROTTLED, httpx.Response(200, json={"id": "com_1"})]
    )
    is_error, payload = await _run(
        code_server, '(await check.get_company(company_id="com_1"))["id"]'
    )
    assert not is_error, payload
    assert payload["result"] == "com_1"
    assert payload["calls"] == [
        {
            "tool": "get_company",
            "arguments": {"company_id": "com_1"},
            "status": "ok",
            "duration_ms": payload["calls"][0]["duration_ms"],
            "retries": 2,
        }
    ]
    assert mock_api.calls.call_count == 3


@pytest.mark.anyio
async def test_run_code_gives_up_after_max_retries(mock_api, monkeypatch):
    monkeypatch.setenv("CHECK_API_KEY", "test-key")
    monkeypatch.setenv("CHECK_CODE_MAX_RETRIES", "1")
    mock_api.get("/companies/com_1").mock(return_value=THROTTLED)
    server = CheckMCP("Test Code", lifespan=lifespan)
    setup_tools(server, tool_mode="code")
    is_error, payload = await _run(
        server, 'await check.get_company(company_id="com_1")'
    )
    assert is_error
    assert payload["kind"] == "runtime_error"
    assert payload["calls"][0]["retries"] == 1
    assert payload["calls"][0]["error"]["status_code"] == 429
    assert mock_api.calls.call_count == 2


@pytest.mark.anyio
async def test_run_code_uncaught_error_reports_trace(mock_api, code_server):
    mock_api.get("/companies/com_missing").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )
    is_error, payload = await _run(
        code_server,
        'import check\nprint("before")\nawait check.get_company(company_id="com_missing")',
    )
    assert is_error
    assert payload["kind"] == "runtime_error"
    assert "RuntimeError" in payload["detail"]
    assert payload["logs"] == "before\n"
    assert payload["calls"][0]["tool"] == "get_company"


@pytest.mark.anyio
async def test_run_code_write_must_be_declared(mock_api, code_server):
    mock_api.post("/workplaces").mock(
        return_value=httpx.Response(201, json={"id": "wrk_1", "name": "HQ"})
    )
    code = """
import check
await check.create_workplace(
    company="com_1", name="HQ", address={"line1": "1 Main St", "city": "SF", "state": "CA", "postal_code": "94105"}
)
"""
    is_error, payload = await _run(code_server, code)
    assert is_error
    assert payload["kind"] == "type_check_failed"
    assert "create_workplace" in payload["detail"]
    assert mock_api.calls.call_count == 0

    is_error, payload = await _run(code_server, code, writes=["create_workplace"])
    assert not is_error, payload
    assert payload["result"] == {"id": "wrk_1", "name": "HQ"}
    assert mock_api.calls.call_count == 1


@pytest.mark.anyio
async def test_run_code_read_only_blocks_declared_write(code_server):
    code_server._static_filter = ToolFilter(read_only=True, code_mode=True)
    is_error, payload = await _run(
        code_server, "import check\n1", writes=["create_workplace"]
    )
    assert is_error
    assert "not available" in payload["detail"]


@pytest.mark.anyio
async def test_run_code_rejects_unknown_write(code_server):
    is_error, payload = await _run(code_server, "1", writes=["launch_rocket"])
    assert is_error
    assert "launch_rocket" in payload["detail"]


@pytest.mark.anyio
async def test_run_code_has_no_filesystem_or_network(code_server):
    is_error, payload = await _run(code_server, 'import os\nos.listdir("/")')
    assert is_error
    assert payload["kind"] == "runtime_error"
    assert "PermissionError" in payload["detail"]


@pytest.mark.anyio
async def test_run_code_times_out(monkeypatch):
    monkeypatch.setenv("CHECK_API_KEY", "test-key")
    monkeypatch.setenv("CHECK_CODE_TIMEOUT_SECS", "1")
    server = CheckMCP("Test Code", lifespan=lifespan)
    setup_tools(server, tool_mode="code")
    is_error, payload = await _run(server, "i = 0\nwhile True:\n    i += 1\n")
    assert is_error
    assert payload["kind"] == "timeout"


@pytest.mark.anyio
async def test_run_code_enforces_call_budget(mock_api, monkeypatch):
    monkeypatch.setenv("CHECK_API_KEY", "test-key")
    monkeypatch.setenv("CHECK_CODE_MAX_CALLS", "2")
    mock_api.get("/companies/com_1").mock(
        return_value=httpx.Response(200, json={"id": "com_1"})
    )
    server = CheckMCP("Test Code", lifespan=lifespan)
    setup_tools(server, tool_mode="code")
    code = """
import check
for _ in range(3):
    await check.get_company(company_id="com_1")
"""
    is_error, payload = await _run(server, code)
    assert is_error
    assert payload["kind"] == "runtime_error"
    assert "budget" in payload["detail"]
    assert mock_api.calls.call_count == 2
