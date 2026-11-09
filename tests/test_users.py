"""Tests for user tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.users import get_user, list_users


@pytest.mark.anyio
async def test_list_users(mock_api, ctx):
    route = mock_api.get("/users").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [{"id": "usr_001", "status": "active"}],
            },
        )
    )
    result = await list_users(ctx, limit=10, cursor="abc")
    assert result["results"] == [{"id": "usr_001", "status": "active"}]
    params = route.calls.last.request.url.params
    assert params["limit"] == "10"
    assert params["cursor"] == "abc"


@pytest.mark.anyio
async def test_get_user(mock_api, ctx):
    mock_api.get("/users/usr_001").mock(
        return_value=httpx.Response(200, json={"id": "usr_001", "status": "inactive"})
    )
    result = await get_user(ctx, "usr_001")
    assert result["status"] == "inactive"


@pytest.mark.anyio
async def test_get_user_not_found(mock_api, ctx):
    mock_api.get("/users/usr_missing").mock(
        return_value=httpx.Response(
            404, json={"error": {"type": "not_found", "message": "Not found."}}
        )
    )
    result = await get_user(ctx, "usr_missing")
    assert result["error"] is True
    assert result["status_code"] == 404
