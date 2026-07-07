"""Tests for agency tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.agencies import get_agency, list_agencies


@pytest.mark.anyio
async def test_list_agencies(mock_api, ctx):
    mock_api.get("/agencies").mock(
        return_value=httpx.Response(
            200,
            json={
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": "agc_001",
                        "label": "Internal Revenue Service",
                        "jurisdiction": "fed",
                    }
                ],
            },
        )
    )
    result = await list_agencies(ctx)
    assert result["result_count"] == 1
    assert result["results"][0]["id"] == "agc_001"
    assert result["results"][0]["label"] == "Internal Revenue Service"


@pytest.mark.anyio
async def test_list_agencies_with_filters(mock_api, ctx):
    route = mock_api.get("/agencies").mock(
        return_value=httpx.Response(
            200, json={"next": None, "previous": None, "results": []}
        )
    )
    await list_agencies(
        ctx,
        ids=["agc_001", "agc_002"],
        jurisdiction=["fed", "ny"],
        label_contains="revenue",
        limit=50,
    )
    params = route.calls[0].request.url.params
    # Multi-value filters are sent as repeated params, not comma-joined.
    assert params.get_list("id") == ["agc_001", "agc_002"]
    assert params.get_list("jurisdiction") == ["fed", "ny"]
    assert params["label_contains"] == "revenue"
    assert params["limit"] == "50"


@pytest.mark.anyio
async def test_get_agency(mock_api, ctx):
    mock_api.get("/agencies/agc_001").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "agc_001",
                "label": "Internal Revenue Service",
                "jurisdiction": "fed",
            },
        )
    )
    result = await get_agency(ctx, agency_id="agc_001")
    assert result["id"] == "agc_001"
    assert result["jurisdiction"] == "fed"
