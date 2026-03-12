"""Bank account tools for the Check API."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server_check.helpers import (
    Ctx,
    check_api_delete,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)


async def list_bank_accounts(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List bank accounts, optionally filtered by company.

    Args:
        company: Filter to bank accounts belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/bank_accounts", params=params or None)


async def get_bank_account(ctx: Ctx, bank_account_id: str) -> dict:
    """Get details for a specific bank account.

    Args:
        bank_account_id: The Check bank account ID.
    """
    return await check_api_get(ctx, f"/bank_accounts/{bank_account_id}")


async def create_bank_account(
    ctx: Ctx,
    raw_bank_account: dict | None = None,
    plaid_bank_account: dict | None = None,
    employee: str | None = None,
    company: str | None = None,
    contractor: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Create a new bank account.

    Provide either raw_bank_account or plaid_bank_account, plus exactly one of
    employee, company, or contractor to indicate who owns the account.

    Args:
        raw_bank_account: Bank account details dict with keys: account_number (required),
            routing_number (required), subtype (required — "checking" or "savings"),
            institution_name (optional).
        plaid_bank_account: Plaid token dict with key: plaid_processor_token (required).
        employee: ID of the employee who owns this account.
        company: ID of the company who owns this account.
        contractor: ID of the contractor who owns this account.
        metadata: Additional JSON metadata string.
    """
    body: dict = {}
    if raw_bank_account is not None:
        body["raw_bank_account"] = raw_bank_account
    if plaid_bank_account is not None:
        body["plaid_bank_account"] = plaid_bank_account
    if employee is not None:
        body["employee"] = employee
    if company is not None:
        body["company"] = company
    if contractor is not None:
        body["contractor"] = contractor
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_post(ctx, "/bank_accounts", data=body)


async def update_bank_account(
    ctx: Ctx,
    bank_account_id: str,
    raw_bank_account: dict | None = None,
    metadata: str | None = None,
) -> dict:
    """Update a bank account.

    Args:
        bank_account_id: The Check bank account ID.
        raw_bank_account: Bank account details dict with keys: account_number,
            routing_number, subtype ("checking" or "savings"), institution_name.
        metadata: Additional JSON metadata string.
    """
    body: dict = {}
    if raw_bank_account is not None:
        body["raw_bank_account"] = raw_bank_account
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_patch(ctx, f"/bank_accounts/{bank_account_id}", data=body)


async def delete_bank_account(ctx: Ctx, bank_account_id: str) -> dict:
    """Delete a bank account.

    Args:
        bank_account_id: The Check bank account ID.
    """
    return await check_api_delete(ctx, f"/bank_accounts/{bank_account_id}")


async def reveal_bank_account_number(ctx: Ctx, bank_account_id: str) -> dict:
    """Reveal the full account number for a bank account.

    Args:
        bank_account_id: The Check bank account ID.
    """
    return await check_api_get(ctx, f"/bank_accounts/{bank_account_id}/reveal")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_bank_accounts)
    mcp.add_tool(get_bank_account)
    mcp.add_tool(reveal_bank_account_number)
    if not read_only:
        mcp.add_tool(create_bank_account)
        mcp.add_tool(update_bank_account)
        mcp.add_tool(delete_bank_account)
