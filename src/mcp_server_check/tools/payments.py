"""Payment tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
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
    parent_id: list[str] | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List payments with optional filters.

    Args:
        company: Filter to payments belonging to this Check company ID (e.g. "com_xxxxx").
        payroll: Filter by payroll ID (e.g. "pay_xxxxx").
        payroll_item: Filter by payroll item ID (e.g. "itm_xxxxx").
        contractor_payment: Filter by contractor payment ID (e.g. "cpa_xxxxx").
        direction: Filter by payment direction: "credit" or "debit".
        amount_min: Minimum payment amount (payments where amount >= this value).
        amount_max: Maximum payment amount (payments where amount <= this value).
        type: Filter by payment type: "company_cash_requirement", "employee_net_pay", "net_pay_refund", "collection", or "refund".
        completion_date_after: Filter to payments with completion date on or after this date (YYYY-MM-DD).
        completion_date_before: Filter to payments with completion date on or before this date (YYYY-MM-DD).
        parent_id: Filter to payments whose parent_id matches (e.g. "pay_xxxxx",
            "itm_xxxxx", "cpa_xxxxx", or "cor_xxxxx" for correction parents when
            your account has the corrections API). Multiple values are OR'd (max
            100 per request).
        limit: Maximum number of results to return (default 25, max 100).
        cursor: Pagination cursor.
    """
    return await check_api_list(
        ctx,
        "/payments",
        params=build_params(
            company=company,
            payroll=payroll,
            payroll_item=payroll_item,
            contractor_payment=contractor_payment,
            direction=direction,
            amount_min=amount_min,
            amount_max=amount_max,
            type=type,
            completion_date_after=completion_date_after,
            completion_date_before=completion_date_before,
            parent_id=parent_id,
            limit=limit,
            cursor=cursor,
        ),
    )


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
    return await check_api_list(
        ctx,
        "/payment_attempts",
        params=build_params(payment=payment_id, limit=limit, cursor=cursor),
    )


async def retry_payment(
    ctx: Ctx,
    payment_id: str,
    bank_account: str | None = None,
    payment_type: str | None = None,
) -> dict:
    """Retry a failed payment.

    A failed credit to an employee or contractor can only be retried to a
    different bank account: add one for the worker (create_bank_account),
    then pass it as bank_account. Retrying without it fails with "Cannot retry
    a failed credit payment without a new bank account." A failed funding
    debit can be retried as is, or as a wire with payment_type "wire" (not
    together with bank_account).

    Args:
        payment_id: The Check payment ID (e.g. "pyt_xxxxx").
        bank_account: Bank account ID (e.g. "bnk_xxxxx") to send the retry to.
            Required for a failed credit; must belong to the same worker.
        payment_type: Rail for the retry: "ach", "instant", or "wire".
    """
    return await check_api_post(
        ctx,
        f"/payments/{payment_id}/retry",
        data=build_body({}, bank_account=bank_account, payment_type=payment_type)
        or None,
    )


async def refund_payment(ctx: Ctx, payment_id: str) -> dict:
    """Refund a payment.

    Args:
        payment_id: The Check payment ID.
    """
    return await check_api_post(ctx, f"/payments/{payment_id}/refund")


# --- Sandbox simulation ---


async def simulate_complete_payment(ctx: Ctx, payment_id: str) -> dict:
    """Simulate one payment settling (sandbox only).

    Settles a single pending employee, contractor, or funding payment on a
    payroll whose simulation_mode is "manual", leaving the payroll's other
    payments untouched. The payment must be pending. Returns
    ``{"success": true}``; read the payment back with get_payment.

    Args:
        payment_id: The Check payment ID (e.g. "pyt_xxxxx"). Find a worker's
            credit with list_payments: the one whose parent is their payroll
            item or contractor payment.
    """
    return await check_api_post(ctx, f"/payments/{payment_id}/simulate/complete")


async def simulate_fail_payment(ctx: Ctx, payment_id: str) -> dict:
    """Simulate one payment failing (sandbox only).

    Fails a single pending payment on a payroll whose simulation_mode is
    "manual": the payment and its payroll item or contractor payment move to
    "failed" with ``can_retry`` true, and the payroll becomes "partially_paid"
    once its other payments settle. This is the explicit replacement for the
    "Barry BadAccount" sentinel. Returns ``{"success": true}``. To retry, add
    a new bank account for the worker and call retry_payment with it.

    Args:
        payment_id: The Check payment ID (e.g. "pyt_xxxxx").
    """
    return await check_api_post(ctx, f"/payments/{payment_id}/simulate/fail")


async def cancel_payment(ctx: Ctx, payment_id: str) -> dict:
    """Cancel a payment.

    Args:
        payment_id: The Check payment ID.
    """
    return await check_api_post(ctx, f"/payments/{payment_id}/cancel")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_payments)
    add_annotated_tool(mcp, get_payment)
    add_annotated_tool(mcp, list_payment_attempts)
    if not read_only:
        add_annotated_tool(mcp, retry_payment)
        add_annotated_tool(mcp, refund_payment)
        add_annotated_tool(mcp, cancel_payment)
        add_annotated_tool(mcp, simulate_complete_payment)
        add_annotated_tool(mcp, simulate_fail_payment)
