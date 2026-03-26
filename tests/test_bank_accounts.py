"""Tests for bank account tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.bank_accounts import (
    create_bank_account,
    delete_bank_account,
    list_bank_accounts,
)


@pytest.mark.anyio
async def test_list_bank_accounts(mock_api, ctx):
    mock_api.get("/bank_accounts").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "bnk_001"}]},
        )
    )
    result = await list_bank_accounts(ctx)
    assert result["results"] == [{"id": "bnk_001"}]


@pytest.mark.anyio
async def test_list_bank_accounts_with_filters(mock_api, ctx):
    mock_api.get("/bank_accounts").mock(
        return_value=httpx.Response(
            200,
            json={"next": None, "previous": None, "results": [{"id": "bnk_001"}]},
        )
    )
    result = await list_bank_accounts(
        ctx, company="com_123", employee="emp_456", contractor="ctr_789"
    )
    assert result["results"] == [{"id": "bnk_001"}]
    req = mock_api.get("/bank_accounts").calls.last.request
    assert req.url.params["company"] == "com_123"
    assert req.url.params["employee"] == "emp_456"
    assert req.url.params["contractor"] == "ctr_789"


@pytest.mark.anyio
async def test_create_bank_account(mock_api, ctx):
    mock_api.post("/bank_accounts").mock(
        return_value=httpx.Response(201, json={"id": "bnk_new"})
    )
    result = await create_bank_account(
        ctx,
        raw_bank_account={
            "routing_number": "021000021",
            "account_number": "123456789",
            "subtype": "checking",
        },
    )
    assert result["id"] == "bnk_new"


@pytest.mark.anyio
async def test_delete_bank_account(mock_api, ctx):
    mock_api.delete("/bank_accounts/bnk_001").mock(return_value=httpx.Response(204))
    result = await delete_bank_account(ctx, bank_account_id="bnk_001")
    assert result == {"success": True}
