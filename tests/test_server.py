"""Tests for the Check MCP server."""

from __future__ import annotations

import httpx
import pytest
from mcp_server_check.helpers import (
    _extract_cursor,
    _format_list_response,
)
from mcp_server_check.server import CheckMCP, _setup_dynamic_mode, lifespan
from mcp_server_check.tool_filter import ToolFilter, is_write_tool
from mcp_server_check.tools import register_all
from mcp_server_check.tools.companies import get_company, list_companies
from mcp_server_check.tools.employees import get_employee, list_employees
from mcp_server_check.tools.payrolls import get_payroll, list_payrolls
from mcp_server_check.tools.workplaces import get_workplace, list_workplaces

BASE_URL = "https://sandbox.checkhq.com"


# --- Helper to create servers with specific configurations ---


def _make_all_tools_server(tool_filter: ToolFilter | None = None) -> CheckMCP:
    """Create a CheckMCP instance in all-tools mode with the given static filter."""
    server = CheckMCP("Test")
    register_all(server, registry=server._registry)
    if tool_filter is not None:
        server._static_filter = tool_filter
    return server


def _make_dynamic_server(tool_filter: ToolFilter | None = None) -> CheckMCP:
    """Create a CheckMCP instance in dynamic mode."""
    server = CheckMCP("Test Dynamic", lifespan=lifespan)
    _setup_dynamic_mode(server)
    if tool_filter is not None:
        server._static_filter = tool_filter
    return server


# --- Unit tests for helpers ---


class TestExtractCursor:
    def test_extracts_cursor_from_url(self):
        url = "https://sandbox.checkhq.com/companies?cursor=abc123&limit=10"
        assert _extract_cursor(url) == "abc123"

    def test_returns_none_for_none(self):
        assert _extract_cursor(None) is None

    def test_returns_none_for_empty_string(self):
        assert _extract_cursor("") is None

    def test_returns_none_when_no_cursor_param(self):
        url = "https://sandbox.checkhq.com/companies?limit=10"
        assert _extract_cursor(url) is None


class TestFormatListResponse:
    def test_formats_paginated_response(self):
        data = {
            "next": "https://sandbox.checkhq.com/companies?cursor=next123",
            "previous": "https://sandbox.checkhq.com/companies?cursor=prev456",
            "results": [{"id": "com_1"}, {"id": "com_2"}],
        }
        result = _format_list_response(data)
        assert result == {
            "results": [{"id": "com_1"}, {"id": "com_2"}],
            "next_cursor": "next123",
            "previous_cursor": "prev456",
        }

    def test_handles_null_pagination(self):
        data = {
            "next": None,
            "previous": None,
            "results": [{"id": "com_1"}],
        }
        result = _format_list_response(data)
        assert result == {
            "results": [{"id": "com_1"}],
            "next_cursor": None,
            "previous_cursor": None,
        }

    def test_handles_missing_keys(self):
        result = _format_list_response({})
        assert result == {
            "results": [],
            "next_cursor": None,
            "previous_cursor": None,
        }


# --- Integration tests calling tool functions directly ---


@pytest.mark.anyio
async def test_list_companies(mock_api, ctx):
    mock_api.get("/companies").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": f"{BASE_URL}/companies?cursor=next_abc",
                "previous": None,
                "results": [
                    {"id": "com_001", "legal_name": "Acme Corp"},
                    {"id": "com_002", "legal_name": "Widget Inc"},
                ],
            },
        )
    )

    result = await list_companies(ctx)
    assert result["results"] == [
        {"id": "com_001", "legal_name": "Acme Corp"},
        {"id": "com_002", "legal_name": "Widget Inc"},
    ]
    assert result["next_cursor"] == "next_abc"
    assert result["previous_cursor"] is None


@pytest.mark.anyio
async def test_list_companies_with_params(mock_api, ctx):
    route = mock_api.get("/companies").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "com_001"}]},
        )
    )

    result = await list_companies(ctx, limit=5, active=True, cursor="abc")
    assert result["results"] == [{"id": "com_001"}]
    # Verify params were passed
    request = route.calls[0].request
    assert "limit=5" in str(request.url)
    assert "active=true" in str(request.url)
    assert "cursor=abc" in str(request.url)


@pytest.mark.anyio
async def test_get_company(mock_api, ctx):
    mock_api.get("/companies/com_001").mock(
        return_value=httpx.Response(
            200,
            json={"id": "com_001", "legal_name": "Acme Corp"},
        )
    )

    result = await get_company(ctx, company_id="com_001")
    assert result == {"id": "com_001", "legal_name": "Acme Corp"}


@pytest.mark.anyio
async def test_list_employees(mock_api, ctx):
    mock_api.get("/employees").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [{"id": "emp_001", "first_name": "Jane"}],
            },
        )
    )

    result = await list_employees(ctx)
    assert result["results"] == [{"id": "emp_001", "first_name": "Jane"}]


@pytest.mark.anyio
async def test_get_employee(mock_api, ctx):
    mock_api.get("/employees/emp_001").mock(
        return_value=httpx.Response(
            200,
            json={"id": "emp_001", "first_name": "Jane"},
        )
    )

    result = await get_employee(ctx, employee_id="emp_001")
    assert result == {"id": "emp_001", "first_name": "Jane"}


@pytest.mark.anyio
async def test_list_workplaces(mock_api, ctx):
    mock_api.get("/workplaces").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [{"id": "wrk_001"}],
            },
        )
    )

    result = await list_workplaces(ctx)
    assert result["results"] == [{"id": "wrk_001"}]


@pytest.mark.anyio
async def test_get_workplace(mock_api, ctx):
    mock_api.get("/workplaces/wrk_001").mock(
        return_value=httpx.Response(
            200,
            json={"id": "wrk_001", "name": "HQ"},
        )
    )

    result = await get_workplace(ctx, workplace_id="wrk_001")
    assert result == {"id": "wrk_001", "name": "HQ"}


@pytest.mark.anyio
async def test_list_payrolls(mock_api, ctx):
    mock_api.get("/payrolls").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [{"id": "prl_001"}],
            },
        )
    )

    result = await list_payrolls(ctx)
    assert result["results"] == [{"id": "prl_001"}]


@pytest.mark.anyio
async def test_get_payroll(mock_api, ctx):
    mock_api.get("/payrolls/prl_001").mock(
        return_value=httpx.Response(
            200,
            json={"id": "prl_001", "period_start": "2026-01-01"},
        )
    )

    result = await get_payroll(ctx, payroll_id="prl_001")
    assert result == {"id": "prl_001", "period_start": "2026-01-01"}


@pytest.mark.anyio
async def test_api_error_returns_error_dict(mock_api, ctx):
    mock_api.get("/companies/com_nonexistent").mock(
        return_value=httpx.Response(
            404,
            json={"error": "Not found"},
        )
    )

    result = await get_company(ctx, company_id="com_nonexistent")
    assert result["error"] is True
    assert result["status_code"] == 404


# --- Tool registration and filtering tests (all-tools mode) ---


@pytest.mark.anyio
async def test_tools_registered():
    """All tools are registered in all-tools mode."""
    server = _make_all_tools_server()
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    expected_core = {
        "list_companies",
        "get_company",
        "list_employees",
        "get_employee",
        "list_workplaces",
        "get_workplace",
        "list_payrolls",
        "get_payroll",
    }
    assert expected_core.issubset(tool_names), (
        f"Missing core tools: {expected_core - tool_names}"
    )
    assert len(tools) > 100, f"Expected 100+ tools, got {len(tools)}"


@pytest.mark.anyio
async def test_registry_populated():
    """The registry maps every tool to its toolset."""
    server = _make_all_tools_server()
    assert len(server._registry) > 100
    assert server._registry["list_companies"] == "companies"
    assert server._registry["list_employees"] == "employees"
    assert server._registry["list_bank_accounts"] == "bank_accounts"


@pytest.mark.anyio
async def test_read_only_mode():
    """Verify read-only mode excludes all write/mutating tools."""
    server = _make_all_tools_server(ToolFilter(read_only=True))
    ro_tools = await server.list_tools()
    ro_names = {t.name for t in ro_tools}

    full_server = _make_all_tools_server(ToolFilter())
    full_tools = await full_server.list_tools()
    full_names = {t.name for t in full_tools}

    # Read-only should be a strict subset of full
    assert ro_names < full_names, (
        "Read-only tools should be a strict subset of full tools"
    )

    # Read-only should have no write tools
    for name in ro_names:
        assert not is_write_tool(name), (
            f"Write tool '{name}' should not be in read-only mode"
        )

    # Core read tools should still be present
    expected_read = {
        "list_companies",
        "get_company",
        "list_employees",
        "get_employee",
        "list_payrolls",
        "get_payroll",
        "preview_payroll",
        "list_workplaces",
        "get_workplace",
        "list_payments",
        "get_payment",
        "list_webhook_configs",
        "get_webhook_config",
        "list_forms",
        "get_form",
        "validate_address",
    }
    assert expected_read.issubset(ro_names), (
        f"Missing read tools in read-only mode: {expected_read - ro_names}"
    )


@pytest.mark.anyio
async def test_toolset_filtering():
    """Only tools from selected toolsets are listed."""
    server = _make_all_tools_server(
        ToolFilter(toolsets=frozenset({"companies", "employees"}))
    )
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}

    assert "list_companies" in tool_names
    assert "get_company" in tool_names
    assert "list_employees" in tool_names
    assert "get_employee" in tool_names

    # Tools from other toolsets should be excluded
    assert "list_payrolls" not in tool_names
    assert "list_bank_accounts" not in tool_names
    assert "list_webhook_configs" not in tool_names


@pytest.mark.anyio
async def test_individual_tool_filtering():
    """Only individually named tools are listed when tools filter is set."""
    server = _make_all_tools_server(
        ToolFilter(tools=frozenset({"list_companies", "get_company"}))
    )
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}

    assert tool_names == {"list_companies", "get_company"}


@pytest.mark.anyio
async def test_exclude_tools():
    """Excluded tools are hidden regardless of other settings."""
    server = _make_all_tools_server(
        ToolFilter(exclude_tools=frozenset({"create_company", "delete_payroll"}))
    )
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}

    assert "create_company" not in tool_names
    assert "delete_payroll" not in tool_names
    assert "list_companies" in tool_names
    assert "get_payroll" in tool_names


@pytest.mark.anyio
async def test_exclude_overrides_tools_allowlist():
    """Exclude takes precedence over the tools allowlist."""
    server = _make_all_tools_server(
        ToolFilter(
            tools=frozenset({"list_companies", "create_company"}),
            exclude_tools=frozenset({"create_company"}),
        )
    )
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}

    assert tool_names == {"list_companies"}


@pytest.mark.anyio
async def test_readonly_with_toolsets():
    """Read-only combined with toolsets filters both."""
    server = _make_all_tools_server(
        ToolFilter(toolsets=frozenset({"companies"}), read_only=True)
    )
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}

    assert "list_companies" in tool_names
    assert "get_company" in tool_names
    assert "create_company" not in tool_names
    assert "update_company" not in tool_names
    # Tools from other toolsets should also be excluded
    assert "list_employees" not in tool_names
