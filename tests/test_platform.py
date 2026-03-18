"""Tests for platform tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.platform import (
    create_communication,
    get_applied_for_ids_report,
    list_notifications,
    list_usage_summaries,
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
async def test_create_communication(mock_api, ctx):
    mock_api.post("/communications").mock(
        return_value=httpx.Response(201, json={"id": "comm_new"})
    )
    result = await create_communication(ctx, company="com_001", type="email")
    assert result["id"] == "comm_new"


@pytest.mark.anyio
async def test_list_usage_summaries(mock_api, ctx):
    mock_api.get("/usage_summaries").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "us_001"}]},
        )
    )
    result = await list_usage_summaries(ctx)
    assert result["results"] == [{"id": "us_001"}]


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
