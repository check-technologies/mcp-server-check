"""Tests for compensation tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.compensation import (
    create_benefit,
    create_pay_schedule,
    delete_pay_schedule,
    list_benefits,
    list_company_benefits,
    list_earning_codes,
    list_earning_rates,
    list_net_pay_splits,
    list_pay_schedules,
    list_post_tax_deductions,
)


@pytest.mark.anyio
async def test_list_pay_schedules(mock_api, ctx):
    mock_api.get("/pay_schedules").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "psc_001"}]},
        )
    )
    result = await list_pay_schedules(ctx)
    assert result["results"] == [{"id": "psc_001"}]


@pytest.mark.anyio
async def test_create_pay_schedule(mock_api, ctx):
    mock_api.post("/pay_schedules").mock(
        return_value=httpx.Response(201, json={"id": "psc_new"})
    )
    result = await create_pay_schedule(
        ctx,
        company="com_001",
        pay_frequency="biweekly",
        first_payday="2026-01-15",
        first_period_end="2026-01-14",
    )
    assert result["id"] == "psc_new"


@pytest.mark.anyio
async def test_delete_pay_schedule(mock_api, ctx):
    mock_api.delete("/pay_schedules/psc_001").mock(return_value=httpx.Response(204))
    result = await delete_pay_schedule(ctx, pay_schedule_id="psc_001")
    assert result == {"success": True}


@pytest.mark.anyio
async def test_create_benefit(mock_api, ctx):
    mock_api.post("/benefits").mock(
        return_value=httpx.Response(201, json={"id": "ben_new"})
    )
    result = await create_benefit(ctx, employee="emp_001", company_benefit="cb_001")
    assert result["id"] == "ben_new"


@pytest.mark.anyio
async def test_list_company_benefits(mock_api, ctx):
    mock_api.get("/company_benefits").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "cb_001"}]},
        )
    )
    result = await list_company_benefits(ctx)
    assert result["results"] == [{"id": "cb_001"}]


@pytest.mark.anyio
async def test_list_benefits_with_filters(mock_api, ctx):
    mock_api.get("/benefits").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ben_001"}]},
        )
    )
    result = await list_benefits(
        ctx, company="com_123", employee="emp_456", include_external=True
    )
    assert result["results"] == [{"id": "ben_001"}]
    req = mock_api.get("/benefits").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["employee"] == "emp_456"
    assert req.url.params["include_external"] == "true"


@pytest.mark.anyio
async def test_list_post_tax_deductions_with_filters(mock_api, ctx):
    mock_api.get("/post_tax_deductions").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ptd_001"}]},
        )
    )
    result = await list_post_tax_deductions(
        ctx, company="com_123", include_external=True
    )
    assert result["results"] == [{"id": "ptd_001"}]
    req = mock_api.get("/post_tax_deductions").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["include_external"] == "true"


@pytest.mark.anyio
async def test_list_earning_rates_with_filters(mock_api, ctx):
    mock_api.get("/earning_rates").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "er_001"}]},
        )
    )
    result = await list_earning_rates(
        ctx, company="com_123", employee="emp_456", active=True
    )
    assert result["results"] == [{"id": "er_001"}]
    req = mock_api.get("/earning_rates").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["employee"] == "emp_456"
    assert req.url.params["active"] == "true"


@pytest.mark.anyio
async def test_list_net_pay_splits_with_filters(mock_api, ctx):
    mock_api.get("/net_pay_splits").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "nps_001"}]},
        )
    )
    result = await list_net_pay_splits(ctx, company="com_123", contractor="ctr_456")
    assert result["results"] == [{"id": "nps_001"}]
    req = mock_api.get("/net_pay_splits").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["contractor"] == "ctr_456"


@pytest.mark.anyio
async def test_list_earning_codes(mock_api, ctx):
    mock_api.get("/earning_codes").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ec_001"}]},
        )
    )
    result = await list_earning_codes(ctx)
    assert result["results"] == [{"id": "ec_001"}]
