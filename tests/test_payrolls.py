"""Tests for payroll tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.payrolls import (
    approve_payroll,
    create_payroll,
    delete_payroll,
    preview_payroll,
    reopen_payroll,
    simulate_start_processing,
    update_payroll,
)

BASE_URL = "https://sandbox.checkhq.com"


@pytest.mark.anyio
async def test_create_payroll(mock_api, ctx):
    mock_api.post("/payrolls").mock(
        return_value=httpx.Response(201, json={"id": "prl_new"})
    )
    result = await create_payroll(
        ctx,
        company="com_001",
        period_start="2026-01-01",
        period_end="2026-01-15",
        payday="2026-01-17",
    )
    assert result["id"] == "prl_new"


@pytest.mark.anyio
async def test_update_payroll(mock_api, ctx):
    mock_api.patch("/payrolls/prl_001").mock(
        return_value=httpx.Response(200, json={"id": "prl_001", "type": "regular"})
    )
    result = await update_payroll(ctx, payroll_id="prl_001", type="regular")
    assert result["type"] == "regular"


@pytest.mark.anyio
async def test_delete_payroll(mock_api, ctx):
    mock_api.delete("/payrolls/prl_001").mock(return_value=httpx.Response(204))
    result = await delete_payroll(ctx, payroll_id="prl_001")
    assert result == {"success": True}


@pytest.mark.anyio
async def test_preview_payroll(mock_api, ctx):
    mock_api.get("/payrolls/prl_001/preview").mock(
        return_value=httpx.Response(200, json={"id": "prl_001", "totals": {}})
    )
    result = await preview_payroll(ctx, payroll_id="prl_001")
    assert "totals" in result


@pytest.mark.anyio
async def test_approve_payroll(mock_api, ctx):
    mock_api.post("/payrolls/prl_001/approve").mock(
        return_value=httpx.Response(
            200, json={"id": "prl_001", "approval_status": "approved"}
        )
    )
    result = await approve_payroll(ctx, payroll_id="prl_001")
    assert result["approval_status"] == "approved"


@pytest.mark.anyio
async def test_reopen_payroll(mock_api, ctx):
    mock_api.post("/payrolls/prl_001/reopen").mock(
        return_value=httpx.Response(
            200, json={"id": "prl_001", "approval_status": "draft"}
        )
    )
    result = await reopen_payroll(ctx, payroll_id="prl_001")
    assert result["approval_status"] == "draft"


@pytest.mark.anyio
async def test_simulate_start_processing(mock_api, ctx):
    mock_api.post("/payrolls/prl_001/simulate/start_processing").mock(
        return_value=httpx.Response(200, json={"id": "prl_001"})
    )
    result = await simulate_start_processing(ctx, payroll_id="prl_001")
    assert result["id"] == "prl_001"
