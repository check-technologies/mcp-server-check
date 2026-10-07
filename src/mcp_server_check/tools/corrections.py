"""Correction tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
    check_api_delete,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)
from mcp_server_check.types import VoidSubset


async def list_corrections(
    ctx: Ctx,
    company: str | None = None,
    year: int | None = None,
    status: str | None = None,
    payroll: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List corrections, optionally filtered by company, year, status, or payroll.

    Args:
        company: Filter to corrections for this Check company ID (e.g. "com_xxxxx").
        year: Filter to corrections for this tax year (e.g. 2026).
        status: Filter by status — "draft", "pending", "processing", "settled",
            or "failed".
        payroll: Filter to corrections that include this payroll ID (e.g. "pay_xxxxx").
        limit: Maximum number of results to return (default 25, max 100).
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/corrections",
        params=build_params(
            company=company,
            year=year,
            status=status,
            payroll=payroll,
            limit=limit,
            cursor=cursor,
        ),
    )


async def get_correction(ctx: Ctx, correction_id: str) -> dict:
    """Get a correction, including its operations, totals, and preview and approval state.

    Poll this after preview_correction or approve_correction: each runs in the
    background and reports progress on the correction's "preview" or "approval"
    object ("calculating", then "succeeded" or "failed" with an "error_code").

    Args:
        correction_id: The Check correction ID (e.g. "cor_xxxxx").
    """
    return await check_api_get(ctx, f"/corrections/{correction_id}")


async def create_correction(
    ctx: Ctx,
    company: str,
    year: int,
    settlement_date: str | None = None,
    bank_account: str | None = None,
    description: str | None = None,
    metadata: dict | None = None,
    simulation_mode: str | None = None,
) -> dict:
    """Create a draft correction for a company and tax year.

    A correction groups changes to a company's past payrolls: void payrolls with
    void_payroll, add missing managed payrolls with add_payroll_to_correction,
    add historical external payrolls with add_external_payroll, then price the result with preview_correction and commit it with
    approve_correction.

    Args:
        company: The Check company ID.
        year: The tax year the correction applies to. Every payroll added to the
            correction must have a payday in this year.
        settlement_date: Date money moves for the correction (YYYY-MM-DD). When
            omitted, a date is chosen at approval.
        bank_account: ID of the company bank account to debit or credit. Defaults
            to the company's default bank account.
        description: Free-text explanation of why the correction exists.
        metadata: Arbitrary key-value object stored on the correction.
        simulation_mode: Sandbox only. How money moves after approval — "automatic"
            (default) or "manual" (step with simulate_correction_* tools). Null
            omits the field and uses automatic.
    """
    return await check_api_post(
        ctx,
        "/corrections",
        data=build_body(
            {"company": company, "year": year},
            settlement_date=settlement_date,
            bank_account=bank_account,
            description=description,
            metadata=metadata,
            simulation_mode=simulation_mode,
        ),
    )


async def update_correction(
    ctx: Ctx,
    correction_id: str,
    settlement_date: str | None = None,
    bank_account: str | None = None,
    description: str | None = None,
    metadata: dict | None = None,
    simulation_mode: str | None = None,
) -> dict:
    """Update a draft correction's settlement date, bank account, description, metadata, or simulation mode.

    The payrolls in a correction can't be changed here; use void_payroll,
    add_payroll_to_correction, and add_external_payroll instead.

    Args:
        correction_id: The Check correction ID.
        settlement_date: Date money moves for the correction (YYYY-MM-DD).
        bank_account: ID of the company bank account to debit or credit.
        description: Free-text explanation of why the correction exists.
        metadata: Arbitrary key-value object stored on the correction.
        simulation_mode: Sandbox only. "automatic" or "manual". Settable while
            the correction is draft.
    """
    return await check_api_patch(
        ctx,
        f"/corrections/{correction_id}",
        data=build_body(
            {},
            settlement_date=settlement_date,
            bank_account=bank_account,
            description=description,
            metadata=metadata,
            simulation_mode=simulation_mode,
        ),
    )


async def delete_correction(ctx: Ctx, correction_id: str) -> dict:
    """Delete a draft correction.

    Args:
        correction_id: The Check correction ID.
    """
    return await check_api_delete(ctx, f"/corrections/{correction_id}")


async def void_payroll(
    ctx: Ctx,
    payroll_id: str,
    correction: str,
    subset: VoidSubset | None,
) -> dict:
    """Void a paid payroll, or part of it, as part of a draft correction.

    Creates a draft void payroll in the correction; nothing is voided until the
    correction is approved.

    Args:
        payroll_id: The Check payroll ID to void.
        correction: ID of the draft correction to add the void to (e.g. "cor_xxxxx").
            Its company and tax year must match the payroll's.
        subset: What to void. Required: pass null to void the entire payroll, or an
            object with "payroll_items" and/or "contractor_payments" lists of IDs
            to void only those.
    """
    return await check_api_post(
        ctx,
        f"/payrolls/{payroll_id}/void",
        data={"correction": correction, "subset": subset},
    )


async def add_payroll_to_correction(
    ctx: Ctx,
    correction: str,
    company: str,
    period_start: str,
    period_end: str,
    payday: str,
    pay_frequency: str | None = None,
    pay_schedule: str | None = None,
    items: list[dict] | None = None,
    contractor_payments: list[dict] | None = None,
    metadata: dict | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Add a new payroll to a draft correction, e.g. to replace a voided one or record a missed one.

    The payroll is created in draft and is approved along with the correction.
    Check API writes inline items only when the request carries
    ?include_items=true, and inline contractor_payments only with
    ?include_contractor_payments=true; this tool adds whichever parameter applies
    when you pass items or contractor_payments.

    Args:
        correction: ID of the draft correction to add the payroll to (e.g. "cor_xxxxx").
        company: The Check company ID. Must match the correction's company.
        period_start: Pay period start date (YYYY-MM-DD).
        period_end: Pay period end date (YYYY-MM-DD).
        payday: Payday date (YYYY-MM-DD). Must be in the past, in the correction's
            tax year, and in the company's open quarter.
        pay_frequency: Pay frequency — "weekly", "biweekly", "semimonthly", "monthly",
            "quarterly", or "annually".
        pay_schedule: ID of the pay schedule this payroll relates to.
        items: List of payroll item dicts (see create_payroll for shape). Each must
            use "payment_method": "manual". When set, the tool sends
            ?include_items=true so Check API writes them.
        contractor_payments: List of contractor payment dicts (see create_payroll for
            shape). Each must use "payment_method": "manual". When set, the tool
            sends ?include_contractor_payments=true so Check API writes them.
        metadata: Arbitrary key-value object stored on the payroll.
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/payrolls",
        data=build_body(
            {
                "correction": correction,
                "company": company,
                "period_start": period_start,
                "period_end": period_end,
                "payday": payday,
            },
            pay_frequency=pay_frequency,
            pay_schedule=pay_schedule,
            items=items,
            contractor_payments=contractor_payments,
            metadata=metadata,
        ),
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
        params=build_params(
            include_items=True if items is not None else None,
            include_contractor_payments=(
                True if contractor_payments is not None else None
            ),
        ),
    )


async def add_external_payroll(
    ctx: Ctx,
    correction: str,
    company: str,
    period_start: str,
    period_end: str,
    payday: str,
    pay_frequency: str | None = None,
    items: list[dict] | None = None,
    contractor_payments: list[dict] | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Add a new external payroll to a draft correction.

    Creates a draft external payroll attached to the correction. The company
    must have run a managed payroll. Payday must be in the past, before the
    company's start date, and within the correction's tax year. Approve, reopen,
    preview, and validate on the external payroll are unavailable once attached;
    use the correction workflow instead.

    Args:
        correction: ID of the draft correction to add the payroll to (e.g. "cor_xxxxx").
        company: The Check company ID. Must match the correction's company.
        period_start: Pay period start date (YYYY-MM-DD).
        period_end: Pay period end date (YYYY-MM-DD).
        payday: Payday date (YYYY-MM-DD). Must be in the past, before the
            company's start date, and in the correction's tax year.
        pay_frequency: Frequency at which the external payroll was paid.
        items: List of external payroll item dicts. Each may include "employee",
            "earnings" (list), "reimbursements" (list), "taxes" (list),
            "benefits" (list), "post_tax_deductions" (list).
        contractor_payments: List of contractor payment dicts. Each may include
            "contractor", "amount", "reimbursement_amount".
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/external_payrolls",
        data=build_body(
            {
                "correction": correction,
                "company": company,
                "period_start": period_start,
                "period_end": period_end,
                "payday": payday,
            },
            pay_frequency=pay_frequency,
            items=items,
            contractor_payments=contractor_payments,
        ),
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


async def preview_correction(ctx: Ctx, correction_id: str) -> dict:
    """Price a draft correction without moving money.

    Runs in the background: poll get_correction until "preview.status" is
    "succeeded" (the correction's "totals" then hold the exact amounts approval
    will move) or "failed".

    Args:
        correction_id: The Check correction ID.
    """
    return await check_api_post(ctx, f"/corrections/{correction_id}/preview")


async def approve_correction(ctx: Ctx, correction_id: str) -> dict:
    """Approve a draft correction, committing its payroll changes and moving money.

    Runs in the background: poll get_correction until "approval.status" is
    "succeeded" or "failed". If the amounts changed since the last preview,
    approval fails with "fulfillment_changed" and the correction's "totals" show
    the new amounts to review before approving again.

    Args:
        correction_id: The Check correction ID.
    """
    return await check_api_post(ctx, f"/corrections/{correction_id}/approve")


async def reopen_correction(ctx: Ctx, correction_id: str) -> dict:
    """Cancel a pending correction's approval and return it to draft.

    Only possible before the correction's "reopen_deadline".

    Args:
        correction_id: The Check correction ID.
    """
    return await check_api_post(ctx, f"/corrections/{correction_id}/reopen")


async def simulate_correction_start_processing(ctx: Ctx, correction_id: str) -> dict:
    """Simulate starting correction processing (sandbox only).

    For corrections with simulation_mode "manual". Returns an empty body on
    success; poll get_correction for the new status.

    Args:
        correction_id: The Check correction ID.
    """
    return await check_api_post(
        ctx, f"/corrections/{correction_id}/simulate/start_processing"
    )


async def simulate_correction_complete_funding(ctx: Ctx, correction_id: str) -> dict:
    """Simulate completing correction funding (sandbox only).

    For corrections with simulation_mode "manual". Returns an empty body on
    success; poll get_correction for the new status.

    Args:
        correction_id: The Check correction ID.
    """
    return await check_api_post(
        ctx, f"/corrections/{correction_id}/simulate/complete_funding"
    )


async def simulate_correction_fail_funding(ctx: Ctx, correction_id: str) -> dict:
    """Simulate failing correction funding (sandbox only).

    For corrections with simulation_mode "manual". Returns an empty body on
    success; poll get_correction for the new status.

    Args:
        correction_id: The Check correction ID.
    """
    return await check_api_post(
        ctx, f"/corrections/{correction_id}/simulate/fail_funding"
    )


async def get_correction_receipt(ctx: Ctx, correction_id: str) -> dict:
    """Get the tax rollup for a previewed correction.

    Available only after preview_correction succeeds. Returns totals and one
    entry per tax the correction moved, with each operation split into check
    and company amounts. Does not return a file URL; use
    get_correction_receipt_download for a PDF link.

    Args:
        correction_id: The Check correction ID.
    """
    return await check_api_get(ctx, f"/corrections/{correction_id}/receipt")


async def get_correction_receipt_download(ctx: Ctx, correction_id: str) -> dict:
    """Get a short-lived presigned URL for the correction receipt PDF.

    Available only after preview_correction succeeds. Each call mints a fresh
    URL with download_url, content_type, and expires_at.

    Args:
        correction_id: The Check correction ID.
    """
    return await check_api_get(ctx, f"/corrections/{correction_id}/receipt_download")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_corrections)
    add_annotated_tool(mcp, get_correction)
    add_annotated_tool(mcp, get_correction_receipt)
    add_annotated_tool(mcp, get_correction_receipt_download)
    if not read_only:
        add_annotated_tool(mcp, create_correction)
        add_annotated_tool(mcp, update_correction)
        add_annotated_tool(mcp, delete_correction)
        add_annotated_tool(mcp, void_payroll)
        add_annotated_tool(mcp, add_payroll_to_correction)
        add_annotated_tool(mcp, add_external_payroll)
        add_annotated_tool(mcp, preview_correction)
        add_annotated_tool(mcp, approve_correction)
        add_annotated_tool(mcp, reopen_correction)
        add_annotated_tool(mcp, simulate_correction_start_processing)
        add_annotated_tool(mcp, simulate_correction_complete_funding)
        add_annotated_tool(mcp, simulate_correction_fail_funding)
