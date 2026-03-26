"""Contractor payment tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.helpers import (
    Ctx,
    check_api_delete,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)


async def list_contractor_payments(
    ctx: Ctx,
    company: str | None = None,
    contractor: str | None = None,
    limit: int = 500,
    ids: list[str] | None = None,
    cursor: str | None = None,
    payroll: str | None = None,
) -> dict:
    """List contractor payments, optionally filtered by company or contractor.

    Args:
        company: Filter to contractor payments belonging to this Check company ID (e.g. "com_xxxxx").
        contractor: Filter to payments for this Check contractor ID (e.g. "ctr_xxxxx").
        limit: Maximum number of results to return (default 500, max 500).
        ids: Filter to specific contractor payment IDs.
        cursor: Pagination cursor from a previous response.
        payroll: Filter by payroll ID.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if contractor is not None:
        params["contractor"] = contractor
    params["limit"] = limit
    if ids:
        params["ids"] = ",".join(ids)
    if cursor:
        params["cursor"] = cursor
    if payroll is not None:
        params["payroll"] = payroll
    return await check_api_list(ctx, "/contractor_payments", params=params or None)


async def get_contractor_payment(ctx: Ctx, contractor_payment_id: str) -> dict:
    """Get details for a specific contractor payment.

    Args:
        contractor_payment_id: The Check contractor payment ID.
    """
    return await check_api_get(ctx, f"/contractor_payments/{contractor_payment_id}")


async def create_contractor_payment(
    ctx: Ctx,
    contractor: str,
    payroll: str,
    payment_method: str | None = None,
    amount: str | None = None,
    reimbursement_amount: str | None = None,
    workplace: str | None = None,
    metadata: str | None = None,
    paper_check_number: str | None = None,
) -> dict:
    """Create a new contractor payment.

    Args:
        contractor: The Check contractor ID.
        payroll: The Check payroll ID.
        payment_method: How the contractor will be paid — "direct_deposit" or "manual".
            Default: "direct_deposit".
        amount: The amount to pay the contractor (e.g. "1500.00"). Default: "0.00".
        reimbursement_amount: Reimbursement amount (e.g. "50.00"). Default: "0.00".
        workplace: Workplace ID associated with this payment.
        metadata: Additional JSON metadata string.
        paper_check_number: Check number for accounting on printed checks.
    """
    body: dict = {"contractor": contractor, "payroll": payroll}
    if payment_method is not None:
        body["payment_method"] = payment_method
    if amount is not None:
        body["amount"] = amount
    if reimbursement_amount is not None:
        body["reimbursement_amount"] = reimbursement_amount
    if workplace is not None:
        body["workplace"] = workplace
    if metadata is not None:
        body["metadata"] = metadata
    if paper_check_number is not None:
        body["paper_check_number"] = paper_check_number
    return await check_api_post(ctx, "/contractor_payments", data=body)


async def update_contractor_payment(
    ctx: Ctx,
    contractor_payment_id: str,
    contractor: str | None = None,
    payment_method: str | None = None,
    amount: str | None = None,
    reimbursement_amount: str | None = None,
    workplace: str | None = None,
    metadata: str | None = None,
    paper_check_number: str | None = None,
) -> dict:
    """Update an existing contractor payment.

    Args:
        contractor_payment_id: The Check contractor payment ID.
        contractor: The Check contractor ID.
        payment_method: How the contractor will be paid — "direct_deposit" or "manual".
        amount: The amount to pay the contractor (e.g. "1500.00").
        reimbursement_amount: Reimbursement amount (e.g. "50.00").
        workplace: Workplace ID associated with this payment.
        metadata: Additional JSON metadata string.
        paper_check_number: Check number for accounting on printed checks.
    """
    body: dict = {}
    if contractor is not None:
        body["contractor"] = contractor
    if payment_method is not None:
        body["payment_method"] = payment_method
    if amount is not None:
        body["amount"] = amount
    if reimbursement_amount is not None:
        body["reimbursement_amount"] = reimbursement_amount
    if workplace is not None:
        body["workplace"] = workplace
    if metadata is not None:
        body["metadata"] = metadata
    if paper_check_number is not None:
        body["paper_check_number"] = paper_check_number
    return await check_api_patch(
        ctx, f"/contractor_payments/{contractor_payment_id}", data=body
    )


async def delete_contractor_payment(ctx: Ctx, contractor_payment_id: str) -> dict:
    """Delete a contractor payment.

    Args:
        contractor_payment_id: The Check contractor payment ID.
    """
    return await check_api_delete(ctx, f"/contractor_payments/{contractor_payment_id}")


async def get_contractor_payment_paper_check(
    ctx: Ctx, contractor_payment_id: str
) -> dict:
    """Get paper check details for a contractor payment.

    Args:
        contractor_payment_id: The Check contractor payment ID.
    """
    return await check_api_get(
        ctx, f"/contractor_payments/{contractor_payment_id}/paper_check"
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_contractor_payments)
    mcp.add_tool(get_contractor_payment)
    mcp.add_tool(get_contractor_payment_paper_check)
    if not read_only:
        mcp.add_tool(create_contractor_payment)
        mcp.add_tool(update_contractor_payment)
        mcp.add_tool(delete_contractor_payment)
