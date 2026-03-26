"""Payment tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.helpers import (
    Ctx,
    check_api_get,
    check_api_list,
    check_api_post,
)


async def list_payments(
    ctx: Ctx,
    company: str | None = None,
    payroll: str | None = None,
    payroll_item: str | None = None,
    contractor_payment: str | None = None,
    direction: str | None = None,
    amount_min: str | None = None,
    amount_max: str | None = None,
    type: str | None = None,
    completion_date_after: str | None = None,
    completion_date_before: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List payments with optional filters.

    Args:
        company: Filter to payments belonging to this Check company ID (e.g. "com_xxxxx").
        payroll: Filter by payroll ID (e.g. "prl_xxxxx").
        payroll_item: Filter by payroll item ID (e.g. "pit_xxxxx").
        contractor_payment: Filter by contractor payment ID (e.g. "ctp_xxxxx").
        direction: Filter by payment direction: "credit" or "debit".
        amount_min: Minimum payment amount (payments where amount >= this value).
        amount_max: Maximum payment amount (payments where amount <= this value).
        type: Filter by payment type: "company_cash_requirement", "employee_net_pay", "net_pay_refund", "collection", or "refund".
        completion_date_after: Filter to payments with completion date on or after this date (YYYY-MM-DD).
        completion_date_before: Filter to payments with completion date on or before this date (YYYY-MM-DD).
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if payroll is not None:
        params["payroll"] = payroll
    if payroll_item is not None:
        params["payroll_item"] = payroll_item
    if contractor_payment is not None:
        params["contractor_payment"] = contractor_payment
    if direction is not None:
        params["direction"] = direction
    if amount_min is not None:
        params["amount_min"] = amount_min
    if amount_max is not None:
        params["amount_max"] = amount_max
    if type is not None:
        params["type"] = type
    if completion_date_after is not None:
        params["completion_date_after"] = completion_date_after
    if completion_date_before is not None:
        params["completion_date_before"] = completion_date_before
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
