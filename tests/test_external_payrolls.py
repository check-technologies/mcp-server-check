"""Tests for external payroll tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.external_payrolls import (
    approve_external_payroll,
    create_external_payroll,
    delete_external_payroll,
    list_external_payrolls,
)


@pytest.mark.anyio
async def test_list_external_payrolls(mock_api, ctx):
    mock_api.get("/external_payrolls").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ep_001"}]},
        )
    )
    result = await list_external_payrolls(ctx)
    assert result["results"] == [{"id": "ep_001"}]


@pytest.mark.anyio
async def test_create_external_payroll(mock_api, ctx):
    mock_api.post("/external_payrolls").mock(
        return_value=httpx.Response(201, json={"id": "ep_new"})
    )
    result = await create_external_payroll(
        ctx,
        company="com_001",
        period_start="2026-01-01",
        period_end="2026-01-15",
        payday="2026-01-17",
    )
    assert result["id"] == "ep_new"


@pytest.mark.anyio
async def test_delete_external_payroll(mock_api, ctx):
    mock_api.delete("/external_payrolls/ep_001").mock(return_value=httpx.Response(204))
    result = await delete_external_payroll(ctx, payroll_id="ep_001")
    assert result == {"success": True}


@pytest.mark.anyio
async def test_approve_external_payroll(mock_api, ctx):
    mock_api.post("/external_payrolls/ep_001/approve").mock(
        return_value=httpx.Response(200, json={"id": "ep_001"})
    )
    result = await approve_external_payroll(ctx, payroll_id="ep_001")
    assert result["id"] == "ep_001"
