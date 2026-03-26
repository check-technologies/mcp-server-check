"""Tests for employee tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.employees import (
    create_employee,
    get_employee_paystub,
    list_employee_forms,
    list_employee_paystubs,
    list_employees,
    onboard_employee,
    submit_employee_form,
    update_employee,
)

BASE_URL = "https://sandbox.checkhq.com"


@pytest.mark.anyio
async def test_list_employees_with_filters(mock_api, ctx):
    mock_api.get("/employees").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "emp_001"}]},
        )
    )
    result = await list_employees(
        ctx, company="com_123", workplace="wrk_456", active=True
    )
    assert result["results"] == [{"id": "emp_001"}]
    req = mock_api.get("/employees").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["workplace"] == "wrk_456"
    assert req.url.params["active"] == "true"


@pytest.mark.anyio
async def test_list_employee_paystubs_with_filters(mock_api, ctx):
    mock_api.get("/employees/emp_001/paystubs").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ps_001"}]},
        )
    )
    result = await list_employee_paystubs(
        ctx,
        employee_id="emp_001",
        payroll="prl_123",
        status="paid",
        start="2026-01-01",
        end="2026-06-30",
        type="regular",
    )
    assert result["results"] == [{"id": "ps_001"}]
    req = mock_api.get("/employees/emp_001/paystubs").calls.last.request
    assert req.url.params["payroll"] == "prl_123"
    assert req.url.params["status"] == "paid"
    assert req.url.params["start"] == "2026-01-01"
    assert req.url.params["end"] == "2026-06-30"
    assert req.url.params["type"] == "regular"


@pytest.mark.anyio
async def test_create_employee(mock_api, ctx):
    mock_api.post("/employees").mock(
        return_value=httpx.Response(
            201,
            json={"id": "emp_new", "first_name": "Jane", "last_name": "Doe"},
        )
    )
    result = await create_employee(
        ctx, company="com_001", first_name="Jane", last_name="Doe"
    )
    assert result["id"] == "emp_new"


@pytest.mark.anyio
async def test_update_employee(mock_api, ctx):
    mock_api.patch("/employees/emp_001").mock(
        return_value=httpx.Response(200, json={"id": "emp_001", "first_name": "Janet"})
    )
    result = await update_employee(ctx, employee_id="emp_001", first_name="Janet")
    assert result["first_name"] == "Janet"


@pytest.mark.anyio
async def test_onboard_employee(mock_api, ctx):
    mock_api.post("/employees/emp_001/onboard").mock(
        return_value=httpx.Response(200, json={"id": "emp_001", "onboard": "complete"})
    )
    result = await onboard_employee(ctx, employee_id="emp_001")
    assert result["onboard"] == "complete"


@pytest.mark.anyio
async def test_list_employee_paystubs(mock_api, ctx):
    mock_api.get("/employees/emp_001/paystubs").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ps_001"}]},
        )
    )
    result = await list_employee_paystubs(ctx, employee_id="emp_001")
    assert result["results"] == [{"id": "ps_001"}]


@pytest.mark.anyio
async def test_get_employee_paystub(mock_api, ctx):
    mock_api.get("/employees/emp_001/paystubs/prl_001").mock(
        return_value=httpx.Response(200, json={"id": "ps_001", "net_pay": "1000"})
    )
    result = await get_employee_paystub(
        ctx, employee_id="emp_001", payroll_id="prl_001"
    )
    assert result["net_pay"] == "1000"


@pytest.mark.anyio
async def test_list_employee_forms(mock_api, ctx):
    mock_api.get("/employees/emp_001/forms").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "frm_001"}]},
        )
    )
    result = await list_employee_forms(ctx, employee_id="emp_001")
    assert result["results"] == [{"id": "frm_001"}]


@pytest.mark.anyio
async def test_submit_employee_form(mock_api, ctx):
    mock_api.post("/employees/emp_001/forms/frm_001/submit").mock(
        return_value=httpx.Response(200, json={"id": "frm_001", "status": "submitted"})
    )
    result = await submit_employee_form(ctx, employee_id="emp_001", form_id="frm_001")
    assert result["status"] == "submitted"
