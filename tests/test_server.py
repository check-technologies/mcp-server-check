"""Tests for the Check MCP server."""

from __future__ import annotations

import httpx
import pytest
from mcp_server_check.helpers import (
    _extract_cursor,
    _format_list_response,
)
from mcp_server_check.server import mcp
from mcp_server_check.tools.companies import get_company, list_companies
from mcp_server_check.tools.employees import get_employee, list_employees
from mcp_server_check.tools.payrolls import get_payroll, list_payrolls
from mcp_server_check.tools.workplaces import get_workplace, list_workplaces

BASE_URL = "https://sandbox.checkhq.com"


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


@pytest.mark.anyio
async def test_tools_registered():
    """Verify expected tools are registered on the MCP server."""
    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools}
    # Check that core tools from the original server are present
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
    # Verify we have a large number of tools registered
    assert len(tools) > 150, f"Expected 150+ tools, got {len(tools)}"


@pytest.mark.anyio
async def test_read_only_mode():
    """Verify read-only mode excludes all write/mutating tools."""
    from mcp.server.fastmcp import FastMCP
    from mcp_server_check.tools import register_all

    read_only_mcp = FastMCP("Test Read-Only")
    register_all(read_only_mcp, read_only=True)
    ro_tools = await read_only_mcp.list_tools()
    ro_names = {t.name for t in ro_tools}

    full_mcp = FastMCP("Test Full")
    register_all(full_mcp, read_only=False)
    full_tools = await full_mcp.list_tools()
    full_names = {t.name for t in full_tools}

    # Read-only should be a strict subset of full
    assert ro_names < full_names, "Read-only tools should be a strict subset of full tools"

    # Read-only should have no create/update/delete/mutating tools
    write_prefixes = ("create_", "update_", "delete_", "bulk_update_", "bulk_delete_")
    write_keywords = (
        "approve_", "reopen_", "onboard_", "submit_", "sign_and_submit_",
        "authorize_", "simulate_", "retry_", "refund_", "cancel_",
        "start_implementation", "cancel_implementation", "request_embedded_setup",
        "ping_", "refresh_", "toggle_", "sync_", "upload_", "request_tax_",
    )
    for name in ro_names:
        assert not any(name.startswith(p) for p in write_prefixes), (
            f"Write tool '{name}' should not be in read-only mode"
        )
        assert not any(name.startswith(k) for k in write_keywords), (
            f"Mutating tool '{name}' should not be in read-only mode"
        )

    # Core read tools should still be present
    expected_read = {
        "list_companies", "get_company",
        "list_employees", "get_employee",
        "list_payrolls", "get_payroll", "preview_payroll",
        "list_workplaces", "get_workplace",
        "list_payments", "get_payment",
        "list_webhook_configs", "get_webhook_config",
        "list_forms", "get_form",
        "validate_address",
    }
    assert expected_read.issubset(ro_names), (
        f"Missing read tools in read-only mode: {expected_read - ro_names}"
    )
