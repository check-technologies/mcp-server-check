"""Payment tools for the Check API."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server_check.helpers import (
    Ctx,
    check_api_get,
    check_api_list,
    check_api_post,
)


async def list_payments(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List payments, optionally filtered by company.

    Args:
        company: Filter to payments belonging to this Check company ID (e.g. "com_xxxxx").
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
    return await check_api_list(ctx, "/payments", params=params or None)


async def get_payment(ctx: Ctx, payment_id: str) -> dict:
    """Get details for a specific payment.

    Args:
        payment_id: The Check payment ID.
    """
    return await check_api_get(ctx, f"/payments/{payment_id}")


async def list_payment_attempts(
    ctx: Ctx,
    payment_id: str,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List payment attempts for a payment.

    Args:
        payment_id: The Check payment ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(
        ctx, f"/payments/{payment_id}/payment_attempts", params=params or None
    )


async def retry_payment(ctx: Ctx, payment_id: str) -> dict:
    """Retry a failed payment.

    Args:
        payment_id: The Check payment ID.
    """
    return await check_api_post(ctx, f"/payments/{payment_id}/retry")


async def refund_payment(ctx: Ctx, payment_id: str) -> dict:
    """Refund a payment.

    Args:
        payment_id: The Check payment ID.
    """
    return await check_api_post(ctx, f"/payments/{payment_id}/refund")


async def cancel_payment(ctx: Ctx, payment_id: str) -> dict:
    """Cancel a payment.

    Args:
        payment_id: The Check payment ID.
    """
    return await check_api_post(ctx, f"/payments/{payment_id}/cancel")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_payments)
    mcp.add_tool(get_payment)
    mcp.add_tool(list_payment_attempts)
    if not read_only:
        mcp.add_tool(retry_payment)
        mcp.add_tool(refund_payment)
        mcp.add_tool(cancel_payment)
