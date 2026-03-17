"""Tests for compensation tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.compensation import (
    create_benefit,
    create_pay_schedule,
    delete_pay_schedule,
    list_company_benefits,
    list_earning_codes,
    list_pay_schedules,
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
async def test_list_earning_codes(mock_api, ctx):
    mock_api.get("/earning_codes").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ec_001"}]},
        )
    )
    result = await list_earning_codes(ctx)
    assert result["results"] == [{"id": "ec_001"}]
