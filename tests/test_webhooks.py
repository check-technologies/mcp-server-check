"""Tests for webhook tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.webhooks import (
    create_webhook_config,
    delete_webhook_config,
    get_event,
    list_events,
    list_webhook_configs,
    ping_webhook_config,
    retry_event,
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
async def test_list_events(mock_api, ctx):
    route = mock_api.get("/events").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": "whe_001",
                        "status": "delivered",
                        "delivery_attempts": [
                            {"status_code": 200, "created_at": "2026-08-01T00:00:00Z"}
                        ],
                    }
                ],
            },
        )
    )
    result = await list_events(
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
async def test_get_event(mock_api, ctx):
    mock_api.get("/events/whe_001").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "whe_001",
                "status": "failed",
                "delivery_attempts": [
                    {"status_code": None, "created_at": "2026-08-01T00:00:00Z"}
                ],
            },
        )
    )
    result = await get_event(ctx, event_id="whe_001")
    assert result["status"] == "failed"
    assert result["delivery_attempts"][0]["status_code"] is None


@pytest.mark.anyio
async def test_retry_event_sends_idempotency_key(mock_api, ctx):
    route = mock_api.post("/events/whe_001/retry").mock(
        return_value=httpx.Response(202, json={"id": "whe_001", "status": "pending"})
    )
    result = await retry_event(ctx, event_id="whe_001")
    assert result["id"] == "whe_001"
    assert route.calls.last.request.headers.get("X-Idempotency-Key")
