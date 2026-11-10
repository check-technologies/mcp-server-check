"""Tests for webhook tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.webhooks import (
    create_webhook_config,
    delete_webhook_config,
    get_webhook_delivery,
    list_webhook_configs,
    list_webhook_deliveries,
    list_webhook_event_types,
    ping_webhook_config,
    retry_webhook_delivery,
    update_webhook_config,
)


@pytest.mark.anyio
async def test_list_webhook_configs(mock_api, ctx):
    mock_api.get("/webhook_configs").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "whc_001"}]},
        )
    )
    result = await list_webhook_configs(ctx)
    assert result["results"] == [{"id": "whc_001"}]


@pytest.mark.anyio
async def test_create_webhook_config(mock_api, ctx):
    mock_api.post("/webhook_configs").mock(
        return_value=httpx.Response(201, json={"id": "whc_new"})
    )
    result = await create_webhook_config(ctx, url="https://example.com/webhook")
    assert result["id"] == "whc_new"


@pytest.mark.anyio
async def test_create_webhook_config_with_api_version(mock_api, ctx):
    route = mock_api.post("/webhook_configs").mock(
        return_value=httpx.Response(
            201, json={"id": "whc_new", "api_version": "2025-01-01"}
        )
    )
    result = await create_webhook_config(
        ctx,
        url="https://example.com/webhook",
        api_version="2025-01-01",
    )
    assert result["api_version"] == "2025-01-01"
    assert json.loads(route.calls.last.request.content) == {
        "url": "https://example.com/webhook",
        "api_version": "2025-01-01",
    }


@pytest.mark.anyio
async def test_create_webhook_config_with_event_types(mock_api, ctx):
    route = mock_api.post("/webhook_configs").mock(
        return_value=httpx.Response(
            201, json={"id": "whc_new", "event_types": ["employee.created"]}
        )
    )
    result = await create_webhook_config(
        ctx,
        url="https://example.com/webhook",
        event_types=["employee.created"],
    )
    assert result["event_types"] == ["employee.created"]
    assert json.loads(route.calls.last.request.content) == {
        "url": "https://example.com/webhook",
        "event_types": ["employee.created"],
    }


@pytest.mark.anyio
async def test_create_webhook_config_omits_event_types_by_default(mock_api, ctx):
    route = mock_api.post("/webhook_configs").mock(
        return_value=httpx.Response(201, json={"id": "whc_new", "event_types": []})
    )
    await create_webhook_config(ctx, url="https://example.com/webhook")
    assert "event_types" not in json.loads(route.calls.last.request.content)


@pytest.mark.anyio
async def test_update_webhook_config_replaces_event_types(mock_api, ctx):
    route = mock_api.patch("/webhook_configs/whc_001").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "whc_001",
                "event_types": ["employee.created", "payroll.updated"],
            },
        )
    )
    result = await update_webhook_config(
        ctx,
        webhook_config_id="whc_001",
        event_types=["employee.created", "payroll.updated"],
    )
    assert result["event_types"] == ["employee.created", "payroll.updated"]
    assert json.loads(route.calls.last.request.content) == {
        "event_types": ["employee.created", "payroll.updated"],
    }


@pytest.mark.anyio
async def test_update_webhook_config_sends_empty_event_types(mock_api, ctx):
    """An empty list means "select nothing" and must reach the API, unlike None."""
    route = mock_api.patch("/webhook_configs/whc_001").mock(
        return_value=httpx.Response(200, json={"id": "whc_001", "event_types": []})
    )
    await update_webhook_config(ctx, webhook_config_id="whc_001", event_types=[])
    assert json.loads(route.calls.last.request.content) == {"event_types": []}


@pytest.mark.anyio
async def test_update_webhook_config_with_api_version(mock_api, ctx):
    route = mock_api.patch("/webhook_configs/whc_001").mock(
        return_value=httpx.Response(
            200, json={"id": "whc_001", "api_version": "2021-09-02"}
        )
    )
    result = await update_webhook_config(
        ctx,
        webhook_config_id="whc_001",
        api_version="2021-09-02",
    )
    assert result["api_version"] == "2021-09-02"
    assert json.loads(route.calls.last.request.content) == {
        "api_version": "2021-09-02",
    }


@pytest.mark.anyio
async def test_delete_webhook_config(mock_api, ctx):
    mock_api.delete("/webhook_configs/whc_001").mock(return_value=httpx.Response(204))
    result = await delete_webhook_config(ctx, webhook_config_id="whc_001")
    assert result == {"success": True}


@pytest.mark.anyio
async def test_ping_webhook_config(mock_api, ctx):
    mock_api.post("/webhook_configs/whc_001/ping").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await ping_webhook_config(ctx, webhook_config_id="whc_001")
    assert result["success"] is True


@pytest.mark.anyio
async def test_list_webhook_event_types(mock_api, ctx):
    route = mock_api.get("/event_types").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "type": "payroll.status_change",
                        "description": "...",
                        "status": "deprecated",
                        "selectable": True,
                        "unavailable_reason": None,
                        "replacement": "payroll.updated",
                        "migration_guide_url": None,
                        "retires_at": None,
                    },
                    {
                        "type": "payroll.updated",
                        "description": "...",
                        "status": "supported",
                        "selectable": True,
                        "unavailable_reason": None,
                        "replacement": None,
                        "migration_guide_url": None,
                        "retires_at": None,
                    },
                ]
            },
        )
    )
    result = await list_webhook_event_types(ctx)
    assert [e["type"] for e in result["results"]] == [
        "payroll.status_change",
        "payroll.updated",
    ]
    assert result["results"][0]["replacement"] == "payroll.updated"
    assert not route.calls.last.request.url.params


@pytest.mark.anyio
async def test_list_webhook_event_types_for_a_config(mock_api, ctx):
    route = mock_api.get("/event_types").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await list_webhook_event_types(ctx, webhook_config="whc_001")
    assert dict(route.calls.last.request.url.params) == {"webhook_config": "whc_001"}


@pytest.mark.anyio
async def test_list_webhook_event_types_at_an_api_version(mock_api, ctx):
    route = mock_api.get("/event_types").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await list_webhook_event_types(ctx, api_version="2025-01-01")
    assert dict(route.calls.last.request.url.params) == {"api_version": "2025-01-01"}


@pytest.mark.anyio
async def test_list_webhook_deliveries(mock_api, ctx):
    route = mock_api.get("/webhook_deliveries").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": "whe_001",
                        "status": "delivered",
                        "attempts": [
                            {"status_code": 200, "created_at": "2026-08-01T00:00:00Z"}
                        ],
                    }
                ],
            },
        )
    )
    result = await list_webhook_deliveries(
        ctx,
        webhook_config="whc_001",
        status="delivered",
        created_after="2026-08-01T00:00:00Z",
    )
    assert result["results"][0]["id"] == "whe_001"
    params = route.calls.last.request.url.params
    assert params["webhook_config"] == "whc_001"
    assert params["status"] == "delivered"
    assert params["created_after"] == "2026-08-01T00:00:00Z"


@pytest.mark.anyio
async def test_get_webhook_delivery(mock_api, ctx):
    mock_api.get("/webhook_deliveries/whe_001").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "whe_001",
                "status": "failed",
                "attempts": [
                    {"status_code": None, "created_at": "2026-08-01T00:00:00Z"}
                ],
            },
        )
    )
    result = await get_webhook_delivery(ctx, webhook_delivery_id="whe_001")
    assert result["status"] == "failed"
    assert result["attempts"][0]["status_code"] is None


@pytest.mark.anyio
async def test_retry_webhook_delivery_sends_idempotency_key(mock_api, ctx):
    route = mock_api.post("/webhook_deliveries/whe_001/retry").mock(
        return_value=httpx.Response(202, json={"id": "whe_001", "status": "pending"})
    )
    result = await retry_webhook_delivery(ctx, webhook_delivery_id="whe_001")
    assert result["id"] == "whe_001"
    assert route.calls.last.request.headers.get("X-Idempotency-Key")
