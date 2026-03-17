"""Tests for webhook tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.webhooks import (
    create_webhook_config,
    delete_webhook_config,
    list_webhook_configs,
    ping_webhook_config,
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
