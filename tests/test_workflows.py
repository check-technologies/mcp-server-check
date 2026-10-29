"""Tests for workflow composite tools."""

from __future__ import annotations

import httpx
import pytest
from mcp_server_check.tools.workflows import (
    diagnose_payment,
    get_company_overview,
    get_company_tax_overview,
    get_contractor_snapshot,
    get_employee_snapshot,
    get_onboarding_status,
    get_payroll_details,
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
        return_value=httpx.Response(200, json=_list_response([{"id": "pay_001"}]))
    )
    mock_api.get("/bank_accounts").mock(
        return_value=httpx.Response(200, json=_list_response([{"id": "bnk_001"}]))
    )

    result = await get_company_overview(ctx, company_id="com_001")

    assert result["company"]["id"] == "com_001"
    assert result["employees"]["results"][0]["id"] == "emp_001"
    assert result["payrolls"]["results"][0]["id"] == "pay_001"
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
    mock_api.get("/payments/pyt_001").mock(
        return_value=httpx.Response(
            200,
            json={"id": "pyt_001", "status": "failed", "payroll_item": "itm_001"},
        )
    )
    mock_api.get("/payment_attempts").mock(
        return_value=httpx.Response(
            200,
            json=_list_response([{"id": "att_001", "status": "failed"}]),
        )
    )
    mock_api.get("/payroll_items/itm_001").mock(
        return_value=httpx.Response(200, json={"id": "itm_001", "employee": "emp_001"})
    )

    result = await diagnose_payment(ctx, payment_id="pyt_001")

    assert result["payment"]["id"] == "pyt_001"
    assert result["payment_attempts"]["results"][0]["id"] == "att_001"
    assert result["payroll_item"]["id"] == "itm_001"
    req = mock_api.get("/payment_attempts").calls.last.request
    assert req.url.params["payment"] == "pyt_001"


@pytest.mark.anyio
async def test_diagnose_payment_without_payroll_item(mock_api, ctx):
    mock_api.get("/payments/pyt_002").mock(
        return_value=httpx.Response(200, json={"id": "pyt_002", "status": "completed"})
    )
    mock_api.get("/payment_attempts").mock(
        return_value=httpx.Response(
            200, json=_list_response([{"id": "att_002", "status": "completed"}])
        )
    )

    result = await diagnose_payment(ctx, payment_id="pyt_002")

    assert result["payment"]["id"] == "pyt_002"
    assert result["payment_attempts"]["results"][0]["id"] == "att_002"
    assert "payroll_item" not in result
    req = mock_api.get("/payment_attempts").calls.last.request
    assert req.url.params["payment"] == "pyt_002"


# --- New workflow tools ---


@pytest.mark.anyio
async def test_get_payroll_details_full(mock_api, ctx):
    mock_api.get("/payrolls/pay_001").mock(
        return_value=httpx.Response(200, json={"id": "pay_001", "status": "draft"})
    )
    mock_api.get("/payroll_items").mock(
        return_value=httpx.Response(
            200, json=_list_response([{"id": "itm_001", "employee": "emp_001"}])
        )
    )
    mock_api.get("/contractor_payments").mock(
        return_value=httpx.Response(
            200, json=_list_response([{"id": "cpm_001", "contractor": "ctr_001"}])
        )
    )

    result = await get_payroll_details(ctx, payroll_id="pay_001")

    assert result["payroll"]["id"] == "pay_001"
    assert result["payroll_items"]["results"][0]["id"] == "itm_001"
    assert result["contractor_payments"]["results"][0]["id"] == "cpm_001"


@pytest.mark.anyio
async def test_get_payroll_details_minimal(mock_api, ctx):
    mock_api.get("/payrolls/pay_001").mock(
        return_value=httpx.Response(200, json={"id": "pay_001"})
    )

    result = await get_payroll_details(
        ctx,
        payroll_id="pay_001",
        include_items=False,
        include_contractor_payments=False,
    )

    assert result["payroll"]["id"] == "pay_001"
    assert "payroll_items" not in result
    assert "contractor_payments" not in result


@pytest.mark.anyio
async def test_get_contractor_snapshot(mock_api, ctx):
    mock_api.get("/contractors/ctr_001").mock(
        return_value=httpx.Response(
            200, json={"id": "ctr_001", "first_name": "Bob", "last_name": "Smith"}
        )
    )
    mock_api.get("/contractors/ctr_001/payments").mock(
        return_value=httpx.Response(
            200, json=_list_response([{"id": "cpm_001", "amount": "1000.00"}])
        )
    )
    mock_api.get("/contractors/ctr_001/forms").mock(
        return_value=httpx.Response(
            200, json=_list_response([{"id": "frm_001", "type": "w9"}])
        )
    )

    result = await get_contractor_snapshot(ctx, contractor_id="ctr_001")

    assert result["contractor"]["id"] == "ctr_001"
    assert result["payments"]["results"][0]["id"] == "cpm_001"
    assert result["forms"]["results"][0]["id"] == "frm_001"


@pytest.mark.anyio
async def test_get_company_tax_overview(mock_api, ctx):
    mock_api.get("/company_tax_params/com_001").mock(
        return_value=httpx.Response(200, json={"id": "com_001", "params": []})
    )
    mock_api.get("/company_tax_elections").mock(
        return_value=httpx.Response(200, json=_list_response([{"id": "txe_001"}]))
    )
    mock_api.get("/filings").mock(
        return_value=httpx.Response(
            200, json=_list_response([{"id": "fil_001", "status": "filed"}])
        )
    )

    result = await get_company_tax_overview(ctx, company_id="com_001")

    assert result["tax_params"]["id"] == "com_001"
    assert result["tax_elections"]["results"][0]["id"] == "txe_001"
    assert result["filings"]["results"][0]["id"] == "fil_001"


@pytest.mark.anyio
async def test_get_onboarding_status_ready(mock_api, ctx):
    mock_api.get("/companies/com_001").mock(
        return_value=httpx.Response(200, json={"id": "com_001", "status": "active"})
    )
    mock_api.get("/workplaces").mock(
        return_value=httpx.Response(200, json=_list_response([{"id": "wrk_001"}]))
    )
    mock_api.get("/employees").mock(
        return_value=httpx.Response(
            200, json=_list_response([{"id": "emp_001", "first_name": "Jane"}])
        )
    )
    mock_api.get("/bank_accounts").mock(
        return_value=httpx.Response(200, json=_list_response([{"id": "bnk_001"}]))
    )
    mock_api.get("/requirements").mock(
        return_value=httpx.Response(
            200, json=_list_response([{"id": "req_001", "status": "met"}])
        )
    )

    result = await get_onboarding_status(ctx, company_id="com_001")

    assert result["company"]["id"] == "com_001"
    assert result["readiness"]["ready"] is True
    assert result["readiness"]["has_workplaces"] is True
    assert result["readiness"]["has_employees"] is True
    assert result["readiness"]["has_bank_accounts"] is True
    assert result["readiness"]["outstanding_requirements"] == 0


@pytest.mark.anyio
async def test_get_onboarding_status_not_ready(mock_api, ctx):
    mock_api.get("/companies/com_001").mock(
        return_value=httpx.Response(200, json={"id": "com_001", "status": "setup"})
    )
    mock_api.get("/workplaces").mock(
        return_value=httpx.Response(200, json=_list_response([]))
    )
    mock_api.get("/employees").mock(
        return_value=httpx.Response(200, json=_list_response([]))
    )
    mock_api.get("/bank_accounts").mock(
        return_value=httpx.Response(200, json=_list_response([]))
    )
    mock_api.get("/requirements").mock(
        return_value=httpx.Response(
            200,
            json=_list_response(
                [
                    {"id": "req_001", "status": "unmet"},
                    {"id": "req_002", "status": "met"},
                ]
            ),
        )
    )

    result = await get_onboarding_status(ctx, company_id="com_001")

    assert result["readiness"]["ready"] is False
    assert result["readiness"]["has_workplaces"] is False
    assert result["readiness"]["outstanding_requirements"] == 1
    assert result["readiness"]["total_requirements"] == 2


@pytest.mark.anyio
async def test_get_payroll_details_drops_items_the_api_inlined_on_the_payroll(
    mock_api, ctx
):
    # Before API version 2025-01-01 the payroll itself carries every item; the
    # paginated payroll_items call is the one copy this tool should return.
    mock_api.get("/payrolls/pay_001").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "pay_001",
                "items": [{"id": "itm_001"}, {"id": "itm_002"}],
                "contractor_payments": [],
            },
        )
    )
    mock_api.get("/payroll_items").mock(
        return_value=httpx.Response(200, json=_list_response([{"id": "itm_001"}]))
    )
    mock_api.get("/contractor_payments").mock(
        return_value=httpx.Response(200, json=_list_response([]))
    )

    result = await get_payroll_details(ctx, payroll_id="pay_001", item_limit=1)

    assert result["payroll"] == {
        "id": "pay_001",
        "items_count": 2,
        "contractor_payments_count": 0,
    }
    assert result["payroll_items"]["results"] == [{"id": "itm_001"}]
