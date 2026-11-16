"""Tests for external payroll tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.external_payrolls import (
    approve_external_payroll,
    create_external_payroll,
    delete_external_payroll,
    get_external_payroll,
    list_external_payrolls,
    preview_external_payroll,
    update_external_payroll,
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
    # The API inlines every payroll's items unless told not to.
    req = mock_api.get("/external_payrolls").calls.last.request
    assert req.url.params["include_items"] == "false"


@pytest.mark.anyio
async def test_list_external_payrolls_with_filters(mock_api, ctx):
    mock_api.get("/external_payrolls").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ep_001"}]},
        )
    )
    result = await list_external_payrolls(
        ctx, company="com_123", pay_schedule="psc_456", include_items=False
    )
    assert result["results"] == [{"id": "ep_001"}]
    req = mock_api.get("/external_payrolls").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["pay_schedule"] == "psc_456"
    assert req.url.params["include_items"] == "false"


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


@pytest.mark.anyio
async def test_list_external_payrolls_include_items_true_is_sent(mock_api, ctx):
    mock_api.get("/external_payrolls").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [{"id": "pay_001", "items": [{"id": "itm_1"}]}],
            },
        )
    )
    result = await list_external_payrolls(ctx, include_items=True)
    req = mock_api.get("/external_payrolls").calls.last.request
    assert req.url.params["include_items"] == "true"
    assert result["results"][0]["items"] == [{"id": "itm_1"}]


_INLINED = {
    "id": "ep_001",
    "payday": "2026-01-17",
    "items": [{"id": "itm_1"}, {"id": "itm_2"}],
    "contractor_payments": [],
}


@pytest.mark.anyio
async def test_get_external_payroll_omits_items_unless_asked(mock_api, ctx):
    route = mock_api.get("/external_payrolls/ep_001").mock(
        return_value=httpx.Response(200, json=_INLINED)
    )
    result = await get_external_payroll(ctx, payroll_id="ep_001")
    assert result == {
        "id": "ep_001",
        "payday": "2026-01-17",
        "items_count": 2,
        "contractor_payments_count": 0,
    }
    # The retrieve endpoint has no opt-out, so nothing extra is sent.
    assert not route.calls.last.request.url.params

    result = await get_external_payroll(ctx, payroll_id="ep_001", include_items=True)
    assert result == _INLINED


@pytest.mark.anyio
async def test_external_payroll_write_tools_omit_inlined_items(mock_api, ctx):
    mock_api.post("/external_payrolls").mock(
        return_value=httpx.Response(201, json=_INLINED)
    )
    mock_api.patch("/external_payrolls/ep_001").mock(
        return_value=httpx.Response(200, json=_INLINED)
    )
    mock_api.post("/external_payrolls/ep_001/approve").mock(
        return_value=httpx.Response(200, json=_INLINED)
    )
    mock_api.get("/external_payrolls/ep_001/preview").mock(
        return_value=httpx.Response(200, json=_INLINED)
    )
    results = [
        await create_external_payroll(
            ctx,
            company="com_001",
            period_start="2026-01-01",
            period_end="2026-01-15",
            payday="2026-01-17",
            items=[{"employee": "emp_1"}],
        ),
        await update_external_payroll(ctx, payroll_id="ep_001", payday="2026-01-18"),
        await approve_external_payroll(ctx, payroll_id="ep_001"),
        await preview_external_payroll(ctx, external_payroll_id="ep_001"),
    ]
    for result in results:
        assert "items" not in result
        assert result["items_count"] == 2
