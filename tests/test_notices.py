"""Tests for notice tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.notices import create_notice, get_notice, list_notices


@pytest.mark.anyio
async def test_list_notices(mock_api, ctx):
    route = mock_api.get("/notices").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "ntc_001"}]},
        )
    )
    result = await list_notices(ctx, company="com_001", limit=10, cursor="cur_1")
    assert result["results"][0]["id"] == "ntc_001"
    assert route.calls.last.request.url.params["company"] == "com_001"
    assert route.calls.last.request.url.params["limit"] == "10"
    assert route.calls.last.request.url.params["cursor"] == "cur_1"


@pytest.mark.anyio
async def test_get_notice(mock_api, ctx):
    mock_api.get("/notices/ntc_001").mock(
        return_value=httpx.Response(200, json={"id": "ntc_001", "processing_status": "processing"})
    )
    result = await get_notice(ctx, notice_id="ntc_001")
    assert result["processing_status"] == "processing"


@pytest.mark.anyio
async def test_create_notice(mock_api, ctx):
    route = mock_api.post("/notices").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "ntc_001",
                "company": "com_001",
                "attachments": ["file_001"],
                "processing_status": "processing",
            },
        )
    )
    result = await create_notice(
        ctx,
        company="com_001",
        attachments=["file_001"],
        description="IRS letter",
        idempotency_key="idem-1",
    )
    assert result["id"] == "ntc_001"
    assert json.loads(route.calls.last.request.content) == {
        "company": "com_001",
        "attachments": ["file_001"],
        "description": "IRS letter",
    }
    assert route.calls.last.request.headers["X-Idempotency-Key"] == "idem-1"


@pytest.mark.anyio
async def test_create_notice_omits_optional_fields(mock_api, ctx):
    route = mock_api.post("/notices").mock(
        return_value=httpx.Response(201, json={"id": "ntc_001"})
    )
    await create_notice(ctx, company="com_001", attachments=["file_001"])
    body = json.loads(route.calls.last.request.content)
    assert body == {"company": "com_001", "attachments": ["file_001"]}
    assert "description" not in body
    assert "X-Idempotency-Key" not in route.calls.last.request.headers
