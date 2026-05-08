"""Tests for tax tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.tax import (
    get_company_tax_params,
    get_filing,
    list_company_tax_elections,
    list_company_tax_param_settings,
    list_employee_tax_param_settings,
    list_employee_tax_params,
    list_employee_tax_statements,
    list_filings,
    update_company_tax_params,
)


@pytest.mark.anyio
async def test_get_company_tax_params(mock_api, ctx):
    mock_api.get("/company_tax_params/com_001").mock(
        return_value=httpx.Response(200, json={"id": "com_001", "ein": "12-3456789"})
    )
    result = await get_company_tax_params(ctx, company_id="com_001")
    assert result["ein"] == "12-3456789"


@pytest.mark.anyio
async def test_update_company_tax_params(mock_api, ctx):
    mock_api.patch("/company_tax_params/com_001").mock(
        return_value=httpx.Response(200, json={"results": [{"id": "spa_001"}]})
    )
    result = await update_company_tax_params(
        ctx, company_id="com_001", data=[{"id": "spa_001", "value": "12-3456789"}]
    )
    assert result["results"] == [{"id": "spa_001"}]


@pytest.mark.anyio
async def test_list_employee_tax_params(mock_api, ctx):
    mock_api.get("/employee_tax_params").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "etp_001"}]},
        )
    )
    result = await list_employee_tax_params(ctx)
    assert result["results"] == [{"id": "etp_001"}]


@pytest.mark.anyio
async def test_list_company_tax_elections(mock_api, ctx):
    mock_api.get("/companies/com_001/tax_elections").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "te_001"}]},
        )
    )
    result = await list_company_tax_elections(ctx, company_id="com_001")
    assert result["results"] == [{"id": "te_001"}]


@pytest.mark.anyio
async def test_list_filings(mock_api, ctx):
    mock_api.get("/filings").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [{"id": "com_fil_001"}],
            },
        )
    )
    result = await list_filings(ctx)
    assert result["results"] == [{"id": "com_fil_001"}]


@pytest.mark.anyio
async def test_list_employee_tax_params_with_filters(mock_api, ctx):
    mock_api.get("/employee_tax_params").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "etp_001"}]},
        )
    )
    result = await list_employee_tax_params(
        ctx, employee="emp_123", company="com_456", jurisdiction="CA"
    )
    assert result["results"] == [{"id": "etp_001"}]
    req = mock_api.get("/employee_tax_params").calls.last.request
    assert req.url.params["employee"] == "emp_123"
    assert req.url.params["company"] == "com_456"
    assert req.url.params["jurisdiction"] == "CA"
    assert "as_of" not in req.url.params


@pytest.mark.anyio
async def test_list_company_tax_param_settings_with_filters(mock_api, ctx):
    mock_api.get("/company_tax_params/com_001/settings").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "sps_001"}]},
        )
    )
    result = await list_company_tax_param_settings(
        ctx, company_id="com_001", as_of="2026-01-01", jurisdiction="CA"
    )
    assert result["results"] == [{"id": "sps_001"}]
    req = mock_api.get("/company_tax_params/com_001/settings").calls.last.request
    assert req.url.params["as_of"] == "2026-01-01"
    assert req.url.params["jurisdiction"] == "CA"


@pytest.mark.anyio
async def test_list_employee_tax_param_settings_with_filters(mock_api, ctx):
    mock_api.get("/employee_tax_params/emp_001/settings").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "sps_001"}]},
        )
    )
    result = await list_employee_tax_param_settings(
        ctx, employee_id="emp_001", jurisdiction="NY", submitter="employer"
    )
    assert result["results"] == [{"id": "sps_001"}]
    req = mock_api.get("/employee_tax_params/emp_001/settings").calls.last.request
    assert req.url.params["jurisdiction"] == "NY"
    assert req.url.params["submitter"] == "employer"


@pytest.mark.anyio
async def test_list_filings_with_filters(mock_api, ctx):
    mock_api.get("/filings").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [{"id": "com_fil_001"}],
            },
        )
    )
    result = await list_filings(
        ctx, company="com_123", year=2025, period="q1", status="blocked"
    )
    assert result["results"] == [{"id": "com_fil_001"}]
    req = mock_api.get("/filings").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["year"] == "2025"
    assert req.url.params["period"] == "q1"
    assert req.url.params["status"] == "blocked"


@pytest.mark.anyio
async def test_list_employee_tax_statements_with_filters(mock_api, ctx):
    mock_api.get("/employee_tax_statements").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ets_001"}]},
        )
    )
    result = await list_employee_tax_statements(
        ctx, employee="emp_123", company="com_456", year=2025
    )
    assert result["results"] == [{"id": "ets_001"}]
    req = mock_api.get("/employee_tax_statements").calls.last.request
    assert req.url.params["employee"] == "emp_123"
    assert req.url.params["company"] == "com_456"
    assert req.url.params["year"] == "2025"


@pytest.mark.anyio
async def test_get_filing(mock_api, ctx):
    mock_api.get("/filings/com_fil_001").mock(
        return_value=httpx.Response(200, json={"id": "com_fil_001"})
    )
    result = await get_filing(ctx, filing_id="com_fil_001")
    assert result["id"] == "com_fil_001"
