"""Employee tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.types import Address, FormParameter
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)


async def list_employees(
    ctx: Ctx,
    company: str | None = None,
    limit: int = 100,
    ids: list[str] | None = None,
    cursor: str | None = None,
    workplace: str | None = None,
    active: bool | None = None,
) -> dict:
    """List employees, optionally filtered by company.

    Args:
        company: Filter to employees belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return (max 100, default 100).
        ids: Filter to specific employee IDs.
        cursor: Pagination cursor from a previous response.
        workplace: Filter by workplace ID(s).
        active: Filter by active status.
    """
    return await check_api_list(
        ctx,
        "/employees",
        params=build_params(
            company=company,
            limit=limit,
            ids=ids,
            cursor=cursor,
            workplace=workplace,
            active=active,
        ),
    )


async def get_employee(ctx: Ctx, employee_id: str) -> dict:
    """Get details for a specific employee.

    Args:
        employee_id: The Check employee ID (e.g. "emp_xxxxx").
    """
    return await check_api_get(ctx, f"/employees/{employee_id}")


async def create_employee(
    ctx: Ctx,
    company: str,
    first_name: str,
    last_name: str,
    middle_name: str | None = None,
    email: str | None = None,
    dob: str | None = None,
    start_date: str | None = None,
    termination_date: str | None = None,
    residence: Address | None = None,
    workplaces: list[str] | None = None,
    primary_workplace: str | None = None,
    ssn: str | None = None,
    payment_method_preference: str | None = None,
    default_net_pay_split: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Create a new employee.

    Args:
        company: The Check company ID the employee belongs to.
        first_name: Employee's first name.
        last_name: Employee's last name.
        middle_name: Employee's middle name.
        email: Employee's email address.
        dob: Date of birth (YYYY-MM-DD).
        start_date: Most recent start date of employment (YYYY-MM-DD).
        termination_date: Most recent termination date (YYYY-MM-DD).
        residence: Residence address with keys: line1, line2, city, state,
            postal_code, country.
        workplaces: List of workplace IDs where the employee works.
        primary_workplace: Workplace ID of the employee's primary workplace.
        ssn: Employee's Social Security Number. Only last four digits available after set.
        payment_method_preference: "direct_deposit" or "manual".
        default_net_pay_split: ID of employee's default net pay split.
        metadata: Additional JSON metadata string.
    """
    return await check_api_post(
        ctx,
        "/employees",
        data=build_body(
            {"company": company, "first_name": first_name, "last_name": last_name},
            middle_name=middle_name,
            email=email,
            dob=dob,
            start_date=start_date,
            termination_date=termination_date,
            residence=residence,
            workplaces=workplaces,
            primary_workplace=primary_workplace,
            ssn=ssn,
            payment_method_preference=payment_method_preference,
            default_net_pay_split=default_net_pay_split,
            metadata=metadata,
        ),
    )


async def update_employee(
    ctx: Ctx,
    employee_id: str,
    first_name: str | None = None,
    middle_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    dob: str | None = None,
    start_date: str | None = None,
    termination_date: str | None = None,
    residence: Address | None = None,
    workplaces: list[str] | None = None,
    primary_workplace: str | None = None,
    ssn: str | None = None,
    payment_method_preference: str | None = None,
    default_net_pay_split: str | None = None,
    metadata: str | None = None,
) -> dict:
    """Update an existing employee.

    Args:
        employee_id: The Check employee ID.
        first_name: Employee's first name.
        middle_name: Employee's middle name.
        last_name: Employee's last name.
        email: Employee's email address.
        dob: Date of birth (YYYY-MM-DD).
        start_date: Most recent start date of employment (YYYY-MM-DD).
        termination_date: Most recent termination date (YYYY-MM-DD).
        residence: Residence address with keys: line1, line2, city, state,
            postal_code, country.
        workplaces: List of workplace IDs where the employee works.
        primary_workplace: Workplace ID of the employee's primary workplace.
        ssn: Employee's Social Security Number.
        payment_method_preference: "direct_deposit" or "manual".
        default_net_pay_split: ID of employee's default net pay split.
        metadata: Additional JSON metadata string.
    """
    return await check_api_patch(
        ctx,
        f"/employees/{employee_id}",
        data=build_body(
            {},
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            dob=dob,
            start_date=start_date,
            termination_date=termination_date,
            residence=residence,
            workplaces=workplaces,
            primary_workplace=primary_workplace,
            ssn=ssn,
            payment_method_preference=payment_method_preference,
            default_net_pay_split=default_net_pay_split,
            metadata=metadata,
        ),
    )


async def onboard_employee(ctx: Ctx, employee_id: str) -> dict:
    """Onboard an employee, transitioning them to active status.

    Args:
        employee_id: The Check employee ID.
    """
    return await check_api_post(ctx, f"/employees/{employee_id}/onboard")


# --- Paystubs ---


async def list_employee_paystubs(
    ctx: Ctx,
    employee_id: str,
    limit: int | None = None,
    cursor: str | None = None,
    payroll: str | None = None,
    status: str | None = None,
    start: str | None = None,
    end: str | None = None,
    type: str | None = None,
) -> dict:
    """List paystubs for an employee.

    Args:
        employee_id: The Check employee ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        payroll: Filter by payroll ID.
        status: Filter by status — "pending", "processing", "failed", or "paid".
        start: Filter to paystubs from payrolls with payday on or after this date (YYYY-MM-DD).
        end: Filter to paystubs from payrolls with payday on or before this date (YYYY-MM-DD).
        type: Filter by payroll type — "regular", "balancing", or "amendment".
    """
    return await check_api_list(
        ctx,
        f"/employees/{employee_id}/paystubs",
        params=build_params(
            limit=limit,
            cursor=cursor,
            payroll=payroll,
            status=status,
            start=start,
            end=end,
            type=type,
        ),
    )


async def get_employee_paystub(ctx: Ctx, employee_id: str, payroll_id: str) -> dict:
    """Get a specific paystub for an employee.

    Args:
        employee_id: The Check employee ID.
        payroll_id: The Check payroll ID.
    """
    return await check_api_get(ctx, f"/employees/{employee_id}/paystubs/{payroll_id}")


# --- Forms ---


async def list_employee_forms(
    ctx: Ctx,
    employee_id: str,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List forms for an employee.

    Args:
        employee_id: The Check employee ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    return await check_api_list(
        ctx,
        f"/employees/{employee_id}/forms",
        params=build_params(limit=limit, cursor=cursor),
    )


async def get_employee_form(ctx: Ctx, employee_id: str, form_id: str) -> dict:
    """Get a specific form for an employee.

    Args:
        employee_id: The Check employee ID.
        form_id: The form ID.
    """
    return await check_api_get(ctx, f"/employees/{employee_id}/forms/{form_id}")


async def submit_employee_form(
    ctx: Ctx,
    employee_id: str,
    form_id: str,
    parameters: list[FormParameter] | None = None,
) -> dict:
    """Submit an employee form.

    Args:
        employee_id: The Check employee ID.
        form_id: The form ID.
        parameters: List of name/value dicts representing form fields.
            Example: [{"name": "field_name", "value": "field_value"}].
    """
    body: dict | None = None
    if parameters is not None:
        body = {"parameters": parameters}
    return await check_api_post(
        ctx, f"/employees/{employee_id}/forms/{form_id}/submit", data=body
    )


async def sign_and_submit_employee_form(
    ctx: Ctx,
    employee_id: str,
    form_id: str,
    parameters: list[FormParameter] | None = None,
) -> dict:
    """Sign and submit an employee form.

    Args:
        employee_id: The Check employee ID.
        form_id: The form ID.
        parameters: List of name/value dicts representing form fields.
            Example: [{"name": "field_name", "value": "field_value"}].
    """
    body: dict | None = None
    if parameters is not None:
        body = {"parameters": parameters}
    return await check_api_post(
        ctx, f"/employees/{employee_id}/forms/{form_id}/sign_and_submit", data=body
    )


# --- Company Defined Attributes ---


async def get_employee_company_defined_attributes(ctx: Ctx, employee_id: str) -> dict:
    """Get company-defined attributes for an employee.

    Args:
        employee_id: The Check employee ID.
    """
    return await check_api_get(
        ctx, f"/employees/{employee_id}/company_defined_attributes"
    )


async def update_employee_company_defined_attributes(
    ctx: Ctx, employee_id: str, data: dict
) -> dict:
    """Update company-defined attributes for an employee.

    The schema is dynamic and defined per-company, so attributes are passed
    as a free-form dict.

    Args:
        employee_id: The Check employee ID.
        data: Attributes to update (schema varies by company configuration).
    """
    return await check_api_patch(
        ctx, f"/employees/{employee_id}/company_defined_attributes", data=data
    )


# --- Reciprocity Elections ---


async def get_employee_reciprocity_elections(ctx: Ctx, employee_id: str) -> dict:
    """Get reciprocity elections for an employee.

    Args:
        employee_id: The Check employee ID.
    """
    return await check_api_get(ctx, f"/employees/{employee_id}/reciprocity_elections")


async def update_employee_reciprocity_elections(
    ctx: Ctx, employee_id: str, data: dict
) -> dict:
    """Update reciprocity elections for an employee.

    Args:
        employee_id: The Check employee ID.
        data: Reciprocity election data (complex nested structure).
    """
    return await check_api_patch(
        ctx, f"/employees/{employee_id}/reciprocity_elections", data=data
    )


# --- Other ---


async def authorize_employee_partner(
    ctx: Ctx, employee_id: str, data: dict | None = None
) -> dict:
    """Authorize a partner for an employee.

    Args:
        employee_id: The Check employee ID.
        data: Partner authorization details.
    """
    return await check_api_post(
        ctx, f"/employees/{employee_id}/authorize_partner", data=data
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_employees)
    mcp.add_tool(get_employee)
    mcp.add_tool(list_employee_paystubs)
    mcp.add_tool(get_employee_paystub)
    mcp.add_tool(list_employee_forms)
    mcp.add_tool(get_employee_form)
    mcp.add_tool(get_employee_company_defined_attributes)
    mcp.add_tool(get_employee_reciprocity_elections)
    if not read_only:
        mcp.add_tool(create_employee)
        mcp.add_tool(update_employee)
        mcp.add_tool(onboard_employee)
        mcp.add_tool(submit_employee_form)
        mcp.add_tool(sign_and_submit_employee_form)
        mcp.add_tool(update_employee_company_defined_attributes)
        mcp.add_tool(update_employee_reciprocity_elections)
        mcp.add_tool(authorize_employee_partner)
