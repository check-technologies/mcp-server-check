"""Tests for employee tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.employees import (
    create_employee,
    get_employee_paystub,
    list_employee_forms,
    list_employee_paystubs,
    onboard_employee,
    reveal_employee_ssn,
    submit_employee_form,
    update_employee,
)

BASE_URL = "https://sandbox.checkhq.com"


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


@pytest.mark.anyio
async def test_reveal_employee_ssn(mock_api, ctx):
    mock_api.get("/employees/emp_001/reveal").mock(
        return_value=httpx.Response(200, json={"ssn": "123-45-6789"})
    )
    result = await reveal_employee_ssn(ctx, employee_id="emp_001")
    assert result["ssn"] == "123-45-6789"
