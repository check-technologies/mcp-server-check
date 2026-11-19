"""Tests for time off tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.time_off import (
    create_time_off_balance,
    create_time_off_enrollment,
    create_time_off_entry,
    create_time_off_policy,
    delete_time_off_enrollment,
    get_time_off_enrollment,
    list_time_off_enrollments,
    list_time_off_policies,
    update_time_off_balance,
    update_time_off_enrollment,
    update_time_off_policy,
)


@pytest.mark.anyio
async def test_list_time_off_policies_filters(mock_api, ctx):
    route = mock_api.get("/time_off_policies").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [{"id": "time_off_policy_1"}],
            },
        )
    )
    result = await list_time_off_policies(ctx, company="com_001", status="active")
    assert result["results"] == [{"id": "time_off_policy_1"}]
    params = route.calls[0].request.url.params
    assert params["company"] == "com_001"
    assert params["status"] == "active"


@pytest.mark.anyio
async def test_create_time_off_policy_sends_only_given_options(mock_api, ctx):
    route = mock_api.post("/time_off_policies").mock(
        return_value=httpx.Response(200, json={"id": "time_off_policy_new"})
    )
    await create_time_off_policy(
        ctx,
        company="com_001",
        label="PTO",
        accrual_method="per_payroll",
        policy_year={"basis": "fixed_date", "date": "01-01"},
        per_payroll_options={"hours_per_year": "120.00"},
        idempotency_key="key-1",
    )
    request = route.calls[0].request
    assert json.loads(request.content) == {
        "company": "com_001",
        "label": "PTO",
        "accrual_method": "per_payroll",
        "policy_year": {"basis": "fixed_date", "date": "01-01"},
        "per_payroll_options": {"hours_per_year": "120.00"},
    }
    assert request.headers["X-Idempotency-Key"] == "key-1"


@pytest.mark.anyio
async def test_update_time_off_policy(mock_api, ctx):
    route = mock_api.patch("/time_off_policies/time_off_policy_1").mock(
        return_value=httpx.Response(200, json={"status": "archived"})
    )
    await update_time_off_policy(ctx, "time_off_policy_1", status="archived")
    assert json.loads(route.calls[0].request.content) == {"status": "archived"}


@pytest.mark.anyio
async def test_create_time_off_balance(mock_api, ctx):
    route = mock_api.post("/time_off_balances").mock(
        return_value=httpx.Response(200, json={"id": "time_off_balance_new"})
    )
    await create_time_off_balance(ctx, employee="emp_001", label="PTO")
    assert json.loads(route.calls[0].request.content) == {
        "employee": "emp_001",
        "label": "PTO",
    }


@pytest.mark.anyio
async def test_update_time_off_balance(mock_api, ctx):
    route = mock_api.patch("/time_off_balances/time_off_balance_1").mock(
        return_value=httpx.Response(200, json={"id": "time_off_balance_1"})
    )
    await update_time_off_balance(ctx, "time_off_balance_1", metadata={"a": None})
    assert json.loads(route.calls[0].request.content) == {"metadata": {"a": None}}


@pytest.mark.anyio
async def test_list_time_off_enrollments_filters(mock_api, ctx):
    route = mock_api.get("/time_off_enrollments").mock(
        return_value=httpx.Response(
            200, json={"next": None, "previous": None, "results": []}
        )
    )
    await list_time_off_enrollments(
        ctx, balance="time_off_balance_1", policy="time_off_policy_1"
    )
    params = route.calls[0].request.url.params
    assert params["balance"] == "time_off_balance_1"
    assert params["policy"] == "time_off_policy_1"
    assert "employee" not in params


@pytest.mark.anyio
async def test_get_time_off_enrollment(mock_api, ctx):
    mock_api.get("/time_off_enrollments/time_off_enrollment_1").mock(
        return_value=httpx.Response(200, json={"id": "time_off_enrollment_1"})
    )
    result = await get_time_off_enrollment(ctx, "time_off_enrollment_1")
    assert result["id"] == "time_off_enrollment_1"


@pytest.mark.anyio
async def test_create_time_off_enrollment(mock_api, ctx):
    route = mock_api.post("/time_off_enrollments").mock(
        return_value=httpx.Response(200, json={"id": "time_off_enrollment_new"})
    )
    await create_time_off_enrollment(
        ctx,
        balance="time_off_balance_1",
        policy="time_off_policy_1",
        effective_start="2026-01-01",
    )
    assert json.loads(route.calls[0].request.content) == {
        "balance": "time_off_balance_1",
        "policy": "time_off_policy_1",
        "effective_start": "2026-01-01",
    }


@pytest.mark.anyio
async def test_update_time_off_enrollment_sends_metadata_alone(mock_api, ctx):
    route = mock_api.patch("/time_off_enrollments/time_off_enrollment_1").mock(
        return_value=httpx.Response(200, json={"id": "time_off_enrollment_1"})
    )
    await update_time_off_enrollment(ctx, "time_off_enrollment_1", metadata={"a": "1"})
    assert json.loads(route.calls[0].request.content) == {"metadata": {"a": "1"}}


@pytest.mark.anyio
async def test_update_time_off_enrollment_reopens_with_clear_fields(mock_api, ctx):
    route = mock_api.patch("/time_off_enrollments/time_off_enrollment_1").mock(
        return_value=httpx.Response(200, json={"id": "time_off_enrollment_1"})
    )
    await update_time_off_enrollment(
        ctx, "time_off_enrollment_1", clear_fields=["effective_end"]
    )
    assert json.loads(route.calls[0].request.content) == {"effective_end": None}


@pytest.mark.anyio
async def test_update_time_off_enrollment_rejects_other_clear_fields(ctx):
    with pytest.raises(ValueError, match="cannot clear metadata"):
        await update_time_off_enrollment(
            ctx, "time_off_enrollment_1", clear_fields=["metadata"]
        )


@pytest.mark.anyio
async def test_delete_time_off_enrollment(mock_api, ctx):
    route = mock_api.delete("/time_off_enrollments/time_off_enrollment_1").mock(
        return_value=httpx.Response(200, json={"id": "time_off_enrollment_1"})
    )
    result = await delete_time_off_enrollment(ctx, "time_off_enrollment_1")
    assert route.called
    assert result["id"] == "time_off_enrollment_1"


@pytest.mark.anyio
async def test_create_time_off_entry_is_manual(mock_api, ctx):
    route = mock_api.post("/time_off_entries").mock(
        return_value=httpx.Response(200, json={"id": "time_off_entry_new"})
    )
    await create_time_off_entry(
        ctx,
        balance="time_off_balance_1",
        hours="24.00",
        description="Opening balance",
    )
    assert json.loads(route.calls[0].request.content) == {
        "balance": "time_off_balance_1",
        "hours": "24.00",
        "source": "manual",
        "description": "Opening balance",
    }


@pytest.mark.anyio
async def test_not_found_without_the_feature_says_time_off_is_not_enabled(
    mock_api, ctx
):
    mock_api.get("/time_off_enrollments/time_off_enrollment_1").mock(
        return_value=httpx.Response(404, json={"error": {"type": "not_found"}})
    )
    mock_api.get("/time_off_policies").mock(
        return_value=httpx.Response(404, json={"error": {"type": "not_found"}})
    )
    result = await get_time_off_enrollment(ctx, "time_off_enrollment_1")
    assert result["error"] is True
    assert result["time_off_not_enabled"] is True
    assert "isn't enabled" in result["detail"]


@pytest.mark.anyio
async def test_not_found_with_the_feature_passes_the_404_through(mock_api, ctx):
    not_found = {"error": {"type": "not_found"}}
    mock_api.get("/time_off_enrollments/time_off_enrollment_1").mock(
        return_value=httpx.Response(404, json=not_found)
    )
    mock_api.get("/time_off_policies").mock(
        return_value=httpx.Response(
            200, json={"next": None, "previous": None, "results": []}
        )
    )
    result = await get_time_off_enrollment(ctx, "time_off_enrollment_1")
    assert result == {"error": True, "status_code": 404, "detail": not_found}
