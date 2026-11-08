"""Tests for payment tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.payments import (
    cancel_payment,
    get_payment,
    list_payment_attempts,
    list_payments,
    retry_payment,
    reverse_payment,
    simulate_complete_payment,
    simulate_fail_payment,
)


@pytest.mark.anyio
async def test_list_payments(mock_api, ctx):
    mock_api.get("/payments").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "pyt_001"}]},
        )
    )
    result = await list_payments(ctx)
    assert result["results"] == [{"id": "pyt_001"}]


@pytest.mark.anyio
async def test_list_payments_with_filters(mock_api, ctx):
    mock_api.get("/payments").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "pyt_002"}]},
        )
    )
    result = await list_payments(
        ctx,
        company="com_123",
        payroll="pay_456",
        type="company_cash_requirement",
        direction="debit",
        amount_min="100.00",
        completion_date_after="2025-01-01",
    )
    assert result["results"] == [{"id": "pyt_002"}]
    req = mock_api.get("/payments").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["payroll"] == "pay_456"
    assert req.url.params["type"] == "company_cash_requirement"
    assert req.url.params["direction"] == "debit"
    assert req.url.params["amount_min"] == "100.00"
    assert req.url.params["completion_date_after"] == "2025-01-01"
    assert "amount_max" not in req.url.params
    assert "completion_date_before" not in req.url.params


@pytest.mark.anyio
async def test_list_payments_parent_id_filter(mock_api, ctx):
    mock_api.get("/payments").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "pyt_003"}]},
        )
    )
    result = await list_payments(
        ctx,
        parent_id=["pay_abc", "cor_def"],
    )
    assert result["results"] == [{"id": "pyt_003"}]
    req = mock_api.get("/payments").calls.last.request
    assert req.url.params.get_list("parent_id") == ["pay_abc", "cor_def"]


@pytest.mark.anyio
async def test_get_payment(mock_api, ctx):
    mock_api.get("/payments/pyt_001").mock(
        return_value=httpx.Response(200, json={"id": "pyt_001"})
    )
    result = await get_payment(ctx, payment_id="pyt_001")
    assert result["id"] == "pyt_001"


@pytest.mark.anyio
async def test_list_payment_attempts(mock_api, ctx):
    mock_api.get("/payment_attempts").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "pa_001"}]},
        )
    )
    result = await list_payment_attempts(ctx, payment_id="pyt_001")
    assert result["results"] == [{"id": "pa_001"}]
    req = mock_api.get("/payment_attempts").calls.last.request
    assert req.url.params["payment"] == "pyt_001"


@pytest.mark.anyio
async def test_retry_payment(mock_api, ctx):
    mock_api.post("/payments/pyt_001/retry").mock(
        return_value=httpx.Response(200, json={"id": "pyt_001"})
    )
    result = await retry_payment(ctx, payment_id="pyt_001")
    assert result["id"] == "pyt_001"
    assert mock_api.post("/payments/pyt_001/retry").calls.last.request.content == b""


@pytest.mark.anyio
async def test_retry_payment_to_new_bank_account(mock_api, ctx):
    route = mock_api.post("/payments/pyt_001/retry").mock(
        return_value=httpx.Response(200, json={"id": "pyt_001", "status": "pending"})
    )
    result = await retry_payment(ctx, payment_id="pyt_001", bank_account="bnk_new")
    assert result["status"] == "pending"
    assert json.loads(route.calls.last.request.content) == {"bank_account": "bnk_new"}


@pytest.mark.anyio
async def test_retry_payment_by_wire(mock_api, ctx):
    route = mock_api.post("/payments/pyt_001/retry").mock(
        return_value=httpx.Response(200, json={"id": "pyt_001"})
    )
    await retry_payment(ctx, payment_id="pyt_001", payment_type="wire")
    assert json.loads(route.calls.last.request.content) == {"payment_type": "wire"}


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("tool", "action"),
    [(simulate_complete_payment, "complete"), (simulate_fail_payment, "fail")],
)
async def test_simulate_payment_outcome(mock_api, ctx, tool, action):
    """The payment simulate actions answer 200 with an empty body."""
    route = mock_api.post(f"/payments/pyt_001/simulate/{action}").mock(
        return_value=httpx.Response(200, content=b"")
    )
    result = await tool(ctx, payment_id="pyt_001")
    assert route.called
    assert result == {"success": True}


@pytest.mark.anyio
async def test_simulate_fail_payment_passes_errors_through(mock_api, ctx):
    mock_api.post("/payments/pyt_001/simulate/fail").mock(
        return_value=httpx.Response(
            400, json=["Payment must be pending to simulate outcome"]
        )
    )
    result = await simulate_fail_payment(ctx, payment_id="pyt_001")
    assert result["error"] is True
    assert result["status_code"] == 400


@pytest.mark.anyio
async def test_cancel_payment(mock_api, ctx):
    mock_api.post("/payments/pyt_001/cancel").mock(
        return_value=httpx.Response(200, json={"id": "pyt_001", "status": "canceled"})
    )
    result = await cancel_payment(ctx, payment_id="pyt_001")
    assert result["status"] == "canceled"


@pytest.mark.anyio
async def test_reverse_payment(mock_api, ctx):
    mock_api.post("/payments/pyt_001/reverse").mock(
        return_value=httpx.Response(200, json={"id": "pyt_001", "status": "reversed"})
    )
    result = await reverse_payment(
        ctx,
        payment_id="pyt_001",
        reason="duplicate",
        idempotency_key="idem-1",
    )
    assert result["status"] == "reversed"
    request = mock_api.post("/payments/pyt_001/reverse").calls.last.request
    assert request.headers["X-Idempotency-Key"] == "idem-1"
    assert json.loads(request.content) == {"reason": "duplicate"}


@pytest.mark.anyio
async def test_reverse_payment_defaults_idempotency_key(mock_api, ctx):
    route = mock_api.post("/payments/pyt_001/reverse").mock(
        return_value=httpx.Response(200, json={"id": "pyt_001", "status": "reversed"})
    )
    await reverse_payment(ctx, payment_id="pyt_001", reason="duplicate")
    assert route.calls.last.request.headers["X-Idempotency-Key"]
