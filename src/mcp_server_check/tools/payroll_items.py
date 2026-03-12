"""Payroll item tools for the Check API."""

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


async def list_payroll_items(
    ctx: Ctx,
    company: str | None = None,
    employee: str | None = None,
    payroll: str | None = None,
    limit: int | None = None,
    ids: list[str] | None = None,
    cursor: str | None = None,
) -> dict:
    """List payroll items, optionally filtered by company, employee, or payroll.

    Args:
        company: Filter to payroll items belonging to this Check company ID (e.g. "com_xxxxx").
        employee: Filter to payroll items for this Check employee ID (e.g. "emp_xxxxx").
        payroll: Filter to payroll items for this Check payroll ID (e.g. "prl_xxxxx").
        limit: Maximum number of results to return (default 10, max 100).
        ids: Filter to specific payroll item IDs.
        cursor: Pagination cursor from a previous response.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if employee is not None:
        params["employee"] = employee
    if payroll is not None:
        params["payroll"] = payroll
    if limit is not None:
        params["limit"] = limit
    if ids:
        params["ids"] = ",".join(ids)
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/payroll_items", params=params or None)


async def get_payroll_item(ctx: Ctx, payroll_item_id: str) -> dict:
    """Get details for a specific payroll item.

    Args:
        payroll_item_id: The Check payroll item ID.
    """
    return await check_api_get(ctx, f"/payroll_items/{payroll_item_id}")


async def create_payroll_item(
    ctx: Ctx,
    payroll: str,
    employee: str,
    payment_method: str | None = None,
    earnings: list[dict] | None = None,
    reimbursements: list[dict] | None = None,
) -> dict:
    """Create a new payroll item.

    Args:
        payroll: The Check payroll ID.
        employee: The Check employee ID.
        payment_method: Payment method — "direct_deposit" or "manual".
        earnings: List of earning dicts. Each requires "workplace" and may include
            "type", "earning_code", "description", "earning_rate", "amount", "hours",
            "piece_units", "metadata".
        reimbursements: List of reimbursement dicts. Each requires "amount" and may
            include "description", "code", "metadata".
    """
    body: dict = {"payroll": payroll, "employee": employee}
    if payment_method is not None:
        body["payment_method"] = payment_method
    if earnings is not None:
        body["earnings"] = earnings
    if reimbursements is not None:
        body["reimbursements"] = reimbursements
    return await check_api_post(ctx, "/payroll_items", data=body)


async def update_payroll_item(
    ctx: Ctx,
    payroll_item_id: str,
    payment_method: str | None = None,
    earnings: list[dict] | None = None,
    reimbursements: list[dict] | None = None,
    benefit_overrides: list[dict] | None = None,
    post_tax_deduction_overrides: list[dict] | None = None,
    pto_balance_hours: float | None = None,
    sick_balance_hours: float | None = None,
    supplemental_tax_calc_method: str | None = None,
    paper_check_number: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Update an existing payroll item.

    Args:
        payroll_item_id: The Check payroll item ID.
        payment_method: Payment method — "direct_deposit" or "manual".
        earnings: List of earning dicts (see create_payroll_item for shape).
        reimbursements: List of reimbursement dicts (see create_payroll_item for shape).
        benefit_overrides: List of benefit override dicts. Each requires "benefit" and
            may include "employee_contribution_amount", "company_contribution_amount".
        post_tax_deduction_overrides: List of post-tax deduction override dicts. Each
            requires "post_tax_deduction" and "amount".
        pto_balance_hours: Employee's remaining PTO hour balance for paystub display.
        sick_balance_hours: Employee's remaining sick hour balance for paystub display.
        supplemental_tax_calc_method: Tax calculation method — "flat" or "aggregate".
        paper_check_number: Check number for printed checks.
        metadata: Additional JSON metadata string.
    """
    body: dict = {}
    if payment_method is not None:
        body["payment_method"] = payment_method
    if earnings is not None:
        body["earnings"] = earnings
    if reimbursements is not None:
        body["reimbursements"] = reimbursements
    if benefit_overrides is not None:
        body["benefit_overrides"] = benefit_overrides
    if post_tax_deduction_overrides is not None:
        body["post_tax_deduction_overrides"] = post_tax_deduction_overrides
    if pto_balance_hours is not None:
        body["pto_balance_hours"] = pto_balance_hours
    if sick_balance_hours is not None:
        body["sick_balance_hours"] = sick_balance_hours
    if supplemental_tax_calc_method is not None:
        body["supplemental_tax_calc_method"] = supplemental_tax_calc_method
    if paper_check_number is not None:
        body["paper_check_number"] = paper_check_number
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_patch(ctx, f"/payroll_items/{payroll_item_id}", data=body)


async def bulk_update_payroll_items(ctx: Ctx, data: dict) -> dict:
    """Bulk update payroll items.

    The payload is a complex bulk structure — pass the full request body as a dict.

    Args:
        data: Bulk update payload with items array.
    """
    return await check_api_patch(ctx, "/payroll_items", data=data)


async def delete_payroll_item(ctx: Ctx, payroll_item_id: str) -> dict:
    """Delete a payroll item.

    Args:
        payroll_item_id: The Check payroll item ID.
    """
    return await check_api_delete(ctx, f"/payroll_items/{payroll_item_id}")


async def bulk_delete_payroll_items(
    ctx: Ctx, ids: list[str]
) -> dict:
    """Bulk delete payroll items.

    Args:
        ids: List of payroll item IDs to delete.
    """
    params = {"ids": ",".join(ids)}
    return await check_api_delete(ctx, "/payroll_items", params=params)


async def get_payroll_item_paper_check(ctx: Ctx, payroll_item_id: str) -> dict:
    """Get paper check details for a payroll item.

    Args:
        payroll_item_id: The Check payroll item ID.
    """
    return await check_api_get(ctx, f"/payroll_items/{payroll_item_id}/paper_check")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_payroll_items)
    mcp.add_tool(get_payroll_item)
    mcp.add_tool(get_payroll_item_paper_check)
    if not read_only:
        mcp.add_tool(create_payroll_item)
        mcp.add_tool(update_payroll_item)
        mcp.add_tool(bulk_update_payroll_items)
        mcp.add_tool(delete_payroll_item)
        mcp.add_tool(bulk_delete_payroll_items)
