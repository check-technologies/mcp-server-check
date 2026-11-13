"""Tests for file tools."""

from __future__ import annotations

import json

import httpx
import pytest

from mcp_server_check.tools.files import create_file, get_file


@pytest.mark.anyio
async def test_create_file(mock_api, ctx):
    route = mock_api.post("/files").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "file_001",
                "purpose": "notice",
                "status": "pending",
                "upload_url": "https://example.com/upload",
            },
        )
    )
    result = await create_file(
        ctx,
        company="com_001",
        purpose="notice",
        filename="letter.pdf",
        content_type="application/pdf",
        size=1000,
        idempotency_key="idem-1",
    )
    assert result["id"] == "file_001"
    assert json.loads(route.calls.last.request.content) == {
        "company": "com_001",
        "purpose": "notice",
        "filename": "letter.pdf",
        "content_type": "application/pdf",
        "size": 1000,
    }
    assert route.calls.last.request.headers["X-Idempotency-Key"] == "idem-1"


@pytest.mark.anyio
async def test_create_file_omits_idempotency_key_when_unset(mock_api, ctx):
    route = mock_api.post("/files").mock(
        return_value=httpx.Response(201, json={"id": "file_001"})
    )
    await create_file(
        ctx,
        company="com_001",
        purpose="notice",
        filename="letter.pdf",
        content_type="application/pdf",
        size=1000,
    )
    assert "X-Idempotency-Key" not in route.calls.last.request.headers


@pytest.mark.anyio
async def test_get_file(mock_api, ctx):
    mock_api.get("/files/file_001").mock(
        return_value=httpx.Response(200, json={"id": "file_001", "status": "ready"})
    )
    result = await get_file(ctx, file_id="file_001")
    assert result["status"] == "ready"
