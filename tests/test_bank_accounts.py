"""Tests for bank account tools."""

from __future__ import annotations

import httpx
import pytest

from mcp_server_check.tools.bank_accounts import (
    create_bank_account,
    delete_bank_account,
    list_bank_accounts,
    reveal_bank_account_number,
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


@pytest.mark.anyio
async def test_reveal_bank_account_number(mock_api, ctx):
    mock_api.get("/bank_accounts/bnk_001/reveal").mock(
        return_value=httpx.Response(200, json={"raw_account_number": "123456789"})
    )
    result = await reveal_bank_account_number(ctx, bank_account_id="bnk_001")
    assert result["raw_account_number"] == "123456789"
