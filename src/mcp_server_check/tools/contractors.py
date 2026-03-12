"""Contractor tools for the Check API."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server_check.helpers import (
    Ctx,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)


async def list_contractors(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    ids: list[str] | None = None,
    cursor: str | None = None,
) -> dict:
    """List contractors, optionally filtered by company.

    Args:
        company: Filter to contractors belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return (default 10, max 100).
        ids: Filter to specific contractor IDs.
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
    return await check_api_list(ctx, "/contractors", params=params or None)


async def get_contractor(ctx: Ctx, contractor_id: str) -> dict:
    """Get details for a specific contractor.

    Args:
        contractor_id: The Check contractor ID (e.g. "ctr_xxxxx").
    """
    return await check_api_get(ctx, f"/contractors/{contractor_id}")


async def create_contractor(
    ctx: Ctx,
    company: str,
    type: str | None = None,
    first_name: str | None = None,
    middle_name: str | None = None,
    last_name: str | None = None,
    business_name: str | None = None,
    dob: str | None = None,
    start_date: str | None = None,
    termination_date: str | None = None,
    workplaces: list[str] | None = None,
    primary_workplace: str | None = None,
    email: str | None = None,
    ssn: str | None = None,
    ein: str | None = None,
    default_net_pay_split: str | None = None,
    payment_method_preference: str | None = None,
    address: dict | None = None,
    metadata: str | None = None,
) -> dict:
    """Create a new contractor.

    Args:
        company: The Check company ID.
        type: Contractor type — "individual" or "business".
        first_name: Contractor's first name (or business primary contact's first name).
        middle_name: Contractor's middle name.
        last_name: Contractor's last name (or business primary contact's last name).
        business_name: Business name (for business-type contractors).
        dob: Date of birth (YYYY-MM-DD).
        start_date: Most recent start date of contract (YYYY-MM-DD).
        termination_date: Most recent termination date (YYYY-MM-DD).
        workplaces: List of workplace IDs where the contractor works.
        primary_workplace: Workplace ID of the contractor's primary workplace.
        email: Contractor's email address.
        ssn: Contractor's Social Security Number.
        ein: Contractor's Employer Identification Number (for businesses).
        default_net_pay_split: ID of contractor's default net pay split.
        payment_method_preference: "direct_deposit" or "manual".
        address: Address dict with keys: line1, line2, city, state, postal_code, country.
        metadata: Additional JSON metadata string.
    """
    body: dict = {"company": company}
    if type is not None:
        body["type"] = type
    if first_name is not None:
        body["first_name"] = first_name
    if middle_name is not None:
        body["middle_name"] = middle_name
    if last_name is not None:
        body["last_name"] = last_name
    if business_name is not None:
        body["business_name"] = business_name
    if dob is not None:
        body["dob"] = dob
    if start_date is not None:
        body["start_date"] = start_date
    if termination_date is not None:
        body["termination_date"] = termination_date
    if workplaces is not None:
        body["workplaces"] = workplaces
    if primary_workplace is not None:
        body["primary_workplace"] = primary_workplace
    if email is not None:
        body["email"] = email
    if ssn is not None:
        body["ssn"] = ssn
    if ein is not None:
        body["ein"] = ein
    if default_net_pay_split is not None:
        body["default_net_pay_split"] = default_net_pay_split
    if payment_method_preference is not None:
        body["payment_method_preference"] = payment_method_preference
    if address is not None:
        body["address"] = address
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_post(ctx, "/contractors", data=body)


async def update_contractor(
    ctx: Ctx,
    contractor_id: str,
    type: str | None = None,
    first_name: str | None = None,
    middle_name: str | None = None,
    last_name: str | None = None,
    business_name: str | None = None,
    dob: str | None = None,
    start_date: str | None = None,
    termination_date: str | None = None,
    workplaces: list[str] | None = None,
    primary_workplace: str | None = None,
    email: str | None = None,
    ssn: str | None = None,
    ein: str | None = None,
    default_net_pay_split: str | None = None,
    payment_method_preference: str | None = None,
    address: dict | None = None,
    metadata: str | None = None,
) -> dict:
    """Update an existing contractor.

    Args:
        contractor_id: The Check contractor ID.
        type: Contractor type — "individual" or "business".
        first_name: Contractor's first name.
        middle_name: Contractor's middle name.
        last_name: Contractor's last name.
        business_name: Business name (for business-type contractors).
        dob: Date of birth (YYYY-MM-DD).
        start_date: Most recent start date of contract (YYYY-MM-DD).
        termination_date: Most recent termination date (YYYY-MM-DD).
        workplaces: List of workplace IDs where the contractor works.
        primary_workplace: Workplace ID of the contractor's primary workplace.
        email: Contractor's email address.
        ssn: Contractor's Social Security Number.
        ein: Contractor's Employer Identification Number (for businesses).
        default_net_pay_split: ID of contractor's default net pay split.
        payment_method_preference: "direct_deposit" or "manual".
        address: Address dict with keys: line1, line2, city, state, postal_code, country.
        metadata: Additional JSON metadata string.
    """
    body: dict = {}
    if type is not None:
        body["type"] = type
    if first_name is not None:
        body["first_name"] = first_name
    if middle_name is not None:
        body["middle_name"] = middle_name
    if last_name is not None:
        body["last_name"] = last_name
    if business_name is not None:
        body["business_name"] = business_name
    if dob is not None:
        body["dob"] = dob
    if start_date is not None:
        body["start_date"] = start_date
    if termination_date is not None:
        body["termination_date"] = termination_date
    if workplaces is not None:
        body["workplaces"] = workplaces
    if primary_workplace is not None:
        body["primary_workplace"] = primary_workplace
    if email is not None:
        body["email"] = email
    if ssn is not None:
        body["ssn"] = ssn
    if ein is not None:
        body["ein"] = ein
    if default_net_pay_split is not None:
        body["default_net_pay_split"] = default_net_pay_split
    if payment_method_preference is not None:
        body["payment_method_preference"] = payment_method_preference
    if address is not None:
        body["address"] = address
    if metadata is not None:
        body["metadata"] = metadata
    return await check_api_patch(ctx, f"/contractors/{contractor_id}", data=body)


async def onboard_contractor(ctx: Ctx, contractor_id: str) -> dict:
    """Onboard a contractor, transitioning them to active status.

    Args:
        contractor_id: The Check contractor ID.
    """
    return await check_api_post(ctx, f"/contractors/{contractor_id}/onboard")


async def list_contractor_payments_for_contractor(
    ctx: Ctx,
    contractor_id: str,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List payments for a specific contractor.

    Args:
        contractor_id: The Check contractor ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(
        ctx, f"/contractors/{contractor_id}/payments", params=params or None
    )


async def get_contractor_payment_for_payroll(
    ctx: Ctx, contractor_id: str, payroll_id: str
) -> dict:
    """Get a contractor payment for a specific payroll.

    Args:
        contractor_id: The Check contractor ID.
        payroll_id: The Check payroll ID.
    """
    return await check_api_get(
        ctx, f"/contractors/{contractor_id}/payments/{payroll_id}"
    )


async def list_contractor_forms(
    ctx: Ctx,
    contractor_id: str,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List forms for a contractor.

    Args:
        contractor_id: The Check contractor ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(
        ctx, f"/contractors/{contractor_id}/forms", params=params or None
    )


async def submit_contractor_form(
    ctx: Ctx,
    contractor_id: str,
    form_id: str,
    parameters: list[dict] | None = None,
) -> dict:
    """Submit a contractor form.

    Args:
        contractor_id: The Check contractor ID.
        form_id: The form ID.
        parameters: List of name/value dicts representing form fields.
            Example: [{"name": "field_name", "value": "field_value"}].
    """
    body: dict | None = None
    if parameters is not None:
        body = {"parameters": parameters}
    return await check_api_post(
        ctx, f"/contractors/{contractor_id}/forms/{form_id}/submit", data=body
    )


async def reveal_contractor_ssn(ctx: Ctx, contractor_id: str) -> dict:
    """Reveal the SSN/EIN for a contractor.

    Args:
        contractor_id: The Check contractor ID.
    """
    return await check_api_get(ctx, f"/contractors/{contractor_id}/reveal")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_contractors)
    mcp.add_tool(get_contractor)
    mcp.add_tool(list_contractor_payments_for_contractor)
    mcp.add_tool(get_contractor_payment_for_payroll)
    mcp.add_tool(list_contractor_forms)
    mcp.add_tool(reveal_contractor_ssn)
    if not read_only:
        mcp.add_tool(create_contractor)
        mcp.add_tool(update_contractor)
        mcp.add_tool(onboard_contractor)
        mcp.add_tool(submit_contractor_form)
