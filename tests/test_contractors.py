"""Tests for contractor tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.contractors import (
    create_contractor,
    get_contractor,
    list_contractor_forms,
    list_contractor_payments_for_contractor,
    list_contractors,
    onboard_contractor,
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
        ctx, contractor_id="ctr_001", payroll="prl_123", status="paid"
    )
    assert result["results"] == [{"id": "cp_001"}]
    req = mock_api.get("/contractors/ctr_001/payments").calls.last.request
    assert req.url.params["payroll"] == "prl_123"
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
