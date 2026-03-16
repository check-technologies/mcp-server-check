"""Tests for company tools."""

from __future__ import annotations

import httpx
import pytest
from mcp_server_check.tools.companies import (
    COMPANY_REPORT_TYPES,
    create_company,
    get_company_paydays,
    get_company_report,
    list_signatories,
    onboard_company,
    start_implementation,
    update_company,
)

BASE_URL = "https://sandbox.checkhq.com"


@pytest.mark.anyio
async def test_create_company(mock_api, ctx):
    mock_api.post("/companies").mock(
        return_value=httpx.Response(201, json={"id": "com_new", "legal_name": "New Co"})
    )
    result = await create_company(ctx, legal_name="New Co")
    assert result["id"] == "com_new"


@pytest.mark.anyio
async def test_update_company(mock_api, ctx):
    mock_api.patch("/companies/com_001").mock(
        return_value=httpx.Response(
            200, json={"id": "com_001", "legal_name": "Updated"}
        )
    )
    result = await update_company(ctx, company_id="com_001", legal_name="Updated")
    assert result["legal_name"] == "Updated"


@pytest.mark.anyio
async def test_onboard_company(mock_api, ctx):
    mock_api.post("/companies/com_001/onboard").mock(
        return_value=httpx.Response(200, json={"id": "com_001", "status": "active"})
    )
    result = await onboard_company(ctx, company_id="com_001")
    assert result["status"] == "active"


@pytest.mark.anyio
async def test_get_company_paydays(mock_api, ctx):
    route = mock_api.get("/companies/com_001/paydays").mock(
        return_value=httpx.Response(200, json={"paydays": ["2026-01-15"]})
    )
    result = await get_company_paydays(
        ctx, company_id="com_001", start_date="2026-01-01", end_date="2026-01-31"
    )
    assert result["paydays"] == ["2026-01-15"]
    assert "start_date=2026-01-01" in str(route.calls[0].request.url)


@pytest.mark.anyio
async def test_get_company_report_with_dates(mock_api, ctx):
    route = mock_api.get("/companies/com_001/reports/payroll_journal").mock(
        return_value=httpx.Response(200, json={"report": "data"})
    )
    result = await get_company_report(
        ctx,
        company_id="com_001",
        report_type="payroll_journal",
        start_date="2026-01-01",
        end_date="2026-01-31",
    )
    assert result["report"] == "data"
    assert "start_date=2026-01-01" in str(route.calls[0].request.url)


@pytest.mark.anyio
async def test_get_company_report_w2_preview(mock_api, ctx):
    mock_api.get("/companies/com_001/reports/w2_preview").mock(
        return_value=httpx.Response(200, json={"report": "w2"})
    )
    result = await get_company_report(
        ctx, company_id="com_001", report_type="w2_preview", year="2025"
    )
    assert result["report"] == "w2"


@pytest.mark.anyio
async def test_get_company_report_no_params(mock_api, ctx):
    mock_api.get("/companies/com_001/reports/w4_exemption_status").mock(
        return_value=httpx.Response(200, json={"report": "w4"})
    )
    result = await get_company_report(
        ctx, company_id="com_001", report_type="w4_exemption_status"
    )
    assert result["report"] == "w4"


@pytest.mark.anyio
async def test_get_company_report_invalid_type(mock_api, ctx):
    result = await get_company_report(
        ctx, company_id="com_001", report_type="nonexistent"
    )
    assert result["error"] is True
    assert "Unknown report_type" in result["detail"]


def test_report_type_count():
    assert len(COMPANY_REPORT_TYPES) == 8


@pytest.mark.anyio
async def test_list_signatories(mock_api, ctx):
    mock_api.get("/companies/com_001/signatories").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "sig_001"}]},
        )
    )
    result = await list_signatories(ctx, company_id="com_001")
    assert result["results"] == [{"id": "sig_001"}]


@pytest.mark.anyio
async def test_start_implementation(mock_api, ctx):
    mock_api.post("/companies/com_001/start_implementation").mock(
        return_value=httpx.Response(200, json={"id": "com_001"})
    )
    result = await start_implementation(ctx, company_id="com_001")
    assert result["id"] == "com_001"
