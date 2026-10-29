"""External payroll tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    check_api_delete,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
    shape_payroll,
)


async def list_external_payrolls(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    ids: list[str] | None = None,
    cursor: str | None = None,
    pay_schedule: str | None = None,
    include_items: bool = False,
) -> dict:
    """List external payrolls, optionally filtered by company.

    Line items are omitted by default (the API would include every item of
    every payroll otherwise, which is slow for large companies and very large
    in context). Use get_external_payroll for one payroll's items, or pass
    include_items=true to get them inline for the whole page.

    Args:
        company: Filter to external payrolls belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return (default 10, max 100).
        ids: Filter to specific external payroll IDs.
        cursor: Pagination cursor from a previous response.
        pay_schedule: Filter by pay schedule ID.
        include_items: Return each payroll's line items and contractor payments
            inline (default false).
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
    if pay_schedule is not None:
        params["pay_schedule"] = pay_schedule
    params["include_items"] = str(include_items).lower()
    return await check_api_list(ctx, "/external_payrolls", params=params)


async def get_external_payroll(
    ctx: Ctx, payroll_id: str, include_items: bool = False
) -> dict:
    """Get details for a specific external payroll.

    The API always inlines the payroll's items and contractor payments; by
    default this tool replaces them with ``items_count`` and
    ``contractor_payments_count``. Pass ``include_items=true`` to get them.

    Args:
        payroll_id: The Check external payroll ID.
        include_items: Return line items and contractor payments inline
            (default false).
    """
    result = await check_api_get(ctx, f"/external_payrolls/{payroll_id}")
    return shape_payroll(result, include_items=include_items)


async def create_external_payroll(
    ctx: Ctx,
    company: str,
    period_start: str,
    period_end: str,
    payday: str,
    pay_frequency: str | None = None,
    items: list[dict] | None = None,
    contractor_payments: list[dict] | None = None,
    idempotency_key: str | None = None,
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
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.

    The response omits the inlined items and contractor payments (see
    get_external_payroll); ``items_count`` confirms how many were written.
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
    result = await check_api_post(
        ctx,
        "/external_payrolls",
        data=body,
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )
    return shape_payroll(result)


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

    The response omits the inlined items and contractor payments (see
    get_external_payroll).
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
    result = await check_api_patch(ctx, f"/external_payrolls/{payroll_id}", data=body)
    return shape_payroll(result)


async def delete_external_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Delete an external payroll.

    Args:
        payroll_id: The Check external payroll ID.
    """
    return await check_api_delete(ctx, f"/external_payrolls/{payroll_id}")


async def approve_external_payroll(
    ctx: Ctx, payroll_id: str, idempotency_key: str | None = None
) -> dict:
    """Approve an external payroll.

    Args:
        payroll_id: The Check external payroll ID.
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    result = await check_api_post(
        ctx,
        f"/external_payrolls/{payroll_id}/approve",
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )
    return shape_payroll(result)


async def reopen_external_payroll(ctx: Ctx, payroll_id: str) -> dict:
    """Reopen an external payroll.

    Args:
        payroll_id: The Check external payroll ID.
    """
    return shape_payroll(
        await check_api_post(ctx, f"/external_payrolls/{payroll_id}/reopen")
    )


async def preview_external_payroll(
    ctx: Ctx, external_payroll_id: str, include_items: bool = False
) -> dict:
    """Preview an external payroll.

    Per-item previews are omitted by default (``items_count`` says how many
    there are); pass ``include_items=true`` to get them inline.

    Args:
        external_payroll_id: The Check external payroll ID.
        include_items: Return per-item and per-contractor-payment previews
            inline (default false).
    """
    result = await check_api_get(
        ctx, f"/external_payrolls/{external_payroll_id}/preview"
    )
    return shape_payroll(result, include_items=include_items)


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_external_payrolls)
    add_annotated_tool(mcp, get_external_payroll)
    add_annotated_tool(mcp, preview_external_payroll)
    if not read_only:
        add_annotated_tool(mcp, create_external_payroll)
        add_annotated_tool(mcp, update_external_payroll)
        add_annotated_tool(mcp, delete_external_payroll)
        add_annotated_tool(mcp, approve_external_payroll)
        add_annotated_tool(mcp, reopen_external_payroll)
