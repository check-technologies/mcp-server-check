"""Tests for correction tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.corrections import (
    add_payroll_to_correction,
    approve_correction,
    create_correction,
    delete_correction,
    get_correction,
    list_corrections,
    preview_correction,
    reopen_correction,
    update_correction,
    void_payroll,
)


@pytest.mark.anyio
async def test_list_corrections_with_filters(mock_api, ctx):
    route = mock_api.get("/corrections").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "cor_001"}]},
        )
    )
    result = await list_corrections(
        ctx,
        company="com_123",
        year=2026,
        status="draft",
        payroll="pay_456",
        limit=5,
        cursor="abc",
    )
    assert result["results"] == [{"id": "cor_001"}]
    params = route.calls.last.request.url.params
    assert params["company"] == "com_123"
    assert params["year"] == "2026"
    assert params["status"] == "draft"
    assert params["payroll"] == "pay_456"
    assert params["limit"] == "5"
    assert params["cursor"] == "abc"


@pytest.mark.anyio
async def test_get_correction(mock_api, ctx):
    mock_api.get("/corrections/cor_001").mock(
        return_value=httpx.Response(200, json={"id": "cor_001", "status": "draft"})
    )
    result = await get_correction(ctx, correction_id="cor_001")
    assert result == {"id": "cor_001", "status": "draft"}


@pytest.mark.anyio
async def test_create_correction_sends_only_provided_fields(mock_api, ctx):
    route = mock_api.post("/corrections").mock(
        return_value=httpx.Response(201, json={"id": "cor_new"})
    )
    result = await create_correction(
        ctx, company="com_001", year=2026, description="Wrong workplace"
    )
    assert result["id"] == "cor_new"
    assert json.loads(route.calls.last.request.content) == {
        "company": "com_001",
        "year": 2026,
        "description": "Wrong workplace",
    }


@pytest.mark.anyio
async def test_update_correction(mock_api, ctx):
    route = mock_api.patch("/corrections/cor_001").mock(
        return_value=httpx.Response(200, json={"id": "cor_001"})
    )
    await update_correction(
        ctx,
        correction_id="cor_001",
        settlement_date="2026-10-05",
        bank_account="bnk_001",
    )
    assert json.loads(route.calls.last.request.content) == {
        "settlement_date": "2026-10-05",
        "bank_account": "bnk_001",
    }


@pytest.mark.anyio
async def test_delete_correction(mock_api, ctx):
    mock_api.delete("/corrections/cor_001").mock(return_value=httpx.Response(204))
    result = await delete_correction(ctx, correction_id="cor_001")
    assert result == {"success": True}


@pytest.mark.anyio
async def test_void_payroll_entire_payroll_sends_null_subset(mock_api, ctx):
    route = mock_api.post("/payrolls/pay_001/void").mock(
        return_value=httpx.Response(201, json={"id": "pay_void"})
    )
    result = await void_payroll(
        ctx, payroll_id="pay_001", correction="cor_001", subset=None
    )
    assert result["id"] == "pay_void"
    assert json.loads(route.calls.last.request.content) == {
        "correction": "cor_001",
        "subset": None,
    }


@pytest.mark.anyio
async def test_void_payroll_subset(mock_api, ctx):
    route = mock_api.post("/payrolls/pay_001/void").mock(
        return_value=httpx.Response(201, json={"id": "pay_void"})
    )
    await void_payroll(
        ctx,
        payroll_id="pay_001",
        correction="cor_001",
        subset={"payroll_items": ["itm_001"]},
    )
    assert json.loads(route.calls.last.request.content) == {
        "correction": "cor_001",
        "subset": {"payroll_items": ["itm_001"]},
    }


@pytest.mark.anyio
async def test_add_payroll_to_correction(mock_api, ctx):
    route = mock_api.post("/payrolls").mock(
        return_value=httpx.Response(201, json={"id": "pay_new"})
    )
    items = [{"employee": "emp_001", "payment_method": "manual"}]
    result = await add_payroll_to_correction(
        ctx,
        correction="cor_001",
        company="com_001",
        period_start="2026-07-01",
        period_end="2026-07-15",
        payday="2026-07-17",
        items=items,
        idempotency_key="idem-1",
    )
    assert result["id"] == "pay_new"
    request = route.calls.last.request
    assert json.loads(request.content) == {
        "correction": "cor_001",
        "company": "com_001",
        "period_start": "2026-07-01",
        "period_end": "2026-07-15",
        "payday": "2026-07-17",
        "items": items,
    }
    assert request.headers["X-Idempotency-Key"] == "idem-1"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("tool", "action"),
    [
        (preview_correction, "preview"),
        (approve_correction, "approve"),
        (reopen_correction, "reopen"),
    ],
)
async def test_correction_actions(mock_api, ctx, tool, action):
    route = mock_api.post(f"/corrections/cor_001/{action}").mock(
        return_value=httpx.Response(202, json={"id": "cor_001"})
    )
    result = await tool(ctx, correction_id="cor_001")
    assert result["id"] == "cor_001"
    assert route.called
