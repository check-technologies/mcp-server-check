"""Tests for payment tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.payments import (
    cancel_payment,
    get_payment,
    list_payment_attempts,
    list_payments,
    retry_payment,
)


@pytest.mark.anyio
async def test_list_payments(mock_api, ctx):
    mock_api.get("/payments").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "pmt_001"}]},
        )
    )
    result = await list_payments(ctx)
    assert result["results"] == [{"id": "pmt_001"}]


@pytest.mark.anyio
async def test_list_payments_with_filters(mock_api, ctx):
    mock_api.get("/payments").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "pmt_002"}]},
        )
    )
    result = await list_payments(
        ctx,
        company="com_123",
        payroll="prl_456",
        type="company_cash_requirement",
        direction="debit",
        amount_min="100.00",
        completion_date_after="2025-01-01",
    )
    assert result["results"] == [{"id": "pmt_002"}]
    req = mock_api.get("/payments").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["payroll"] == "prl_456"
    assert req.url.params["type"] == "company_cash_requirement"
    assert req.url.params["direction"] == "debit"
    assert req.url.params["amount_min"] == "100.00"
    assert req.url.params["completion_date_after"] == "2025-01-01"
    assert "amount_max" not in req.url.params
    assert "completion_date_before" not in req.url.params


@pytest.mark.anyio
async def test_get_payment(mock_api, ctx):
    mock_api.get("/payments/pmt_001").mock(
        return_value=httpx.Response(200, json={"id": "pmt_001"})
    )
    result = await get_payment(ctx, payment_id="pmt_001")
    assert result["id"] == "pmt_001"


@pytest.mark.anyio
async def test_list_payment_attempts(mock_api, ctx):
    mock_api.get("/payments/pmt_001/payment_attempts").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "pa_001"}]},
        )
    )
    result = await list_payment_attempts(ctx, payment_id="pmt_001")
    assert result["results"] == [{"id": "pa_001"}]


@pytest.mark.anyio
async def test_retry_payment(mock_api, ctx):
    mock_api.post("/payments/pmt_001/retry").mock(
        return_value=httpx.Response(200, json={"id": "pmt_001"})
    )
    result = await retry_payment(ctx, payment_id="pmt_001")
    assert result["id"] == "pmt_001"


@pytest.mark.anyio
async def test_cancel_payment(mock_api, ctx):
    mock_api.post("/payments/pmt_001/cancel").mock(
        return_value=httpx.Response(200, json={"id": "pmt_001", "status": "canceled"})
    )
    result = await cancel_payment(ctx, payment_id="pmt_001")
    assert result["status"] == "canceled"
