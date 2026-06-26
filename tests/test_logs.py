"""Tests for log tools."""

from __future__ import annotations

import httpx
import pytest
from mcp_server_check.tools.logs import get_log, list_logs

BASE_URL = "https://sandbox.checkhq.com"


def _log(**overrides):
    log = {
        "id": "log_1",
        "method": "POST",
        "path": "/payrolls",
        "status_code": 400,
        "created_at": "2026-06-01T00:00:00Z",
        "processing_duration": 42,
        "request_body": {"foo": "bar"},
        "response_body": {"error": "bad"},
        "headers": {"Content-Type": "application/json"},
    }
    log.update(overrides)
    return log


@pytest.mark.anyio
async def test_list_logs_summarizes_results(mock_api, ctx):
    mock_api.get("/logs").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [_log()]},
        )
    )
    result = await list_logs(ctx)
    assert result["result_count"] == 1
    row = result["results"][0]
    assert row["id"] == "log_1"
    assert row["status_code"] == 400
    # The list view stays compact — bodies/headers are only on get_log.
    assert "request_body" not in row
    assert "headers" not in row


@pytest.mark.anyio
async def test_list_logs_status_class_filter(mock_api, ctx):
    route = mock_api.get("/logs").mock(
        return_value=httpx.Response(
            200, json={"next": None, "previous": None, "results": []}
        )
    )
    await list_logs(ctx, status_code=["4xx", "500"])
    assert route.calls[0].request.url.params["status_code"] == "4xx,500"


@pytest.mark.anyio
async def test_list_logs_multi_method_and_time_range(mock_api, ctx):
    route = mock_api.get("/logs").mock(
        return_value=httpx.Response(
            200, json={"next": None, "previous": None, "results": []}
        )
    )
    await list_logs(
        ctx,
        method=["GET", "POST"],
        path="/payrolls",
        created_after="2026-06-01T00:00:00Z",
        created_before="2026-06-02T00:00:00Z",
        idempotency_key="idem-1",
        limit=100,
    )
    params = route.calls[0].request.url.params
    assert params["method"] == "GET,POST"
    assert params["path"] == "/payrolls"
    assert params["created_after"] == "2026-06-01T00:00:00Z"
    assert params["created_before"] == "2026-06-02T00:00:00Z"
    assert params["idempotency_key"] == "idem-1"
    assert params["limit"] == "100"


@pytest.mark.anyio
async def test_get_log_returns_full_record(mock_api, ctx):
    mock_api.get("/logs/log_1").mock(return_value=httpx.Response(200, json=_log()))
    result = await get_log(ctx, log_id="log_1")
    assert result["id"] == "log_1"
    # get_log is not summarized — full record incl. bodies/headers.
    assert result["request_body"] == {"foo": "bar"}
    assert result["headers"] == {"Content-Type": "application/json"}
