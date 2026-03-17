"""Tests for contractor payment tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.contractor_payments import (
    create_contractor_payment,
    delete_contractor_payment,
    get_contractor_payment,
    list_contractor_payments,
)


@pytest.mark.anyio
async def test_list_contractor_payments(mock_api, ctx):
    mock_api.get("/contractor_payments").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "cp_001"}]},
        )
    )
    result = await list_contractor_payments(ctx)
    assert result["results"] == [{"id": "cp_001"}]


@pytest.mark.anyio
async def test_get_contractor_payment(mock_api, ctx):
    mock_api.get("/contractor_payments/cp_001").mock(
        return_value=httpx.Response(200, json={"id": "cp_001"})
    )
    result = await get_contractor_payment(ctx, contractor_payment_id="cp_001")
    assert result["id"] == "cp_001"


@pytest.mark.anyio
async def test_create_contractor_payment(mock_api, ctx):
    mock_api.post("/contractor_payments").mock(
        return_value=httpx.Response(201, json={"id": "cp_new"})
    )
    result = await create_contractor_payment(
        ctx, contractor="ctr_001", payroll="prl_001"
    )
    assert result["id"] == "cp_new"


@pytest.mark.anyio
async def test_delete_contractor_payment(mock_api, ctx):
    mock_api.delete("/contractor_payments/cp_001").mock(
        return_value=httpx.Response(204)
    )
    result = await delete_contractor_payment(ctx, contractor_payment_id="cp_001")
    assert result == {"success": True}
