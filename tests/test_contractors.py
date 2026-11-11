"""Tests for contractor tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.contractors import (
    create_contractor,
    get_contractor,
    list_contractor_forms,
    list_contractor_payments_for_contractor,
    list_contractors,
    onboard_contractor,
    update_contractor,
)

BASE_URL = "https://sandbox.checkhq.com"


@pytest.mark.anyio
async def test_list_contractors(mock_api, ctx):
    mock_api.get("/contractors").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ctr_001"}]},
        )
    )
    result = await list_contractors(ctx)
    assert result["results"] == [{"id": "ctr_001"}]


@pytest.mark.anyio
async def test_get_contractor(mock_api, ctx):
    mock_api.get("/contractors/ctr_001").mock(
        return_value=httpx.Response(200, json={"id": "ctr_001"})
    )
    result = await get_contractor(ctx, contractor_id="ctr_001")
    assert result["id"] == "ctr_001"


@pytest.mark.anyio
async def test_create_contractor(mock_api, ctx):
    mock_api.post("/contractors").mock(
        return_value=httpx.Response(201, json={"id": "ctr_new"})
    )
    result = await create_contractor(ctx, company="com_001")
    assert result["id"] == "ctr_new"


@pytest.mark.anyio
async def test_update_contractor_mailing_address(mock_api, ctx):
    mock_api.patch("/contractors/ctr_001").mock(
        return_value=httpx.Response(200, json={"id": "ctr_001"})
    )
    mailing = {
        "line1": "PO Box 456",
        "city": "Albany",
        "state": "NY",
        "postal_code": "12201",
    }
    await update_contractor(ctx, contractor_id="ctr_001", mailing_address=mailing)
    body = json.loads(mock_api.patch("/contractors/ctr_001").calls.last.request.content)
    assert body["mailing_address"] == mailing


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"clear_fields": ["mailing_address"]}, {"mailing_address": None}),
        (
            {"start_date": "2026-11-11", "clear_fields": ["termination_date"]},
            {"start_date": "2026-11-11", "termination_date": None},
        ),
        ({"clear_fields": []}, {}),
        ({"clear_mailing_address": True}, {"mailing_address": None}),
        ({"clear_mailing_address": False}, {}),
        (
            {
                "clear_fields": ["mailing_address"],
                "clear_mailing_address": True,
            },
            {"mailing_address": None},
        ),
    ],
)
async def test_update_contractor_clear_fields(mock_api, ctx, kwargs, expected):
    route = mock_api.patch("/contractors/ctr_001").mock(
        return_value=httpx.Response(200, json={"id": "ctr_001"})
    )
    await update_contractor(ctx, contractor_id="ctr_001", **kwargs)
    assert json.loads(route.calls.last.request.content) == expected


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {
                "mailing_address": {"line1": "PO Box 456"},
                "clear_fields": ["mailing_address"],
            },
            "Pass either a value or clear_fields for mailing_address, not both.",
        ),
        (
            {
                "termination_date": "2026-11-10",
                "clear_fields": ["termination_date"],
            },
            "Pass either a value or clear_fields for termination_date, not both.",
        ),
        (
            {"clear_fields": ["email"]},
            "clear_fields cannot clear email. Clearable fields: "
            "mailing_address, start_date, termination_date.",
        ),
        (
            {
                "mailing_address": {"line1": "PO Box 456"},
                "clear_mailing_address": True,
            },
            "Pass either a value or clear_fields for mailing_address, not both.",
        ),
    ],
)
async def test_update_contractor_rejects_invalid_clear_fields(
    mock_api, ctx, kwargs, message
):
    route = mock_api.patch("/contractors/ctr_001").mock(
        return_value=httpx.Response(200, json={"id": "ctr_001"})
    )
    with pytest.raises(ValueError) as exc_info:
        await update_contractor(ctx, contractor_id="ctr_001", **kwargs)
    assert str(exc_info.value) == message
    assert not route.called


@pytest.mark.anyio
@pytest.mark.parametrize("consent", [True, False, None])
@pytest.mark.parametrize(
    ("tool", "method", "path", "kwargs"),
    [
        (create_contractor, "post", "/contractors", {"company": "com_001"}),
        (
            update_contractor,
            "patch",
            "/contractors/ctr_001",
            {"contractor_id": "ctr_001"},
        ),
    ],
)
async def test_contractor_1099_nec_electronic_consent(
    mock_api, ctx, tool, method, path, kwargs, consent
):
    route = getattr(mock_api, method)(path).mock(
        return_value=httpx.Response(200, json={"id": "ctr_001"})
    )
    if consent is not None:
        kwargs = {**kwargs, "nec_1099_electronic_consent_provided": consent}
    await tool(ctx, **kwargs)
    body = json.loads(route.calls.last.request.content)
    assert "nec_1099_electronic_consent_provided" not in body
    if consent is None:
        assert "1099_nec_electronic_consent_provided" not in body
    else:
        assert body["1099_nec_electronic_consent_provided"] is consent


@pytest.mark.anyio
async def test_onboard_contractor(mock_api, ctx):
    mock_api.post("/contractors/ctr_001/onboard").mock(
        return_value=httpx.Response(200, json={"id": "ctr_001"})
    )
    result = await onboard_contractor(ctx, contractor_id="ctr_001")
    assert result["id"] == "ctr_001"


@pytest.mark.anyio
async def test_list_contractor_payments_for_contractor(mock_api, ctx):
    mock_api.get("/contractors/ctr_001/payments").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "cp_001"}]},
        )
    )
    result = await list_contractor_payments_for_contractor(ctx, contractor_id="ctr_001")
    assert result["results"] == [{"id": "cp_001"}]


@pytest.mark.anyio
async def test_list_contractor_payments_for_contractor_with_filters(mock_api, ctx):
    mock_api.get("/contractors/ctr_001/payments").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "cp_001"}]},
        )
    )
    result = await list_contractor_payments_for_contractor(
        ctx, contractor_id="ctr_001", payroll="pay_123", status="paid"
    )
    assert result["results"] == [{"id": "cp_001"}]
    req = mock_api.get("/contractors/ctr_001/payments").calls.last.request
    assert req.url.params["payroll"] == "pay_123"
    assert req.url.params["status"] == "paid"


@pytest.mark.anyio
async def test_list_contractor_forms(mock_api, ctx):
    mock_api.get("/contractors/ctr_001/forms").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "frm_001"}]},
        )
    )
    result = await list_contractor_forms(ctx, contractor_id="ctr_001")
    assert result["results"] == [{"id": "frm_001"}]
