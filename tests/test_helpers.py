"""Tests for HTTP helpers."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.helpers import (
    check_api_delete,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
    check_api_put,
)


@pytest.mark.anyio
async def test_check_api_get(mock_api, ctx):
    mock_api.get("/test").mock(return_value=httpx.Response(200, json={"id": "t_1"}))
    result = await check_api_get(ctx, "/test")
    assert result == {"id": "t_1"}


@pytest.mark.anyio
async def test_check_api_get_with_params(mock_api, ctx):
    route = mock_api.get("/test").mock(
        return_value=httpx.Response(200, json={"id": "t_1"})
    )
    await check_api_get(ctx, "/test", params={"limit": 5})
    assert "limit=5" in str(route.calls[0].request.url)


@pytest.mark.anyio
async def test_check_api_post(mock_api, ctx):
    mock_api.post("/test").mock(return_value=httpx.Response(201, json={"id": "t_new"}))
    result = await check_api_post(ctx, "/test", data={"name": "foo"})
    assert result == {"id": "t_new"}


@pytest.mark.anyio
async def test_check_api_patch(mock_api, ctx):
    mock_api.patch("/test/t_1").mock(
        return_value=httpx.Response(200, json={"id": "t_1", "name": "updated"})
    )
    result = await check_api_patch(ctx, "/test/t_1", data={"name": "updated"})
    assert result["name"] == "updated"


@pytest.mark.anyio
async def test_check_api_put(mock_api, ctx):
    mock_api.put("/test/t_1").mock(
        return_value=httpx.Response(200, json={"id": "t_1", "name": "replaced"})
    )
    result = await check_api_put(ctx, "/test/t_1", data={"name": "replaced"})
    assert result["name"] == "replaced"


@pytest.mark.anyio
async def test_check_api_delete(mock_api, ctx):
    mock_api.delete("/test/t_1").mock(return_value=httpx.Response(204))
    result = await check_api_delete(ctx, "/test/t_1")
    assert result == {"success": True}


@pytest.mark.anyio
async def test_check_api_delete_with_body(mock_api, ctx):
    mock_api.delete("/test/t_1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    result = await check_api_delete(ctx, "/test/t_1")
    assert result == {"deleted": True}


@pytest.mark.anyio
async def test_check_api_list(mock_api, ctx):
    mock_api.get("/items").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": "https://sandbox.checkhq.com/items?cursor=c2",
                "previous": None,
                "results": [{"id": "i_1"}],
            },
        )
    )
    result = await check_api_list(ctx, "/items")
    assert result["results"] == [{"id": "i_1"}]
    assert result["next_cursor"] == "c2"
    assert result["previous_cursor"] is None


@pytest.mark.anyio
async def test_http_error_returns_error_dict(mock_api, ctx):
    mock_api.get("/bad").mock(
        return_value=httpx.Response(422, json={"detail": "Validation error"})
    )
    result = await check_api_get(ctx, "/bad")
    assert result["error"] is True
    assert result["status_code"] == 422
    assert result["detail"] == {"detail": "Validation error"}


@pytest.mark.anyio
async def test_http_error_with_text_body(mock_api, ctx):
    mock_api.get("/bad").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    result = await check_api_get(ctx, "/bad")
    assert result["error"] is True
    assert result["status_code"] == 500
