"""External payroll tools for the Check API."""

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


async def list_external_payrolls(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    ids: list[str] | None = None,
    cursor: str | None = None,
) -> dict:
    """List external payrolls, optionally filtered by company.

    Args:
        company: Filter to external payrolls belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return (default 10, max 100).
        ids: Filter to specific external payroll IDs.
        cursor: Pagination cursor from a previous response.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if limit is not None:
        params["limit"] = limit
    if ids:
        params["ids"] = ",".join(ids)
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/external_payrolls", params=params or None)


async def get_external_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Get details for a specific external payroll.

    Args:
        payroll_id: The Check external payroll ID.
    """
    return await check_api_get(ctx, f"/external_payrolls/{payroll_id}")


async def create_external_payroll(
    ctx: Ctx,
    company: str,
    period_start: str,
    period_end: str,
    payday: str,
    pay_frequency: str | None = None,
    items: list[dict] | None = None,
    contractor_payments: list[dict] | None = None,
) -> dict:
    """Create a new external payroll.

    Args:
        company: The Check company ID.
        period_start: Pay period start date (YYYY-MM-DD).
        period_end: Pay period end date (YYYY-MM-DD).
        payday: Payday date (YYYY-MM-DD).
        pay_frequency: Frequency at which the external payroll was paid.
        items: List of external payroll item dicts. Each may include "employee",
            "earnings" (list), "reimbursements" (list), "taxes" (list),
            "benefits" (list), "post_tax_deductions" (list).
        contractor_payments: List of contractor payment dicts. Each may include
            "contractor", "amount", "reimbursement_amount".
    """
    body: dict = {
        "company": company,
        "period_start": period_start,
        "period_end": period_end,
        "payday": payday,
    }
    if pay_frequency is not None:
        body["pay_frequency"] = pay_frequency
    if items is not None:
        body["items"] = items
    if contractor_payments is not None:
        body["contractor_payments"] = contractor_payments
    return await check_api_post(ctx, "/external_payrolls", data=body)


async def update_external_payroll(
    ctx: Ctx,
    payroll_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
    payday: str | None = None,
    pay_frequency: str | None = None,
    items: list[dict] | None = None,
    contractor_payments: list[dict] | None = None,
) -> dict:
    """Update an existing external payroll.

    Args:
        payroll_id: The Check external payroll ID.
        period_start: Pay period start date (YYYY-MM-DD).
        period_end: Pay period end date (YYYY-MM-DD).
        payday: Payday date (YYYY-MM-DD).
        pay_frequency: Frequency at which the external payroll was paid.
        items: List of external payroll item dicts (see create_external_payroll).
        contractor_payments: List of contractor payment dicts (see create_external_payroll).
    """
    body: dict = {}
    if period_start is not None:
        body["period_start"] = period_start
    if period_end is not None:
        body["period_end"] = period_end
    if payday is not None:
        body["payday"] = payday
    if pay_frequency is not None:
        body["pay_frequency"] = pay_frequency
    if items is not None:
        body["items"] = items
    if contractor_payments is not None:
        body["contractor_payments"] = contractor_payments
    return await check_api_patch(ctx, f"/external_payrolls/{payroll_id}", data=body)


async def delete_external_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Delete an external payroll.

    Args:
        payroll_id: The Check external payroll ID.
    """
    return await check_api_delete(ctx, f"/external_payrolls/{payroll_id}")


async def approve_external_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Approve an external payroll.

    Args:
        payroll_id: The Check external payroll ID.
    """
    return await check_api_post(ctx, f"/external_payrolls/{payroll_id}/approve")


async def reopen_external_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Reopen an external payroll.

    Args:
        payroll_id: The Check external payroll ID.
    """
    return await check_api_post(ctx, f"/external_payrolls/{payroll_id}/reopen")


async def preview_external_payroll(ctx: Ctx, external_payroll_id: str) -> dict:
    """Preview an external payroll.

    Args:
        external_payroll_id: The Check external payroll ID.
    """
    return await check_api_get(ctx, f"/external_payrolls/{external_payroll_id}/preview")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_external_payrolls)
    mcp.add_tool(get_external_payroll)
    mcp.add_tool(preview_external_payroll)
    if not read_only:
        mcp.add_tool(create_external_payroll)
        mcp.add_tool(update_external_payroll)
        mcp.add_tool(delete_external_payroll)
        mcp.add_tool(approve_external_payroll)
        mcp.add_tool(reopen_external_payroll)
