"""Tests for form tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.forms import list_forms


@pytest.mark.anyio
async def test_list_forms_with_filters(mock_api, ctx):
    mock_api.get("/forms").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "frm_001"}]},
        )
    )
    result = await list_forms(
        ctx, company="com_123", state="CA", lang="en", type="contractor_setup"
    )
    assert result["results"] == [{"id": "frm_001"}]
    req = mock_api.get("/forms").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["state"] == "CA"
    assert req.url.params["lang"] == "en"
    assert req.url.params["type"] == "contractor_setup"
