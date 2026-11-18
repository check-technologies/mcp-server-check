"""Time off tools for the Check API: policies, balances, enrollments, and entries.

The time off endpoints are enabled per partner; for a partner without access
every one of them returns "not found".
"""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    apply_clear_fields,
    build_body,
    build_params,
    check_api_delete,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)

_ENROLLMENT_CLEARABLE = frozenset({"effective_end"})


def _idempotency_headers(idempotency_key: str | None) -> dict | None:
    return {"X-Idempotency-Key": idempotency_key} if idempotency_key else None


async def list_time_off_policies(
    ctx: Ctx,
    company: str | None = None,
    status: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> dict:
    """List time off policies, newest first.

    Args:
        company: Filter to policies of this Check company ID (e.g. "com_xxxxx").
        status: Filter by status: "active" or "archived".
        limit: Maximum number of results to return (default 100, max 100).
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/time_off_policies",
        params=build_params(company=company, status=status, limit=limit, cursor=cursor),
    )


async def get_time_off_policy(ctx: Ctx, policy_id: str) -> dict:
    """Get a time off policy.

    Args:
        policy_id: The time off policy ID (e.g. "time_off_policy_xxxxx").
    """
    return await check_api_get(ctx, f"/time_off_policies/{policy_id}")


async def create_time_off_policy(
    ctx: Ctx,
    company: str,
    label: str,
    accrual_method: str,
    policy_year: dict,
    annual_grant_options: dict | None = None,
    per_payroll_options: dict | None = None,
    per_hour_worked_options: dict | None = None,
    limits: dict | None = None,
    accrual_waiting_period_days: int | None = None,
    usage_waiting_period_days: int | None = None,
    metadata: dict | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Create a company's time off policy: the rules for how enrolled balances accrue.

    Only status changes after creation; to change any other setting, create a
    new policy and move the enrollments to it.

    Args:
        company: The Check company ID.
        label: Name shown for the policy (e.g. "PTO").
        accrual_method: "annual_grant", "per_payroll", "per_hour_worked", or
            "none". Pass the options dict matching the method and no other.
        policy_year: {"basis": "fixed_date", "date": "MM-DD"} for a year that
            starts on the same date for everyone, or {"basis": "enrollment"} for
            a year that starts on each enrollment's anniversary.
        annual_grant_options: For annual_grant: {"hours": "80.00",
            "partial_year_method": "prorate" or "full"}.
        per_payroll_options: For per_payroll: {"hours_per_year": "120.00"},
            spread across the employee's payrolls.
        per_hour_worked_options: For per_hour_worked: {"hours": "1.00",
            "per_hours_worked": "30.00", "include_overtime": false}.
        limits: Optional hour limits, each a decimal string or null for no limit:
            max_balance, min_balance (default "0.00"; null allows any negative
            balance), max_rollover, max_accrual_per_policy_year.
        accrual_waiting_period_days: Days after the enrollment starts before
            hours accrue. Default 0.
        usage_waiting_period_days: Days after the enrollment starts before hours
            can be spent without a warning. Default 0.
        metadata: Arbitrary key-value object stored on the policy.
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/time_off_policies",
        data=build_body(
            {
                "company": company,
                "label": label,
                "accrual_method": accrual_method,
                "policy_year": policy_year,
            },
            annual_grant_options=annual_grant_options,
            per_payroll_options=per_payroll_options,
            per_hour_worked_options=per_hour_worked_options,
            limits=limits,
            accrual_waiting_period_days=accrual_waiting_period_days,
            usage_waiting_period_days=usage_waiting_period_days,
            metadata=metadata,
        ),
        headers=_idempotency_headers(idempotency_key),
    )


async def update_time_off_policy(ctx: Ctx, policy_id: str, status: str) -> dict:
    """Archive or reactivate a time off policy. Status is the only mutable field.

    An archived policy takes no new enrollments, and its enrollments can end but
    not be extended or reopened.

    Args:
        policy_id: The time off policy ID.
        status: "active" or "archived".
    """
    return await check_api_patch(
        ctx, f"/time_off_policies/{policy_id}", data={"status": status}
    )


async def list_time_off_balances(
    ctx: Ctx,
    employee: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> dict:
    """List time off balances, newest first. Each balance has its current hours.

    Args:
        employee: Filter to balances of this Check employee ID (e.g. "emp_xxxxx").
        limit: Maximum number of results to return (default 100, max 100).
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/time_off_balances",
        params=build_params(employee=employee, limit=limit, cursor=cursor),
    )


async def get_time_off_balance(ctx: Ctx, balance_id: str) -> dict:
    """Get a time off balance and its current hours.

    Args:
        balance_id: The time off balance ID (e.g. "time_off_balance_xxxxx").
    """
    return await check_api_get(ctx, f"/time_off_balances/{balance_id}")


async def create_time_off_balance(
    ctx: Ctx,
    employee: str,
    label: str,
    metadata: dict | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Open a time off balance for an employee, at zero hours.

    Hours change only through entries: enroll the balance in a policy to accrue,
    or create a manual entry for an opening balance or adjustment.

    Args:
        employee: The Check employee ID.
        label: Name shown for the balance (e.g. "PTO" or "Sick").
        metadata: Arbitrary key-value object stored on the balance.
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/time_off_balances",
        data=build_body({"employee": employee, "label": label}, metadata=metadata),
        headers=_idempotency_headers(idempotency_key),
    )


async def update_time_off_balance(ctx: Ctx, balance_id: str, metadata: dict) -> dict:
    """Update a time off balance's metadata, its only mutable field.

    Args:
        balance_id: The time off balance ID.
        metadata: Keys to merge into the stored metadata; a key set to null is
            removed, and {} clears it.
    """
    return await check_api_patch(
        ctx, f"/time_off_balances/{balance_id}", data={"metadata": metadata}
    )


async def list_time_off_enrollments(
    ctx: Ctx,
    balance: str | None = None,
    employee: str | None = None,
    policy: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> dict:
    """List time off enrollments, newest first.

    Args:
        balance: Filter to enrollments of this time off balance ID.
        employee: Filter to enrollments of this Check employee ID.
        policy: Filter to enrollments in this time off policy ID.
        limit: Maximum number of results to return (default 100, max 100).
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/time_off_enrollments",
        params=build_params(
            balance=balance,
            employee=employee,
            policy=policy,
            limit=limit,
            cursor=cursor,
        ),
    )


async def get_time_off_enrollment(ctx: Ctx, enrollment_id: str) -> dict:
    """Get a time off enrollment.

    Args:
        enrollment_id: The time off enrollment ID (e.g. "time_off_enrollment_xxxxx").
    """
    return await check_api_get(ctx, f"/time_off_enrollments/{enrollment_id}")


async def create_time_off_enrollment(
    ctx: Ctx,
    balance: str,
    policy: str,
    effective_start: str | None = None,
    effective_end: str | None = None,
    metadata: dict | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Enroll a time off balance in a policy for a date range.

    A balance's enrollments can't overlap; to change policies, end the current
    enrollment with update_time_off_enrollment and enroll from the next day. An
    enrollment starting today or earlier immediately writes the grants and
    expirations due through today.

    Args:
        balance: The time off balance ID.
        policy: An active time off policy ID in the employee's company.
        effective_start: First day covered (YYYY-MM-DD). Defaults to the
            employee's start date; required when the employee has none.
        effective_end: Last day covered (YYYY-MM-DD), or omit for open-ended.
        metadata: Arbitrary key-value object stored on the enrollment.
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/time_off_enrollments",
        data=build_body(
            {"balance": balance, "policy": policy},
            effective_start=effective_start,
            effective_end=effective_end,
            metadata=metadata,
        ),
        headers=_idempotency_headers(idempotency_key),
    )


async def update_time_off_enrollment(
    ctx: Ctx,
    enrollment_id: str,
    effective_end: str | None = None,
    metadata: dict | None = None,
    clear_fields: list[str] | None = None,
) -> dict:
    """End, extend, or reopen a time off enrollment, or update its metadata.

    effective_end and metadata are the only mutable fields; to change the
    policy or start, end this enrollment and create a new one.

    Args:
        enrollment_id: The time off enrollment ID.
        effective_end: New last day covered (YYYY-MM-DD).
        metadata: Keys to merge into the stored metadata; a key set to null is
            removed, and {} clears it.
        clear_fields: Fields to send as null. Accepts "effective_end", which
            reopens the enrollment with no end.
    """
    body = build_body({}, effective_end=effective_end, metadata=metadata)
    apply_clear_fields(body, clear_fields, _ENROLLMENT_CLEARABLE)
    return await check_api_patch(
        ctx, f"/time_off_enrollments/{enrollment_id}", data=body
    )


async def delete_time_off_enrollment(ctx: Ctx, enrollment_id: str) -> dict:
    """Delete a time off enrollment that no entries reference, freeing its dates.

    Fails with resource_in_use once the enrollment has written a grant, accrual,
    or expiration; end it with update_time_off_enrollment instead.

    Args:
        enrollment_id: The time off enrollment ID.
    """
    return await check_api_delete(ctx, f"/time_off_enrollments/{enrollment_id}")


async def list_time_off_entries(
    ctx: Ctx,
    balance: str | None = None,
    employee: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> dict:
    """List time off entries, newest first: the signed hour changes on balances.

    Each entry's source is "payroll" (accruals and spends from an approved
    payroll), "annual_grant", "expiration", or "manual".

    Args:
        balance: Filter to entries on this time off balance ID.
        employee: Filter to entries of this Check employee ID.
        limit: Maximum number of results to return (default 100, max 100).
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/time_off_entries",
        params=build_params(
            balance=balance, employee=employee, limit=limit, cursor=cursor
        ),
    )


async def get_time_off_entry(ctx: Ctx, entry_id: str) -> dict:
    """Get a time off entry.

    Args:
        entry_id: The time off entry ID (e.g. "time_off_entry_xxxxx").
    """
    return await check_api_get(ctx, f"/time_off_entries/{entry_id}")


async def create_time_off_entry(
    ctx: Ctx,
    balance: str,
    hours: str,
    date: str | None = None,
    description: str | None = None,
    metadata: dict | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Record a manual time off entry, adding its hours to the balance.

    Use it for an opening balance or an adjustment. Entries are immutable; to
    undo one, record another with the opposite sign.

    Args:
        balance: The time off balance ID.
        hours: Signed decimal string, e.g. "24.00" to add or "-8.00" to remove.
            Can't be zero.
        date: The day the hours apply (YYYY-MM-DD). Defaults to today.
        description: Optional note shown on the entry.
        metadata: Arbitrary key-value object stored on the entry.
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/time_off_entries",
        data=build_body(
            {"balance": balance, "hours": hours, "source": "manual"},
            date=date,
            description=description,
            metadata=metadata,
        ),
        headers=_idempotency_headers(idempotency_key),
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_time_off_policies)
    add_annotated_tool(mcp, get_time_off_policy)
    add_annotated_tool(mcp, list_time_off_balances)
    add_annotated_tool(mcp, get_time_off_balance)
    add_annotated_tool(mcp, list_time_off_enrollments)
    add_annotated_tool(mcp, get_time_off_enrollment)
    add_annotated_tool(mcp, list_time_off_entries)
    add_annotated_tool(mcp, get_time_off_entry)
    if not read_only:
        add_annotated_tool(mcp, create_time_off_policy)
        add_annotated_tool(mcp, update_time_off_policy)
        add_annotated_tool(mcp, create_time_off_balance)
        add_annotated_tool(mcp, update_time_off_balance)
        add_annotated_tool(mcp, create_time_off_enrollment)
        add_annotated_tool(mcp, update_time_off_enrollment)
        add_annotated_tool(mcp, delete_time_off_enrollment)
        add_annotated_tool(mcp, create_time_off_entry)
