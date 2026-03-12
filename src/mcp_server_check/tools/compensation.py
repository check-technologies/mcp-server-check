"""Compensation tools for the Check API (pay schedules, benefits, deductions, etc.)."""

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


# --- Pay Schedules ---


async def list_pay_schedules(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List pay schedules, optionally filtered by company.

    Args:
        company: Filter to pay schedules belonging to this Check company ID (e.g. "com_xxxxx").
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
    return await check_api_list(ctx, "/pay_schedules", params=params or None)


async def get_pay_schedule(ctx: Ctx, pay_schedule_id: str) -> dict:
    """Get details for a specific pay schedule.

    Args:
        pay_schedule_id: The Check pay schedule ID.
    """
    return await check_api_get(ctx, f"/pay_schedules/{pay_schedule_id}")


async def create_pay_schedule(
    ctx: Ctx,
    company: str,
    pay_frequency: str,
    first_payday: str,
    first_period_end: str,
    second_payday: str | None = None,
    name: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Create a new pay schedule.

    Args:
        company: The Check company ID.
        pay_frequency: Pay frequency — "weekly", "biweekly", "semimonthly", "monthly",
            "quarterly", or "annually".
        first_payday: Payday date of the first payroll on this schedule (YYYY-MM-DD).
        first_period_end: Period end date of the first payroll on this schedule (YYYY-MM-DD).
        second_payday: Second payday date (semimonthly only; must be between one day and
            one month after first_payday).
        name: Human-readable name for the pay schedule.
        metadata: Additional JSON metadata string.
    """
    body: dict = {
        "company": company,
        "pay_frequency": pay_frequency,
        "first_payday": first_payday,
        "first_period_end": first_period_end,
    }
    if second_payday is not None:
        body["second_payday"] = second_payday
    if name is not None:
        body["name"] = name
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_post(ctx, "/pay_schedules", data=body)


async def update_pay_schedule(
    ctx: Ctx,
    pay_schedule_id: str,
    pay_frequency: str | None = None,
    first_payday: str | None = None,
    first_period_end: str | None = None,
    second_payday: str | None = None,
    name: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Update a pay schedule.

    Args:
        pay_schedule_id: The Check pay schedule ID.
        pay_frequency: Pay frequency — "weekly", "biweekly", "semimonthly", "monthly",
            "quarterly", or "annually".
        first_payday: Payday date of the first payroll on this schedule (YYYY-MM-DD).
        first_period_end: Period end date of the first payroll (YYYY-MM-DD).
        second_payday: Second payday date (semimonthly only).
        name: Human-readable name for the pay schedule.
        metadata: Additional JSON metadata string.
    """
    body: dict = {}
    if pay_frequency is not None:
        body["pay_frequency"] = pay_frequency
    if first_payday is not None:
        body["first_payday"] = first_payday
    if first_period_end is not None:
        body["first_period_end"] = first_period_end
    if second_payday is not None:
        body["second_payday"] = second_payday
    if name is not None:
        body["name"] = name
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_patch(ctx, f"/pay_schedules/{pay_schedule_id}", data=body)


async def delete_pay_schedule(ctx: Ctx, pay_schedule_id: str) -> dict:
    """Delete a pay schedule.

    Args:
        pay_schedule_id: The Check pay schedule ID.
    """
    return await check_api_delete(ctx, f"/pay_schedules/{pay_schedule_id}")


async def get_pay_schedule_paydays(
    ctx: Ctx,
    pay_schedule_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Get paydays for a pay schedule.

    Args:
        pay_schedule_id: The Check pay schedule ID.
        start_date: Start of date range (YYYY-MM-DD).
        end_date: End of date range (YYYY-MM-DD).
    """
    params: dict = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await check_api_get(
        ctx, f"/pay_schedules/{pay_schedule_id}/paydays", params=params or None
    )


# --- Benefits ---


async def list_benefits(
    ctx: Ctx,
    company: str | None = None,
    employee: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List employee benefits, optionally filtered by company or employee.

    Args:
        company: Filter to benefits belonging to this Check company ID (e.g. "com_xxxxx").
        employee: Filter to benefits for this Check employee ID (e.g. "emp_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if employee is not None:
        params["employee"] = employee
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/benefits", params=params or None)


async def get_benefit(ctx: Ctx, benefit_id: str) -> dict:
    """Get details for a specific benefit.

    Args:
        benefit_id: The Check benefit ID.
    """
    return await check_api_get(ctx, f"/benefits/{benefit_id}")


async def create_benefit(
    ctx: Ctx,
    employee: str,
    company_benefit: str,
    benefit: str | None = None,
    period: str | None = None,
    description: str | None = None,
    company_contribution_amount: str | None = None,
    company_contribution_percent: float | None = None,
    company_period_amount: str | None = None,
    employee_contribution_amount: str | None = None,
    employee_contribution_percent: float | None = None,
    employee_period_amount: str | None = None,
    effective_start: str | None = None,
    effective_end: str | None = None,
    hsa_contribution_limit: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Create a new employee benefit.

    Args:
        employee: The Check employee ID.
        company_benefit: The Check company benefit ID.
        benefit: Type of supported benefit.
        period: Period over which a period amount is distributed — "monthly" or null.
        description: Description to distinguish the benefit within a plan (max 255 chars).
        company_contribution_amount: Company contribution amount per payroll.
        company_contribution_percent: Company contribution as percent of gross pay (0-100).
        company_period_amount: Company contribution over the period.
        employee_contribution_amount: Employee contribution amount per payroll.
        employee_contribution_percent: Employee contribution as percent of gross pay (0-100).
        employee_period_amount: Employee contribution over the period.
        effective_start: Start date for the benefit (YYYY-MM-DD).
        effective_end: End date for the benefit (YYYY-MM-DD).
        hsa_contribution_limit: HSA contribution limit.
        metadata: Additional JSON metadata string.
    """
    body: dict = {"employee": employee, "company_benefit": company_benefit}
    if benefit is not None:
        body["benefit"] = benefit
    if period is not None:
        body["period"] = period
    if description is not None:
        body["description"] = description
    if company_contribution_amount is not None:
        body["company_contribution_amount"] = company_contribution_amount
    if company_contribution_percent is not None:
        body["company_contribution_percent"] = company_contribution_percent
    if company_period_amount is not None:
        body["company_period_amount"] = company_period_amount
    if employee_contribution_amount is not None:
        body["employee_contribution_amount"] = employee_contribution_amount
    if employee_contribution_percent is not None:
        body["employee_contribution_percent"] = employee_contribution_percent
    if employee_period_amount is not None:
        body["employee_period_amount"] = employee_period_amount
    if effective_start is not None:
        body["effective_start"] = effective_start
    if effective_end is not None:
        body["effective_end"] = effective_end
    if hsa_contribution_limit is not None:
        body["hsa_contribution_limit"] = hsa_contribution_limit
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_post(ctx, "/benefits", data=body)


async def update_benefit(
    ctx: Ctx,
    benefit_id: str,
    benefit: str | None = None,
    period: str | None = None,
    description: str | None = None,
    company_contribution_amount: str | None = None,
    company_contribution_percent: float | None = None,
    company_period_amount: str | None = None,
    employee_contribution_amount: str | None = None,
    employee_contribution_percent: float | None = None,
    employee_period_amount: str | None = None,
    effective_start: str | None = None,
    effective_end: str | None = None,
    hsa_contribution_limit: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Update a benefit.

    Args:
        benefit_id: The Check benefit ID.
        benefit: Type of supported benefit.
        period: Period over which a period amount is distributed — "monthly" or null.
        description: Description to distinguish the benefit (max 255 chars).
        company_contribution_amount: Company contribution amount per payroll.
        company_contribution_percent: Company contribution as percent of gross pay (0-100).
        company_period_amount: Company contribution over the period.
        employee_contribution_amount: Employee contribution amount per payroll.
        employee_contribution_percent: Employee contribution as percent of gross pay (0-100).
        employee_period_amount: Employee contribution over the period.
        effective_start: Start date for the benefit (YYYY-MM-DD).
        effective_end: End date for the benefit (YYYY-MM-DD).
        hsa_contribution_limit: HSA contribution limit.
        metadata: Additional JSON metadata string.
    """
    body: dict = {}
    if benefit is not None:
        body["benefit"] = benefit
    if period is not None:
        body["period"] = period
    if description is not None:
        body["description"] = description
    if company_contribution_amount is not None:
        body["company_contribution_amount"] = company_contribution_amount
    if company_contribution_percent is not None:
        body["company_contribution_percent"] = company_contribution_percent
    if company_period_amount is not None:
        body["company_period_amount"] = company_period_amount
    if employee_contribution_amount is not None:
        body["employee_contribution_amount"] = employee_contribution_amount
    if employee_contribution_percent is not None:
        body["employee_contribution_percent"] = employee_contribution_percent
    if employee_period_amount is not None:
        body["employee_period_amount"] = employee_period_amount
    if effective_start is not None:
        body["effective_start"] = effective_start
    if effective_end is not None:
        body["effective_end"] = effective_end
    if hsa_contribution_limit is not None:
        body["hsa_contribution_limit"] = hsa_contribution_limit
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_patch(ctx, f"/benefits/{benefit_id}", data=body)


async def delete_benefit(ctx: Ctx, benefit_id: str) -> dict:
    """Delete a benefit.

    Args:
        benefit_id: The Check benefit ID.
    """
    return await check_api_delete(ctx, f"/benefits/{benefit_id}")


# --- Post-Tax Deductions ---


async def list_post_tax_deductions(
    ctx: Ctx,
    company: str | None = None,
    employee: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List post-tax deductions, optionally filtered by company or employee.

    Args:
        company: Filter to post-tax deductions belonging to this Check company ID (e.g. "com_xxxxx").
        employee: Filter to post-tax deductions for this Check employee ID (e.g. "emp_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if employee is not None:
        params["employee"] = employee
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/post_tax_deductions", params=params or None)


async def get_post_tax_deduction(ctx: Ctx, deduction_id: str) -> dict:
    """Get details for a specific post-tax deduction.

    Args:
        deduction_id: The Check post-tax deduction ID.
    """
    return await check_api_get(ctx, f"/post_tax_deductions/{deduction_id}")


async def create_post_tax_deduction(
    ctx: Ctx,
    employee: str,
    type: str,
    description: str,
    effective_start: str,
    effective_end: str | None = None,
    miscellaneous: dict | None = None,
    child_support: dict | None = None,
    miscellaneous_garnishment: dict | None = None,
    metadata: str | None = None,
    managed: bool | None = None,
) -> dict:
    """Create a new post-tax deduction.

    Args:
        employee: The Check employee ID.
        type: Deduction type — "miscellaneous", "child_support", or
            "miscellaneous_garnishment".
        description: Description of the deduction (max 255 chars).
        effective_start: Start date for the deduction (YYYY-MM-DD).
        effective_end: End date for the deduction (YYYY-MM-DD).
        miscellaneous: Config dict for miscellaneous type with keys: total_amount,
            amount, percent, annual_limit.
        child_support: Config dict for child_support type with keys: external_id,
            agency, fips_code, issue_date, amount, max_percent.
        miscellaneous_garnishment: Config dict for miscellaneous_garnishment type with
            keys: amount, percent, total_amount, annual_limit, priority, max_percent.
        metadata: Additional JSON metadata string.
        managed: Whether the deduction should be remitted by Check (child support only).
    """
    body: dict = {
        "employee": employee,
        "type": type,
        "description": description,
        "effective_start": effective_start,
    }
    if effective_end is not None:
        body["effective_end"] = effective_end
    if miscellaneous is not None:
        body["miscellaneous"] = miscellaneous
    if child_support is not None:
        body["child_support"] = child_support
    if miscellaneous_garnishment is not None:
        body["miscellaneous_garnishment"] = miscellaneous_garnishment
    if metadata is not None:
        body["metadata"] = metadata
    if managed is not None:
        body["managed"] = managed
    return await check_api_post(ctx, "/post_tax_deductions", data=body)


async def update_post_tax_deduction(
    ctx: Ctx,
    deduction_id: str,
    description: str | None = None,
    effective_start: str | None = None,
    effective_end: str | None = None,
    miscellaneous: dict | None = None,
    child_support: dict | None = None,
    miscellaneous_garnishment: dict | None = None,
    metadata: str | None = None,
    managed: bool | None = None,
) -> dict:
    """Update a post-tax deduction.

    Args:
        deduction_id: The Check post-tax deduction ID.
        description: Description of the deduction (max 255 chars).
        effective_start: Start date for the deduction (YYYY-MM-DD).
        effective_end: End date for the deduction (YYYY-MM-DD).
        miscellaneous: Config dict for miscellaneous type (see create_post_tax_deduction).
        child_support: Config dict for child_support type (see create_post_tax_deduction).
        miscellaneous_garnishment: Config dict for miscellaneous_garnishment type
            (see create_post_tax_deduction).
        metadata: Additional JSON metadata string.
        managed: Whether the deduction should be remitted by Check (child support only).
    """
    body: dict = {}
    if description is not None:
        body["description"] = description
    if effective_start is not None:
        body["effective_start"] = effective_start
    if effective_end is not None:
        body["effective_end"] = effective_end
    if miscellaneous is not None:
        body["miscellaneous"] = miscellaneous
    if child_support is not None:
        body["child_support"] = child_support
    if miscellaneous_garnishment is not None:
        body["miscellaneous_garnishment"] = miscellaneous_garnishment
    if metadata is not None:
        body["metadata"] = metadata
    if managed is not None:
        body["managed"] = managed
    return await check_api_patch(ctx, f"/post_tax_deductions/{deduction_id}", data=body)


async def delete_post_tax_deduction(ctx: Ctx, deduction_id: str) -> dict:
    """Delete a post-tax deduction.

    Args:
        deduction_id: The Check post-tax deduction ID.
    """
    return await check_api_delete(ctx, f"/post_tax_deductions/{deduction_id}")


# --- Company Benefits ---


async def list_company_benefits(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List company-level benefits, optionally filtered by company.

    Args:
        company: Filter to company benefits belonging to this Check company ID (e.g. "com_xxxxx").
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
    return await check_api_list(ctx, "/company_benefits", params=params or None)


async def get_company_benefit(ctx: Ctx, company_benefit_id: str) -> dict:
    """Get details for a specific company benefit.

    Args:
        company_benefit_id: The Check company benefit ID.
    """
    return await check_api_get(ctx, f"/company_benefits/{company_benefit_id}")


async def create_company_benefit(
    ctx: Ctx,
    company: str,
    benefit: str,
    description: str,
    period: str | None = None,
    company_contribution_amount: str | None = None,
    company_contribution_percent: str | None = None,
    company_period_amount: str | None = None,
    employee_contribution_amount: str | None = None,
    employee_contribution_percent: str | None = None,
    employee_period_amount: str | None = None,
    effective_start: str | None = None,
    effective_end: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Create a new company benefit.

    Args:
        company: The Check company ID.
        benefit: Type of supported benefit.
        description: Description to distinguish the benefit (max 255 chars).
        period: Period over which a period amount is distributed — "monthly" or null.
        company_contribution_amount: Default company contribution per payroll.
        company_contribution_percent: Default company contribution as percent of gross (0-100).
        company_period_amount: Default company contribution over the period.
        employee_contribution_amount: Default employee contribution per payroll.
        employee_contribution_percent: Default employee contribution as percent of gross (0-100).
        employee_period_amount: Default employee contribution over the period.
        effective_start: Start date for the benefit (YYYY-MM-DD).
        effective_end: End date for the benefit (YYYY-MM-DD).
        metadata: Additional JSON metadata string.
    """
    body: dict = {
        "company": company,
        "benefit": benefit,
        "description": description,
    }
    if period is not None:
        body["period"] = period
    if company_contribution_amount is not None:
        body["company_contribution_amount"] = company_contribution_amount
    if company_contribution_percent is not None:
        body["company_contribution_percent"] = company_contribution_percent
    if company_period_amount is not None:
        body["company_period_amount"] = company_period_amount
    if employee_contribution_amount is not None:
        body["employee_contribution_amount"] = employee_contribution_amount
    if employee_contribution_percent is not None:
        body["employee_contribution_percent"] = employee_contribution_percent
    if employee_period_amount is not None:
        body["employee_period_amount"] = employee_period_amount
    if effective_start is not None:
        body["effective_start"] = effective_start
    if effective_end is not None:
        body["effective_end"] = effective_end
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_post(ctx, "/company_benefits", data=body)


async def update_company_benefit(
    ctx: Ctx,
    company_benefit_id: str,
    benefit: str | None = None,
    description: str | None = None,
    period: str | None = None,
    company_contribution_amount: str | None = None,
    company_contribution_percent: str | None = None,
    company_period_amount: str | None = None,
    employee_contribution_amount: str | None = None,
    employee_contribution_percent: str | None = None,
    employee_period_amount: str | None = None,
    effective_start: str | None = None,
    effective_end: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Update a company benefit.

    Args:
        company_benefit_id: The Check company benefit ID.
        benefit: Type of supported benefit.
        description: Description to distinguish the benefit (max 255 chars).
        period: Period over which a period amount is distributed — "monthly" or null.
        company_contribution_amount: Default company contribution per payroll.
        company_contribution_percent: Default company contribution as percent of gross (0-100).
        company_period_amount: Default company contribution over the period.
        employee_contribution_amount: Default employee contribution per payroll.
        employee_contribution_percent: Default employee contribution as percent of gross (0-100).
        employee_period_amount: Default employee contribution over the period.
        effective_start: Start date for the benefit (YYYY-MM-DD).
        effective_end: End date for the benefit (YYYY-MM-DD).
        metadata: Additional JSON metadata string.
    """
    body: dict = {}
    if benefit is not None:
        body["benefit"] = benefit
    if description is not None:
        body["description"] = description
    if period is not None:
        body["period"] = period
    if company_contribution_amount is not None:
        body["company_contribution_amount"] = company_contribution_amount
    if company_contribution_percent is not None:
        body["company_contribution_percent"] = company_contribution_percent
    if company_period_amount is not None:
        body["company_period_amount"] = company_period_amount
    if employee_contribution_amount is not None:
        body["employee_contribution_amount"] = employee_contribution_amount
    if employee_contribution_percent is not None:
        body["employee_contribution_percent"] = employee_contribution_percent
    if employee_period_amount is not None:
        body["employee_period_amount"] = employee_period_amount
    if effective_start is not None:
        body["effective_start"] = effective_start
    if effective_end is not None:
        body["effective_end"] = effective_end
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_patch(
        ctx, f"/company_benefits/{company_benefit_id}", data=body
    )


async def delete_company_benefit(ctx: Ctx, company_benefit_id: str) -> dict:
    """Delete a company benefit.

    Args:
        company_benefit_id: The Check company benefit ID.
    """
    return await check_api_delete(ctx, f"/company_benefits/{company_benefit_id}")


# --- Earning Rates ---


async def list_earning_rates(
    ctx: Ctx,
    company: str | None = None,
    employee: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List earning rates, optionally filtered by company or employee.

    Args:
        company: Filter to earning rates belonging to this Check company ID (e.g. "com_xxxxx").
        employee: Filter to earning rates for this Check employee ID (e.g. "emp_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if employee is not None:
        params["employee"] = employee
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/earning_rates", params=params or None)


async def get_earning_rate(ctx: Ctx, earning_rate_id: str) -> dict:
    """Get details for a specific earning rate.

    Args:
        earning_rate_id: The Check earning rate ID.
    """
    return await check_api_get(ctx, f"/earning_rates/{earning_rate_id}")


async def create_earning_rate(
    ctx: Ctx,
    employee: str,
    amount: str,
    period: str,
    name: str | None = None,
    workweek_hours: float | None = None,
) -> dict:
    """Create a new earning rate.

    Args:
        employee: The Check employee ID.
        amount: The earning rate amount (e.g. "25.00" or "52000.00").
        period: Period type — "hourly", "annually", or "piece".
        name: Name of the earning rate.
        workweek_hours: Hours per week the employee works. Default: 40.
    """
    body: dict = {"employee": employee, "amount": amount, "period": period}
    if name is not None:
        body["name"] = name
    if workweek_hours is not None:
        body["workweek_hours"] = workweek_hours
    return await check_api_post(ctx, "/earning_rates", data=body)


async def update_earning_rate(
    ctx: Ctx,
    earning_rate_id: str,
    name: str | None = None,
    active: bool | None = None,
    metadata: str | None = None,
) -> dict:
    """Update an earning rate.

    Args:
        earning_rate_id: The Check earning rate ID.
        name: Name of the earning rate.
        active: Whether the earning rate is active.
        metadata: Additional JSON metadata string.
    """
    body: dict = {}
    if name is not None:
        body["name"] = name
    if active is not None:
        body["active"] = active
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_patch(ctx, f"/earning_rates/{earning_rate_id}", data=body)


# --- Earning Codes ---


async def list_earning_codes(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List earning codes, optionally filtered by company.

    Args:
        company: Filter to earning codes belonging to this Check company ID (e.g. "com_xxxxx").
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
    return await check_api_list(ctx, "/earning_codes", params=params or None)


async def get_earning_code(ctx: Ctx, earning_code_id: str) -> dict:
    """Get details for a specific earning code.

    Args:
        earning_code_id: The Check earning code ID.
    """
    return await check_api_get(ctx, f"/earning_codes/{earning_code_id}")


async def create_earning_code(
    ctx: Ctx,
    company: str,
    name: str,
    type: str,
    active: bool | None = None,
    calculation_overrides: dict | None = None,
    metadata: str | None = None,
) -> dict:
    """Create a new earning code.

    Args:
        company: The Check company ID.
        name: Name of the earning code.
        type: Type of earning code.
        active: Whether the code is active (true for ongoing, false for historical).
            Default: true.
        calculation_overrides: Tax calculation overrides dict. May include
            "wa_risk_class_code" (format "####-##" for WA L&I).
        metadata: Additional JSON metadata string.
    """
    body: dict = {"company": company, "name": name, "type": type}
    if active is not None:
        body["active"] = active
    if calculation_overrides is not None:
        body["calculation_overrides"] = calculation_overrides
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_post(ctx, "/earning_codes", data=body)


async def update_earning_code(
    ctx: Ctx,
    earning_code_id: str,
    active: bool | None = None,
    metadata: str | None = None,
) -> dict:
    """Update an earning code.

    Args:
        earning_code_id: The Check earning code ID.
        active: Whether the earning code is active.
        metadata: Additional JSON metadata string.
    """
    body: dict = {}
    if active is not None:
        body["active"] = active
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_patch(ctx, f"/earning_codes/{earning_code_id}", data=body)


# --- Net Pay Splits ---


async def list_net_pay_splits(
    ctx: Ctx,
    company: str | None = None,
    employee: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List net pay splits, optionally filtered by company or employee.

    Args:
        company: Filter to net pay splits belonging to this Check company ID (e.g. "com_xxxxx").
        employee: Filter to net pay splits for this Check employee ID (e.g. "emp_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    if employee is not None:
        params["employee"] = employee
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(ctx, "/net_pay_splits", params=params or None)


async def get_net_pay_split(ctx: Ctx, net_pay_split_id: str) -> dict:
    """Get details for a specific net pay split.

    Args:
        net_pay_split_id: The Check net pay split ID.
    """
    return await check_api_get(ctx, f"/net_pay_splits/{net_pay_split_id}")


async def create_net_pay_split(
    ctx: Ctx,
    splits: list[dict],
    employee: str | None = None,
    contractor: str | None = None,
    is_default: bool | None = None,
) -> dict:
    """Create a new net pay split.

    Provide either employee or contractor to indicate who owns the split.

    Args:
        splits: Prioritized list of split dicts. Each may include "bank_account",
            "priority" (int, default 1), "amount" (max amount for this account),
            "percentage" (percent of net pay).
        employee: The Check employee ID.
        contractor: The Check contractor ID.
        is_default: Whether this is the default net pay split. Default: false.
    """
    body: dict = {"splits": splits}
    if employee is not None:
        body["employee"] = employee
    if contractor is not None:
        body["contractor"] = contractor
    if is_default is not None:
        body["is_default"] = is_default
    return await check_api_post(ctx, "/net_pay_splits", data=body)


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    # Pay Schedules
    mcp.add_tool(list_pay_schedules)
    mcp.add_tool(get_pay_schedule)
    mcp.add_tool(get_pay_schedule_paydays)
    # Benefits
    mcp.add_tool(list_benefits)
    mcp.add_tool(get_benefit)
    # Post-Tax Deductions
    mcp.add_tool(list_post_tax_deductions)
    mcp.add_tool(get_post_tax_deduction)
    # Company Benefits
    mcp.add_tool(list_company_benefits)
    mcp.add_tool(get_company_benefit)
    # Earning Rates
    mcp.add_tool(list_earning_rates)
    mcp.add_tool(get_earning_rate)
    # Earning Codes
    mcp.add_tool(list_earning_codes)
    mcp.add_tool(get_earning_code)
    # Net Pay Splits
    mcp.add_tool(list_net_pay_splits)
    mcp.add_tool(get_net_pay_split)
    if not read_only:
        # Pay Schedules
        mcp.add_tool(create_pay_schedule)
        mcp.add_tool(update_pay_schedule)
        mcp.add_tool(delete_pay_schedule)
        # Benefits
        mcp.add_tool(create_benefit)
        mcp.add_tool(update_benefit)
        mcp.add_tool(delete_benefit)
        # Post-Tax Deductions
        mcp.add_tool(create_post_tax_deduction)
        mcp.add_tool(update_post_tax_deduction)
        mcp.add_tool(delete_post_tax_deduction)
        # Company Benefits
        mcp.add_tool(create_company_benefit)
        mcp.add_tool(update_company_benefit)
        mcp.add_tool(delete_company_benefit)
        # Earning Rates
        mcp.add_tool(create_earning_rate)
        mcp.add_tool(update_earning_rate)
        # Earning Codes
        mcp.add_tool(create_earning_code)
        mcp.add_tool(update_earning_code)
        # Net Pay Splits
        mcp.add_tool(create_net_pay_split)
