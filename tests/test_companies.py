"""Tests for company tools."""

from __future__ import annotations

import httpx
import pytest
from mcp_server_check.tools.companies import (
    COMPANY_REPORT_TYPES,
    create_company,
    get_company_benefit_aggregations,
    get_company_paydays,
    get_company_report,
    list_companies,
    list_signatories,
    onboard_company,
    start_implementation,
    update_company,
)

BASE_URL = "https://sandbox.checkhq.com"


@pytest.mark.anyio
async def test_list_companies_with_implementation_status(mock_api, ctx):
    route = mock_api.get("/companies").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": "com_001",
                        "legal_name": "Test Co",
                        "trade_name": "Test",
                        "pay_frequency": "biweekly",
                        "onboard": {"status": "blocking"},
                        "implementation": {"status": "needs_attention"},
                    }
                ],
            },
        )
    )
    result = await list_companies(ctx, implementation_status="needs_attention")
    assert result["result_count"] == 1
    assert result["results"][0]["onboard"] == {"status": "blocking"}
    assert result["results"][0]["implementation"] == {"status": "needs_attention"}
    assert "implementation_status=needs_attention" in str(route.calls[0].request.url)


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
        ctx, company_id="com_001", start_date="2026-01-01"
    )
    assert result["paydays"] == ["2026-01-15"]
    params = route.calls[0].request.url.params
    # The paydays endpoint reads `start` and has no end-date parameter.
    assert params["start"] == "2026-01-01"
    assert "start_date" not in params
    assert "end_date" not in params


@pytest.mark.anyio
async def test_get_company_benefit_aggregations_sends_start_end(mock_api, ctx):
    """benefit_aggregations reads `start`/`end`; `start_date` silently defaults to YTD."""
    route = mock_api.get("/companies/com_001/benefit_aggregations").mock(
        return_value=httpx.Response(200, json={"aggregations": []})
    )
    await get_company_benefit_aggregations(
        ctx, company_id="com_001", start_date="2026-01-01", end_date="2026-03-31"
    )
    params = route.calls[0].request.url.params
    assert params["start"] == "2026-01-01"
    assert params["end"] == "2026-03-31"
    assert "start_date" not in params


@pytest.mark.anyio
async def test_get_company_report_sends_start_end_not_start_date(mock_api, ctx):
    """The reports endpoints read `start`/`end`; `start_date` is silently ignored."""
    route = mock_api.get("/companies/com_001/reports/tax_liabilities").mock(
        return_value=httpx.Response(200, json={"report": "data"})
    )
    result = await get_company_report(
        ctx,
        company_id="com_001",
        report_type="tax_liabilities",
        start_date="2026-01-01",
        end_date="2026-01-31",
    )
    assert result["report"] == "data"
    params = route.calls[0].request.url.params
    assert params["start"] == "2026-01-01"
    assert params["end"] == "2026-01-31"
    assert "start_date" not in params
    assert "end_date" not in params


@pytest.mark.anyio
@pytest.mark.parametrize("report_type", ["payroll_journal", "payroll_summary"])
async def test_get_company_report_returns_directly_when_fast_enough(
    mock_api, ctx, report_type
):
    """Most journal/summary requests finish in seconds and must not be deferred."""
    route = mock_api.get(f"/companies/com_001/reports/{report_type}").mock(
        return_value=httpx.Response(200, json={"report": "data"})
    )
    result = await get_company_report(
        ctx,
        company_id="com_001",
        report_type=report_type,
        start_date="2026-01-01",
        end_date="2026-12-31",
    )
    assert result["report"] == "data"
    params = route.calls[0].request.url.params
    assert params["start"] == "2026-01-01"
    assert params["end"] == "2026-12-31"


@pytest.mark.anyio
@pytest.mark.parametrize("report_type", ["payroll_journal", "payroll_summary"])
async def test_get_company_report_points_at_report_runs_on_timeout(
    mock_api, ctx, report_type
):
    """Only a request that actually proves too slow is sent to the async path."""
    mock_api.get(f"/companies/com_001/reports/{report_type}").mock(
        side_effect=httpx.ReadTimeout("timed out")
    )
    result = await get_company_report(
        ctx,
        company_id="com_001",
        report_type=report_type,
        start_date="2020-01-01",
        end_date="2026-12-31",
    )
    assert result["error"] is True
    assert "create_report_run" in result["detail"]
    assert "payday_from" in result["detail"]


@pytest.mark.anyio
async def test_get_company_report_timeout_not_rewritten_for_other_reports(
    mock_api, ctx
):
    """tax_liabilities has no report-run equivalent; leave its error alone."""
    mock_api.get("/companies/com_001/reports/tax_liabilities").mock(
        side_effect=httpx.ReadTimeout("timed out")
    )
    result = await get_company_report(
        ctx,
        company_id="com_001",
        report_type="tax_liabilities",
        start_date="2026-01-01",
        end_date="2026-01-31",
    )
    assert result["error"] is True
    assert result.get("timeout") is True
    assert "create_report_run" not in result.get("detail", "")


@pytest.mark.anyio
async def test_get_company_report_passes_payroll_ids(mock_api, ctx):
    """Explicit payroll IDs are the fast path and must reach the wire."""
    route = mock_api.get("/companies/com_001/reports/payroll_journal").mock(
        return_value=httpx.Response(200, json={"report": "data"})
    )
    await get_company_report(
        ctx,
        company_id="com_001",
        report_type="payroll_journal",
        payroll=["pay_001", "pay_002"],
        include_contractor_id=True,
    )
    url = str(route.calls[0].request.url)
    assert "payroll=pay_001" in url
    assert "payroll=pay_002" in url
    assert route.calls[0].request.url.params["include_contractor_id"] == "true"


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
async def test_get_company_report_omits_dates_for_non_range_reports(mock_api, ctx):
    """w2_preview takes `year`; a stray start_date must not reach the wire."""
    route = mock_api.get("/companies/com_001/reports/w2_preview").mock(
        return_value=httpx.Response(200, json={"report": "w2"})
    )
    await get_company_report(
        ctx,
        company_id="com_001",
        report_type="w2_preview",
        year="2025",
        start_date="2026-01-01",
    )
    params = route.calls[0].request.url.params
    assert params["year"] == "2025"
    assert "start" not in params
    assert "start_date" not in params


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
