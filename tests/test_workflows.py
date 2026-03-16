"""Tests for workflow composite tools."""

from __future__ import annotations

import httpx
import pytest
from mcp_server_check.tools.workflows import (
    diagnose_payment,
    get_company_overview,
    get_employee_snapshot,
)


def _list_response(results):
    """Helper to build a paginated list response."""
    return {"next": None, "previous": None, "results": results}


@pytest.mark.anyio
async def test_get_company_overview_full(mock_api, ctx):
    mock_api.get("/companies/com_001").mock(
        return_value=httpx.Response(200, json={"id": "com_001", "legal_name": "Acme"})
    )
    mock_api.get("/employees").mock(
        return_value=httpx.Response(
            200, json=_list_response([{"id": "emp_001", "first_name": "Jane"}])
        )
    )
    mock_api.get("/payrolls").mock(
        return_value=httpx.Response(200, json=_list_response([{"id": "prl_001"}]))
    )
    mock_api.get("/bank_accounts").mock(
        return_value=httpx.Response(200, json=_list_response([{"id": "bnk_001"}]))
    )

    result = await get_company_overview(ctx, company_id="com_001")

    assert result["company"]["id"] == "com_001"
    assert result["employees"]["results"][0]["id"] == "emp_001"
    assert result["payrolls"]["results"][0]["id"] == "prl_001"
    assert result["bank_accounts"]["results"][0]["id"] == "bnk_001"


@pytest.mark.anyio
async def test_get_company_overview_minimal(mock_api, ctx):
    mock_api.get("/companies/com_001").mock(
        return_value=httpx.Response(200, json={"id": "com_001"})
    )

    result = await get_company_overview(
        ctx,
        company_id="com_001",
        include_employees=False,
        include_payrolls=False,
        include_bank_accounts=False,
    )

    assert result["company"]["id"] == "com_001"
    assert "employees" not in result
    assert "payrolls" not in result
    assert "bank_accounts" not in result


@pytest.mark.anyio
async def test_get_employee_snapshot_full(mock_api, ctx):
    mock_api.get("/employees/emp_001").mock(
        return_value=httpx.Response(
            200, json={"id": "emp_001", "first_name": "Jane", "last_name": "Doe"}
        )
    )
    mock_api.get("/employee_tax_params/emp_001").mock(
        return_value=httpx.Response(200, json={"id": "emp_001", "params": []})
    )
    mock_api.get("/employees/emp_001/paystubs").mock(
        return_value=httpx.Response(200, json=_list_response([{"id": "stub_001"}]))
    )

    result = await get_employee_snapshot(ctx, employee_id="emp_001")

    assert result["employee"]["id"] == "emp_001"
    assert "tax_params" in result
    assert result["paystubs"]["results"][0]["id"] == "stub_001"


@pytest.mark.anyio
async def test_get_employee_snapshot_minimal(mock_api, ctx):
    mock_api.get("/employees/emp_001").mock(
        return_value=httpx.Response(200, json={"id": "emp_001"})
    )

    result = await get_employee_snapshot(
        ctx, employee_id="emp_001", include_tax_params=False, include_paystubs=False
    )

    assert result["employee"]["id"] == "emp_001"
    assert "tax_params" not in result
    assert "paystubs" not in result


@pytest.mark.anyio
async def test_diagnose_payment_with_payroll_item(mock_api, ctx):
    mock_api.get("/payments/pmt_001").mock(
        return_value=httpx.Response(
            200,
            json={"id": "pmt_001", "status": "failed", "payroll_item": "pit_001"},
        )
    )
    mock_api.get("/payments/pmt_001/payment_attempts").mock(
        return_value=httpx.Response(
            200,
            json=_list_response([{"id": "att_001", "status": "failed"}]),
        )
    )
    mock_api.get("/payroll_items/pit_001").mock(
        return_value=httpx.Response(200, json={"id": "pit_001", "employee": "emp_001"})
    )

    result = await diagnose_payment(ctx, payment_id="pmt_001")

    assert result["payment"]["id"] == "pmt_001"
    assert result["payment_attempts"]["results"][0]["id"] == "att_001"
    assert result["payroll_item"]["id"] == "pit_001"


@pytest.mark.anyio
async def test_diagnose_payment_without_payroll_item(mock_api, ctx):
    mock_api.get("/payments/pmt_002").mock(
        return_value=httpx.Response(200, json={"id": "pmt_002", "status": "completed"})
    )
    mock_api.get("/payments/pmt_002/payment_attempts").mock(
        return_value=httpx.Response(
            200, json=_list_response([{"id": "att_002", "status": "completed"}])
        )
    )

    result = await diagnose_payment(ctx, payment_id="pmt_002")

    assert result["payment"]["id"] == "pmt_002"
    assert result["payment_attempts"]["results"][0]["id"] == "att_002"
    assert "payroll_item" not in result
