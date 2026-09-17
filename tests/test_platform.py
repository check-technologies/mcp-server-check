"""Tests for platform tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.platform import (
    create_communication,
    get_accounting_mappings,
    get_applied_for_ids_report,
    list_accounting_accounts,
    list_accounting_integrations,
    list_accounting_sync_attempts,
    list_communications,
    list_integration_accesses,
    list_integration_permissions,
    list_notifications,
    list_requirements,
    list_usage_records,
    list_usage_summaries,
    refresh_accounting_accounts,
    sync_accounting,
    validate_address,
)


@pytest.mark.anyio
async def test_list_notifications(mock_api, ctx):
    mock_api.get("/notifications").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ntf_001"}]},
        )
    )
    result = await list_notifications(ctx)
    assert result["results"] == [{"id": "ntf_001"}]


@pytest.mark.anyio
async def test_list_notifications_with_filters(mock_api, ctx):
    mock_api.get("/notifications").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ntf_001"}]},
        )
    )
    result = await list_notifications(
        ctx,
        company="com_123",
        topic="payroll.completed",
        start_date="2026-01-01",
        end_date="2026-06-30",
        recipient_type="employee",
        recipient="emp_456",
    )
    assert result["results"] == [{"id": "ntf_001"}]
    req = mock_api.get("/notifications").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["topic"] == "payroll.completed"
    assert req.url.params["start_date"] == "2026-01-01"
    assert req.url.params["end_date"] == "2026-06-30"
    assert req.url.params["recipient_type"] == "employee"
    assert req.url.params["recipient"] == "emp_456"


@pytest.mark.anyio
async def test_list_communications_with_filters(mock_api, ctx):
    mock_api.get("/communications").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "comm_001"}]},
        )
    )
    result = await list_communications(
        ctx,
        company="com_123",
        start_date="2026-01-01",
        type="email",
        recipient="emp_456",
    )
    assert result["results"] == [{"id": "comm_001"}]
    req = mock_api.get("/communications").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["start_date"] == "2026-01-01"
    assert req.url.params["type"] == "email"
    assert req.url.params["recipient"] == "emp_456"
    assert "end_date" not in req.url.params


@pytest.mark.anyio
async def test_create_communication(mock_api, ctx):
    mock_api.post("/communications").mock(
        return_value=httpx.Response(201, json={"id": "comm_new"})
    )
    result = await create_communication(ctx, company="com_001", type="email")
    assert result["id"] == "comm_new"


@pytest.mark.anyio
async def test_list_usage_summaries(mock_api, ctx):
    mock_api.get("/usage/summaries").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "us_001"}]},
        )
    )
    result = await list_usage_summaries(ctx)
    assert result["results"] == [{"id": "us_001"}]


@pytest.mark.anyio
async def test_list_usage_summaries_with_filters(mock_api, ctx):
    mock_api.get("/usage/summaries").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "us_001"}]},
        )
    )
    result = await list_usage_summaries(
        ctx, company="com_123", category="payroll", period_start="2026-01-01"
    )
    assert result["results"] == [{"id": "us_001"}]
    req = mock_api.get("/usage/summaries").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["category"] == "payroll"
    assert req.url.params["period_start"] == "2026-01-01"
    assert "period_end" not in req.url.params


@pytest.mark.anyio
async def test_list_usage_records_with_filters(mock_api, ctx):
    mock_api.get("/usage/records").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ur_001"}]},
        )
    )
    result = await list_usage_records(
        ctx, company="com_123", resource_type="employee", period_start="2026-01-01"
    )
    assert result["results"] == [{"id": "ur_001"}]
    req = mock_api.get("/usage/records").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["resource_type"] == "employee"
    assert req.url.params["period_start"] == "2026-01-01"


@pytest.mark.anyio
async def test_list_integration_permissions_with_filters(mock_api, ctx):
    mock_api.get("/integration_permissions").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ip_001"}]},
        )
    )
    result = await list_integration_permissions(ctx, integration_partner="ipt_123")
    assert result["results"] == [{"id": "ip_001"}]
    req = mock_api.get("/integration_permissions").calls.last.request
    assert req.url.params["integration_partner"] == "ipt_123"


@pytest.mark.anyio
async def test_list_integration_accesses_with_filters(mock_api, ctx):
    mock_api.get("/integration_accesses").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ia_001"}]},
        )
    )
    result = await list_integration_accesses(ctx, company="com_123")
    assert result["results"] == [{"id": "ia_001"}]
    req = mock_api.get("/integration_accesses").calls.last.request
    assert req.url.params["company"] == "com_123"


@pytest.mark.anyio
async def test_list_requirements_with_filters(mock_api, ctx):
    mock_api.get("/requirements").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "req_001"}]},
        )
    )
    result = await list_requirements(
        ctx, company="com_123", category="tax", status="pending"
    )
    assert result["results"] == [{"id": "req_001"}]
    req = mock_api.get("/requirements").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["category"] == "tax"
    assert req.url.params["status"] == "pending"
    assert "requirement" not in req.url.params


@pytest.mark.anyio
async def test_list_accounting_integrations(mock_api, ctx):
    mock_api.get("/integrations/accounting").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [{"id": "ai_x", "valid_token": True}],
            },
        )
    )
    result = await list_accounting_integrations(ctx, company="com_123")
    assert result["results"] == [{"id": "ai_x", "valid_token": True}]
    req = mock_api.get("/integrations/accounting").calls.last.request
    assert req.url.params["company"] == "com_123"


@pytest.mark.anyio
async def test_sync_accounting(mock_api, ctx):
    mock_api.post("/integrations/accounting/ai_x/sync").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [
                    {"id": "ais_001", "payroll": "pay_1", "status": "pending"},
                    {"id": "ais_002", "payroll": "pay_2", "status": "pending"},
                ],
            },
        )
    )
    result = await sync_accounting(
        ctx, "ai_x", payrolls=["pay_1", "pay_2"], resync=True
    )
    assert [r["payroll"] for r in result["results"]] == ["pay_1", "pay_2"]
    req = mock_api.post("/integrations/accounting/ai_x/sync").calls.last.request
    assert json.loads(req.content) == {"payrolls": ["pay_1", "pay_2"], "resync": True}


@pytest.mark.anyio
async def test_sync_accounting_omits_resync_when_not_passed(mock_api, ctx):
    mock_api.post("/integrations/accounting/ai_x/sync").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [{"id": "ais_001", "payroll": "pay_1", "status": "pending"}],
            },
        )
    )
    await sync_accounting(ctx, "ai_x", payrolls=["pay_1"])
    req = mock_api.post("/integrations/accounting/ai_x/sync").calls.last.request
    assert json.loads(req.content) == {"payrolls": ["pay_1"]}


@pytest.mark.anyio
async def test_list_accounting_sync_attempts(mock_api, ctx):
    mock_api.get("/integrations/accounting/ai_x/sync/attempts").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": "ais_001",
                        "payroll": "pay_1",
                        "status": "failure",
                        "failure_reason": "Refresh Token is invalid.",
                    }
                ],
            },
        )
    )
    result = await list_accounting_sync_attempts(ctx, "ai_x", payroll="pay_1")
    assert result["results"][0]["failure_reason"] == "Refresh Token is invalid."
    req = mock_api.get("/integrations/accounting/ai_x/sync/attempts").calls.last.request
    assert req.url.params["payroll"] == "pay_1"


@pytest.mark.anyio
async def test_list_accounting_accounts(mock_api, ctx):
    route = mock_api.get("/integrations/accounting/ai_x/accounts").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "aia_001"}]},
        )
    )
    result = await list_accounting_accounts(ctx, "ai_x")
    assert result["results"] == [{"id": "aia_001"}]
    assert route.called


@pytest.mark.anyio
async def test_refresh_accounting_accounts(mock_api, ctx):
    route = mock_api.post("/integrations/accounting/ai_x/accounts/refresh").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "aia_001"}]},
        )
    )
    result = await refresh_accounting_accounts(ctx, "ai_x")
    assert result["results"] == [{"id": "aia_001"}]
    assert route.called


@pytest.mark.anyio
async def test_get_accounting_mappings(mock_api, ctx):
    route = mock_api.get("/integrations/accounting/ai_x/mappings").mock(
        return_value=httpx.Response(200, json={"type": "basic", "active": True})
    )
    result = await get_accounting_mappings(ctx, "ai_x")
    assert result["type"] == "basic"
    assert route.called


@pytest.mark.anyio
async def test_validate_address(mock_api, ctx):
    mock_api.post("/addresses/validate").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    result = await validate_address(
        ctx, line1="123 Main St", city="Anytown", state="CA", postal_code="12345"
    )
    assert result["valid"] is True


@pytest.mark.anyio
async def test_get_applied_for_ids_report(mock_api, ctx):
    mock_api.get("/reports/applied_for_ids").mock(
        return_value=httpx.Response(200, json={"report": "data"})
    )
    result = await get_applied_for_ids_report(ctx)
    assert result["report"] == "data"
