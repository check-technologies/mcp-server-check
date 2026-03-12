"""Payroll tools for the Check API."""

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


async def list_payrolls(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    ids: list[str] | None = None,
    cursor: str | None = None,
) -> dict:
    """List payrolls, optionally filtered by company.

    Args:
        company: Filter to payrolls belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return (default 10, max 100).
        ids: Filter to specific payroll IDs.
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
    return await check_api_list(ctx, "/payrolls", params=params or None)


async def get_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Get details for a specific payroll.

    Args:
        payroll_id: The Check payroll ID (e.g. "prl_xxxxx").
    """
    return await check_api_get(ctx, f"/payrolls/{payroll_id}")


async def create_payroll(
    ctx: Ctx,
    company: str,
    period_start: str,
    period_end: str,
    payday: str,
    type: str | None = None,
    processing_period: str | None = None,
    pay_frequency: str | None = None,
    funding_payment_method: str | None = None,
    pay_schedule: str | None = None,
    off_cycle_options: dict | None = None,
    items: list[dict] | None = None,
    contractor_payments: list[dict] | None = None,
    metadata: str | None = None,
    bank_account: str | None = None,
) -> dict:
    """Create a new payroll.

    Args:
        company: The Check company ID.
        period_start: Pay period start date (YYYY-MM-DD).
        period_end: Pay period end date (YYYY-MM-DD).
        payday: Payday date (YYYY-MM-DD).
        type: Payroll type — "regular", "off_cycle", or "amendment". Default: "regular".
        processing_period: Processing period — "three_day", "two_day", or "one_day".
        pay_frequency: Pay frequency — "weekly", "biweekly", "semimonthly", "monthly",
            "quarterly", or "annually". Default: "biweekly".
        funding_payment_method: Funding method — "ach" or "wire". Default: "ach".
        pay_schedule: ID of the pay schedule this payroll relates to.
        off_cycle_options: Off-cycle config dict with keys: force_supplemental_withholding
            (bool), apply_benefits (bool), apply_post_tax_deductions (bool).
        items: List of payroll item dicts. Each requires "employee" and may include
            "payment_method", "earnings" (list), "reimbursements" (list),
            "benefit_overrides" (list), "post_tax_deduction_overrides" (list),
            "pto_balance_hours", "sick_balance_hours", "metadata".
        contractor_payments: List of contractor payment dicts. Each requires "contractor"
            and may include "payment_method", "amount", "reimbursement_amount",
            "workplace", "paper_check_number".
        metadata: Additional JSON metadata string.
        bank_account: ID of the bank account to fund the payroll.
    """
    body: dict = {
        "company": company,
        "period_start": period_start,
        "period_end": period_end,
        "payday": payday,
    }
    if type is not None:
        body["type"] = type
    if processing_period is not None:
        body["processing_period"] = processing_period
    if pay_frequency is not None:
        body["pay_frequency"] = pay_frequency
    if funding_payment_method is not None:
        body["funding_payment_method"] = funding_payment_method
    if pay_schedule is not None:
        body["pay_schedule"] = pay_schedule
    if off_cycle_options is not None:
        body["off_cycle_options"] = off_cycle_options
    if items is not None:
        body["items"] = items
    if contractor_payments is not None:
        body["contractor_payments"] = contractor_payments
    if metadata is not None:
        body["metadata"] = metadata
    if bank_account is not None:
        body["bank_account"] = bank_account
    return await check_api_post(ctx, "/payrolls", data=body)


async def update_payroll(
    ctx: Ctx,
    payroll_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
    payday: str | None = None,
    type: str | None = None,
    processing_period: str | None = None,
    pay_frequency: str | None = None,
    funding_payment_method: str | None = None,
    pay_schedule: str | None = None,
    off_cycle_options: dict | None = None,
    items: list[dict] | None = None,
    contractor_payments: list[dict] | None = None,
    metadata: str | None = None,
    bank_account: str | None = None,
) -> dict:
    """Update an existing payroll.

    Args:
        payroll_id: The Check payroll ID.
        period_start: Pay period start date (YYYY-MM-DD).
        period_end: Pay period end date (YYYY-MM-DD).
        payday: Payday date (YYYY-MM-DD).
        type: Payroll type — "regular", "off_cycle", or "amendment".
        processing_period: Processing period — "three_day", "two_day", or "one_day".
        pay_frequency: Pay frequency — "weekly", "biweekly", "semimonthly", "monthly",
            "quarterly", or "annually".
        funding_payment_method: Funding method — "ach" or "wire".
        pay_schedule: ID of the pay schedule this payroll relates to.
        off_cycle_options: Off-cycle config dict with keys: force_supplemental_withholding
            (bool), apply_benefits (bool), apply_post_tax_deductions (bool).
        items: List of payroll item dicts (see create_payroll for shape).
        contractor_payments: List of contractor payment dicts (see create_payroll for shape).
        metadata: Additional JSON metadata string.
        bank_account: ID of the bank account to fund the payroll.
    """
    body: dict = {}
    if period_start is not None:
        body["period_start"] = period_start
    if period_end is not None:
        body["period_end"] = period_end
    if payday is not None:
        body["payday"] = payday
    if type is not None:
        body["type"] = type
    if processing_period is not None:
        body["processing_period"] = processing_period
    if pay_frequency is not None:
        body["pay_frequency"] = pay_frequency
    if funding_payment_method is not None:
        body["funding_payment_method"] = funding_payment_method
    if pay_schedule is not None:
        body["pay_schedule"] = pay_schedule
    if off_cycle_options is not None:
        body["off_cycle_options"] = off_cycle_options
    if items is not None:
        body["items"] = items
    if contractor_payments is not None:
        body["contractor_payments"] = contractor_payments
    if metadata is not None:
        body["metadata"] = metadata
    if bank_account is not None:
        body["bank_account"] = bank_account
    return await check_api_patch(ctx, f"/payrolls/{payroll_id}", data=body)


async def delete_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Delete a payroll.

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_delete(ctx, f"/payrolls/{payroll_id}")


async def preview_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Preview a payroll before approval.

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_get(ctx, f"/payrolls/{payroll_id}/preview")


async def approve_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Approve a payroll for processing.

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_post(ctx, f"/payrolls/{payroll_id}/approve")


async def reopen_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Reopen a previously approved payroll.

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_post(ctx, f"/payrolls/{payroll_id}/reopen")


async def get_payroll_paper_checks(ctx: Ctx, payroll_id: str) -> dict:
    """Get paper checks for a payroll.

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_get(ctx, f"/payrolls/{payroll_id}/paper_checks")


async def get_payroll_cash_requirement_report(ctx: Ctx, payroll_id: str) -> dict:
    """Get a cash requirement report for a payroll.

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_get(
        ctx, f"/payrolls/{payroll_id}/reports/cash_requirement"
    )


async def get_payroll_paper_checks_report(ctx: Ctx, payroll_id: str) -> dict:
    """Get a paper checks report for a payroll.

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_get(
        ctx, f"/payrolls/{payroll_id}/reports/paper_checks"
    )


# --- Simulation ---


async def simulate_start_processing(ctx: Ctx, payroll_id: str) -> dict:
    """Simulate starting payroll processing (sandbox only).

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_post(
        ctx, f"/payrolls/{payroll_id}/simulate/start_processing"
    )


async def simulate_complete_funding(ctx: Ctx, payroll_id: str) -> dict:
    """Simulate completing payroll funding (sandbox only).

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_post(
        ctx, f"/payrolls/{payroll_id}/simulate/complete_funding"
    )


async def simulate_fail_funding(ctx: Ctx, payroll_id: str) -> dict:
    """Simulate failing payroll funding (sandbox only).

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_post(
        ctx, f"/payrolls/{payroll_id}/simulate/fail_funding"
    )


async def simulate_complete_disbursements(ctx: Ctx, payroll_id: str) -> dict:
    """Simulate completing payroll disbursements (sandbox only).

    Args:
        payroll_id: The Check payroll ID.
    """
    return await check_api_post(
        ctx, f"/payrolls/{payroll_id}/simulate/complete_disbursements"
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_payrolls)
    mcp.add_tool(get_payroll)
    mcp.add_tool(preview_payroll)
    mcp.add_tool(get_payroll_paper_checks)
    mcp.add_tool(get_payroll_cash_requirement_report)
    mcp.add_tool(get_payroll_paper_checks_report)
    if not read_only:
        mcp.add_tool(create_payroll)
        mcp.add_tool(update_payroll)
        mcp.add_tool(delete_payroll)
        mcp.add_tool(approve_payroll)
        mcp.add_tool(reopen_payroll)
        mcp.add_tool(simulate_start_processing)
        mcp.add_tool(simulate_complete_funding)
        mcp.add_tool(simulate_fail_funding)
        mcp.add_tool(simulate_complete_disbursements)
