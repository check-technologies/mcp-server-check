"""Tests for payroll tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.payrolls import (
    approve_payroll,
    create_payroll,
    delete_payroll,
    get_payroll,
    list_payrolls,
    preview_payroll,
    reopen_payroll,
    simulate_start_processing,
    update_payroll,
)

BASE_URL = "https://sandbox.checkhq.com"


@pytest.mark.anyio
async def test_list_payrolls_with_filters(mock_api, ctx):
    mock_api.get("/payrolls").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "prl_001"}]},
        )
    )
    result = await list_payrolls(
        ctx,
        company="com_123",
        type=["regular", "off_cycle"],
        status="paid",
        is_void=False,
        managed=True,
        approved=False,
        pay_schedule="psc_456",
        payday_after="2026-01-01",
        payday_before="2026-12-31",
        include_items=True,
        include_contractor_payments=False,
    )
    assert result["results"] == [{"id": "prl_001"}]
    req = mock_api.get("/payrolls").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params.get_list("type") == ["regular", "off_cycle"]
    assert req.url.params["status"] == "paid"
    assert req.url.params["is_void"] == "false"
    assert req.url.params["managed"] == "true"
    assert req.url.params["approved"] == "false"
    assert req.url.params["pay_schedule"] == "psc_456"
    assert req.url.params["payday_after"] == "2026-01-01"
    assert req.url.params["payday_before"] == "2026-12-31"
    assert req.url.params["include_items"] == "true"
    assert req.url.params["include_contractor_payments"] == "false"


@pytest.mark.anyio
async def test_create_payroll(mock_api, ctx):
    route = mock_api.post("/payrolls").mock(
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
    assert "X-Idempotency-Key" not in route.calls.last.request.headers


@pytest.mark.anyio
async def test_create_payroll_sends_idempotency_key(mock_api, ctx):
    route = mock_api.post("/payrolls").mock(
        return_value=httpx.Response(201, json={"id": "prl_new"})
    )
    await create_payroll(
        ctx,
        company="com_001",
        period_start="2026-01-01",
        period_end="2026-01-15",
        payday="2026-01-17",
        idempotency_key="idem-1",
    )
    assert route.calls.last.request.headers["X-Idempotency-Key"] == "idem-1"


@pytest.mark.anyio
async def test_update_payroll(mock_api, ctx):
    mock_api.patch("/payrolls/prl_001").mock(
        return_value=httpx.Response(200, json={"id": "prl_001", "type": "regular"})
    )
    result = await update_payroll(ctx, payroll_id="prl_001", type="regular")
    assert result["type"] == "regular"


@pytest.mark.anyio
async def test_update_payroll_restate_correction(mock_api, ctx):
    route = mock_api.patch("/payrolls/prl_001").mock(
        return_value=httpx.Response(
            200, json={"id": "prl_001", "correction": "cor_001"}
        )
    )
    result = await update_payroll(ctx, payroll_id="prl_001", correction="cor_001")
    assert result["correction"] == "cor_001"
    assert route.calls.last.request.content == b'{"correction":"cor_001"}'


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
    route = mock_api.post("/payrolls/prl_001/approve").mock(
        return_value=httpx.Response(
            200, json={"id": "prl_001", "approval_status": "approved"}
        )
    )
    result = await approve_payroll(ctx, payroll_id="prl_001")
    assert result["approval_status"] == "approved"
    assert "X-Idempotency-Key" not in route.calls.last.request.headers


@pytest.mark.anyio
async def test_approve_payroll_sends_idempotency_key(mock_api, ctx):
    route = mock_api.post("/payrolls/prl_001/approve").mock(
        return_value=httpx.Response(
            200, json={"id": "prl_001", "approval_status": "approved"}
        )
    )
    await approve_payroll(ctx, payroll_id="prl_001", idempotency_key="idem-1")
    assert route.calls.last.request.headers["X-Idempotency-Key"] == "idem-1"


@pytest.mark.anyio
async def test_approve_payroll_with_preview_started_at(mock_api, ctx):
    route = mock_api.post("/payrolls/prl_001/approve").mock(
        return_value=httpx.Response(
            200, json={"id": "prl_001", "approval_status": "approved"}
        )
    )
    preview_started_at = "2019-06-29T18:26:56.848920Z"
    result = await approve_payroll(
        ctx,
        payroll_id="prl_001",
        preview_started_at=preview_started_at,
    )
    assert result["approval_status"] == "approved"
    assert json.loads(route.calls.last.request.content) == {
        "preview_started_at": preview_started_at,
    }


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


# --- Inlined items are opt-in ---

_INLINED = {
    "id": "prl_001",
    "status": "draft",
    "items": [{"id": "pit_001"}, {"id": "pit_002"}, {"id": "pit_003"}],
    "contractor_payments": [{"id": "cpm_001"}],
}


@pytest.mark.anyio
async def test_get_payroll_omits_inlined_items_by_default(mock_api, ctx):
    route = mock_api.get("/payrolls/prl_001").mock(
        return_value=httpx.Response(200, json=_INLINED)
    )
    result = await get_payroll(ctx, payroll_id="prl_001")
    assert result == {
        "id": "prl_001",
        "status": "draft",
        "items_count": 3,
        "contractor_payments_count": 1,
    }
    assert "include_items" not in route.calls.last.request.url.params


@pytest.mark.anyio
async def test_get_payroll_include_items_asks_the_api_and_keeps_them(mock_api, ctx):
    route = mock_api.get("/payrolls/prl_001").mock(
        return_value=httpx.Response(200, json=_INLINED)
    )
    result = await get_payroll(ctx, payroll_id="prl_001", include_items=True)
    assert result == _INLINED
    params = route.calls.last.request.url.params
    assert params["include_items"] == "true"
    assert params["include_contractor_payments"] == "true"


@pytest.mark.anyio
async def test_get_payroll_without_inlined_items_is_unchanged(mock_api, ctx):
    # API version 2025-01-01 and later omit both lists unless asked.
    mock_api.get("/payrolls/prl_001").mock(
        return_value=httpx.Response(200, json={"id": "prl_001", "status": "paid"})
    )
    result = await get_payroll(ctx, payroll_id="prl_001")
    assert result == {"id": "prl_001", "status": "paid"}


@pytest.mark.anyio
async def test_get_payroll_passes_errors_through(mock_api, ctx):
    mock_api.get("/payrolls/prl_404").mock(
        return_value=httpx.Response(404, json={"error": {"message": "nope"}})
    )
    result = await get_payroll(ctx, payroll_id="prl_404")
    assert result["error"] is True
    assert result["status_code"] == 404


@pytest.mark.anyio
async def test_preview_payroll_omits_item_previews_unless_asked(mock_api, ctx):
    route = mock_api.get("/payrolls/prl_001/preview").mock(
        return_value=httpx.Response(200, json={**_INLINED, "totals": {}})
    )
    result = await preview_payroll(ctx, payroll_id="prl_001")
    assert result["totals"] == {}
    assert result["items_count"] == 3
    assert "items" not in result
    assert "include_items" not in route.calls.last.request.url.params

    result = await preview_payroll(ctx, payroll_id="prl_001", include_items=True)
    assert len(result["items"]) == 3
    assert route.calls.last.request.url.params["include_items"] == "true"


@pytest.mark.anyio
async def test_write_tools_omit_inlined_items_from_their_responses(mock_api, ctx):
    mock_api.post("/payrolls").mock(return_value=httpx.Response(201, json=_INLINED))
    mock_api.patch("/payrolls/prl_001").mock(
        return_value=httpx.Response(200, json=_INLINED)
    )
    mock_api.post("/payrolls/prl_001/approve").mock(
        return_value=httpx.Response(200, json=_INLINED)
    )
    mock_api.post("/payrolls/prl_001/reopen").mock(
        return_value=httpx.Response(200, json=_INLINED)
    )
    mock_api.post("/payrolls/prl_001/simulate/start_processing").mock(
        return_value=httpx.Response(200, json=_INLINED)
    )

    results = [
        await create_payroll(
            ctx,
            company="com_001",
            period_start="2026-01-01",
            period_end="2026-01-15",
            payday="2026-01-17",
            items=[{"employee": "emp_1"}],
        ),
        await update_payroll(ctx, payroll_id="prl_001", payday="2026-01-18"),
        await approve_payroll(ctx, payroll_id="prl_001"),
        await reopen_payroll(ctx, payroll_id="prl_001"),
        await simulate_start_processing(ctx, payroll_id="prl_001"),
    ]
    for result in results:
        assert "items" not in result
        assert result["items_count"] == 3
        assert result["contractor_payments_count"] == 1
