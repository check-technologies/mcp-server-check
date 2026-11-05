"""Tests for payroll item tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.payroll_items import (
    create_payroll_item,
    delete_payroll_item,
    get_payroll_item,
    gross_up_payroll_item,
    list_payroll_items,
    update_payroll_item,
)


@pytest.mark.anyio
async def test_list_payroll_items(mock_api, ctx):
    mock_api.get("/payroll_items").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "itm_001"}]},
        )
    )
    result = await list_payroll_items(ctx)
    assert result["results"] == [{"id": "itm_001"}]


@pytest.mark.anyio
async def test_get_payroll_item(mock_api, ctx):
    mock_api.get("/payroll_items/itm_001").mock(
        return_value=httpx.Response(200, json={"id": "itm_001"})
    )
    result = await get_payroll_item(ctx, payroll_item_id="itm_001")
    assert result["id"] == "itm_001"


@pytest.mark.anyio
async def test_create_payroll_item(mock_api, ctx):
    mock_api.post("/payroll_items").mock(
        return_value=httpx.Response(201, json={"id": "itm_new"})
    )
    result = await create_payroll_item(ctx, payroll="pay_001", employee="emp_001")
    assert result["id"] == "itm_new"


@pytest.mark.anyio
async def test_update_payroll_item(mock_api, ctx):
    mock_api.patch("/payroll_items/itm_001").mock(
        return_value=httpx.Response(200, json={"id": "itm_001"})
    )
    result = await update_payroll_item(
        ctx, payroll_item_id="itm_001", payment_method="direct_deposit"
    )
    assert result["id"] == "itm_001"


@pytest.mark.anyio
async def test_delete_payroll_item(mock_api, ctx):
    mock_api.delete("/payroll_items/itm_001").mock(return_value=httpx.Response(204))
    result = await delete_payroll_item(ctx, payroll_item_id="itm_001")
    assert result == {"success": True}


@pytest.mark.anyio
async def test_gross_up_payroll_item(mock_api, ctx):
    mock_api.post("/payroll_items/itm_001/gross_up").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "itm_001",
                "earnings": [{"type": "bonus", "amount": "1200.00"}],
            },
        )
    )
    result = await gross_up_payroll_item(
        ctx,
        payroll_item_id="itm_001",
        earnings=[
            {
                "type": "bonus",
                "workplace": "wrk_001",
                "net_amount": "1000.00",
            }
        ],
    )
    assert result["id"] == "itm_001"
    assert result["earnings"][0]["amount"] == "1200.00"
