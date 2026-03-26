"""Tax tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.helpers import (
    Ctx,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)


# --- Company Tax Params ---


async def get_company_tax_params(ctx: Ctx, company_id: str) -> dict:
    """Get tax parameters for a company.

    Args:
        company_id: The Check company ID.
    """
    return await check_api_get(ctx, f"/company_tax_params/{company_id}")


async def update_company_tax_params(
    ctx: Ctx, company_id: str, data: list[dict]
) -> dict:
    """Update tax parameters for a company.

    The request body must be a JSON array of tax parameter updates. Each item
    requires an ``id`` (the ``spa_*`` tax parameter ID) and optionally
    ``value``, ``applied_for``, and ``effective_start``.

    Example::

        [
            {"id": "spa_abc123", "value": "123456789"},
            {"id": "spa_def456", "value": "2.43", "effective_start": "2026-01-01"}
        ]

    Args:
        company_id: The Check company ID.
        data: List of tax parameter update objects, each with ``id`` and ``value``.
    """
    return await check_api_patch(ctx, f"/company_tax_params/{company_id}", data=data)


async def list_company_tax_param_settings(
    ctx: Ctx,
    company_id: str,
    limit: int | None = None,
    cursor: str | None = None,
    as_of: str | None = None,
    jurisdiction: str | None = None,
    submitter: str | None = None,
) -> dict:
    """List tax parameter settings for a company.

    Args:
        company_id: The Check company ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        as_of: Filter as of a specific date (YYYY-MM-DD).
        jurisdiction: Filter by tax jurisdiction.
        submitter: Filter by submitter.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    if as_of is not None:
        params["as_of"] = as_of
    if jurisdiction is not None:
        params["jurisdiction"] = jurisdiction
    if submitter is not None:
        params["submitter"] = submitter
    return await check_api_list(
        ctx, f"/company_tax_params/{company_id}/settings", params=params or None
    )


async def get_company_tax_param_setting(
    ctx: Ctx, company_id: str, setting_id: str
) -> dict:
    """Get a specific tax parameter setting for a company.

    Args:
        company_id: The Check company ID.
        setting_id: The tax parameter setting ID.
    """
    return await check_api_get(
        ctx, f"/company_tax_params/{company_id}/settings/{setting_id}"
    )


async def list_company_jurisdictions(
    ctx: Ctx,
    company_id: str,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List tax jurisdictions for a company.

    Args:
        company_id: The Check company ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(
        ctx, f"/company_tax_params/{company_id}/jurisdictions", params=params or None
    )


# --- Employee Tax Params ---


async def list_employee_tax_params(
    ctx: Ctx,
    employee: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    company: str | None = None,
    as_of: str | None = None,
    jurisdiction: str | None = None,
    submitter: str | None = None,
) -> dict:
    """List employee tax parameters, optionally filtered by employee.

    Args:
        employee: Filter to tax parameters for this Check employee ID (e.g. "emp_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        company: Filter by company ID.
        as_of: Filter as of a specific date (YYYY-MM-DD).
        jurisdiction: Filter by tax jurisdiction.
        submitter: Filter by submitter.
    """
    params: dict = {}
    if employee is not None:
        params["employee"] = employee
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    if company is not None:
        params["company"] = company
    if as_of is not None:
        params["as_of"] = as_of
    if jurisdiction is not None:
        params["jurisdiction"] = jurisdiction
    if submitter is not None:
        params["submitter"] = submitter
    return await check_api_list(ctx, "/employee_tax_params", params=params or None)


async def get_employee_tax_params(ctx: Ctx, employee_id: str) -> dict:
    """Get tax parameters for a specific employee.

    Args:
        employee_id: The Check employee ID.
    """
    return await check_api_get(ctx, f"/employee_tax_params/{employee_id}")


async def update_employee_tax_params(
    ctx: Ctx, employee_id: str, data: list[dict]
) -> dict:
    """Update tax parameters for an employee.

    The request body must be a JSON array of tax parameter updates. Each item
    requires an ``id`` (the ``spa_*`` tax parameter ID) and optionally
    ``value``, ``applied_for``, and ``effective_start``.

    Example::

        [
            {"id": "spa_abc123", "value": "S"},
            {"id": "spa_def456", "value": "2000", "effective_start": "2026-01-01"}
        ]

    Args:
        employee_id: The Check employee ID.
        data: List of tax parameter update objects, each with ``id`` and ``value``.
    """
    return await check_api_patch(ctx, f"/employee_tax_params/{employee_id}", data=data)


async def list_employee_tax_param_settings(
    ctx: Ctx,
    employee_id: str,
    limit: int | None = None,
    cursor: str | None = None,
    as_of: str | None = None,
    jurisdiction: str | None = None,
    submitter: str | None = None,
) -> dict:
    """List tax parameter settings for an employee.

    Args:
        employee_id: The Check employee ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        as_of: Filter as of a specific date (YYYY-MM-DD).
        jurisdiction: Filter by tax jurisdiction.
        submitter: Filter by submitter.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    if as_of is not None:
        params["as_of"] = as_of
    if jurisdiction is not None:
        params["jurisdiction"] = jurisdiction
    if submitter is not None:
        params["submitter"] = submitter
    return await check_api_list(
        ctx, f"/employee_tax_params/{employee_id}/settings", params=params or None
    )


async def get_employee_tax_param_setting(
    ctx: Ctx, employee_id: str, setting_id: str
) -> dict:
    """Get a specific tax parameter setting for an employee.

    Args:
        employee_id: The Check employee ID.
        setting_id: The tax parameter setting ID.
    """
    return await check_api_get(
        ctx, f"/employee_tax_params/{employee_id}/settings/{setting_id}"
    )


async def list_employee_jurisdictions(
    ctx: Ctx,
    employee_id: str,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List tax jurisdictions for an employee.

    Args:
        employee_id: The Check employee ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(
        ctx, f"/employee_tax_params/{employee_id}/jurisdictions", params=params or None
    )


async def bulk_get_employee_tax_param_settings(ctx: Ctx, data: dict) -> dict:
    """Bulk get employee tax parameter settings.

    The payload is a complex bulk structure — pass the full request body as a dict.

    Args:
        data: Bulk request payload with employee IDs or filters.
    """
    return await check_api_post(ctx, "/employee_tax_param_settings/bulk_get", data=data)


async def bulk_update_employee_tax_param_settings(ctx: Ctx, data: dict) -> dict:
    """Bulk update employee tax parameter settings.

    The payload is a complex bulk structure — pass the full request body as a dict.

    Args:
        data: Bulk update payload with settings to update.
    """
    return await check_api_post(
        ctx, "/employee_tax_param_settings/bulk_update", data=data
    )


# --- Company Tax Elections ---


async def list_company_tax_elections(
    ctx: Ctx,
    company_id: str,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List tax elections for a company.

    Args:
        company_id: The Check company ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(
        ctx, f"/companies/{company_id}/tax_elections", params=params or None
    )


async def create_company_tax_elections(ctx: Ctx, company_id: str, data: dict) -> dict:
    """Create tax elections for a company.

    The payload is a complex nested structure — pass the full request body as a dict.

    Args:
        company_id: The Check company ID.
        data: Tax election data.
    """
    return await check_api_post(
        ctx, f"/companies/{company_id}/tax_elections", data=data
    )


async def update_company_tax_elections(ctx: Ctx, company_id: str, data: dict) -> dict:
    """Update tax elections for a company.

    The payload is a complex nested structure — pass the full request body as a dict.

    Args:
        company_id: The Check company ID.
        data: Tax election fields to update.
    """
    return await check_api_patch(
        ctx, f"/companies/{company_id}/tax_elections", data=data
    )


# --- Employee Tax Elections ---


async def list_employee_tax_elections(
    ctx: Ctx,
    employee_id: str,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List tax elections for an employee.

    Args:
        employee_id: The Check employee ID.
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    return await check_api_list(
        ctx, f"/employees/{employee_id}/tax_elections", params=params or None
    )


async def update_employee_tax_elections(ctx: Ctx, employee_id: str, data: dict) -> dict:
    """Update tax elections for an employee.

    The payload is a complex nested structure — pass the full request body as a dict.

    Args:
        employee_id: The Check employee ID.
        data: Tax election fields to update.
    """
    return await check_api_patch(
        ctx, f"/employees/{employee_id}/tax_elections", data=data
    )


# --- Tax Filings ---


async def list_tax_filings(
    ctx: Ctx,
    company: str | None = None,
    limit: int = 500,
    cursor: str | None = None,
    year: int | None = None,
    period: str | None = None,
) -> dict:
    """List tax filings, optionally filtered by company.

    Args:
        company: Filter to tax filings belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return (default 500, max 500).
        cursor: Pagination cursor.
        year: Filter by tax year.
        period: Filter by filing period.
    """
    params: dict = {}
    if company is not None:
        params["company"] = company
    params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    if year is not None:
        params["year"] = year
    if period is not None:
        params["period"] = period
    return await check_api_list(ctx, "/tax_filings", params=params or None)


async def get_tax_filing(ctx: Ctx, tax_filing_id: str) -> dict:
    """Get details for a specific tax filing.

    Args:
        tax_filing_id: The Check tax filing ID.
    """
    return await check_api_get(ctx, f"/tax_filings/{tax_filing_id}")


async def request_tax_filing_refile(ctx: Ctx, tax_filing_id: str) -> dict:
    """Request a refile for a tax filing.

    Args:
        tax_filing_id: The Check tax filing ID.
    """
    return await check_api_post(ctx, f"/tax_filings/{tax_filing_id}/request_refile")


# --- Tax Filing Events ---


async def get_tax_filing_event(ctx: Ctx, event_id: str) -> dict:
    """Get a specific tax filing event.

    Args:
        event_id: The tax filing event ID.
    """
    return await check_api_get(ctx, f"/tax_filing_events/{event_id}")


# --- Exempt Status ---


async def get_exempt_status(ctx: Ctx, employee_id: str) -> dict:
    """Get exempt status for an employee.

    Args:
        employee_id: The Check employee ID.
    """
    return await check_api_get(ctx, f"/employees/{employee_id}/exempt_status")


async def update_exempt_status(ctx: Ctx, employee_id: str, data: dict) -> dict:
    """Update exempt status for an employee.

    The payload is a complex structure — pass the full request body as a dict.

    Args:
        employee_id: The Check employee ID.
        data: Exempt status fields to update.
    """
    return await check_api_patch(
        ctx, f"/employees/{employee_id}/exempt_status", data=data
    )


# --- Exemptible Taxes ---


async def list_exemptible_taxes(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List exemptible taxes, optionally filtered by company.

    Args:
        company: Filter to exemptible taxes belonging to this Check company ID (e.g. "com_xxxxx").
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
    return await check_api_list(ctx, "/exemptible_taxes", params=params or None)


async def update_exemptible_tax(ctx: Ctx, tax_id: str, data: dict) -> dict:
    """Update an exemptible tax.

    The payload is a complex structure — pass the full request body as a dict.

    Args:
        tax_id: The exemptible tax ID.
        data: Fields to update.
    """
    return await check_api_patch(ctx, f"/exemptible_taxes/{tax_id}", data=data)


async def bulk_update_exemptible_taxes(ctx: Ctx, data: dict) -> dict:
    """Bulk update exemptible taxes.

    The payload is a complex bulk structure — pass the full request body as a dict.

    Args:
        data: Bulk update payload.
    """
    return await check_api_patch(ctx, "/exemptible_taxes", data=data)


# --- Employee Tax Statements ---


async def list_employee_tax_statements(
    ctx: Ctx,
    employee: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    company: str | None = None,
    year: int | None = None,
) -> dict:
    """List employee tax statements, optionally filtered by employee.

    Args:
        employee: Filter to tax statements for this Check employee ID (e.g. "emp_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        company: Filter by company ID.
        year: Filter by tax year.
    """
    params: dict = {}
    if employee is not None:
        params["employee"] = employee
    if limit is not None:
        params["limit"] = limit
    if cursor:
        params["cursor"] = cursor
    if company is not None:
        params["company"] = company
    if year is not None:
        params["year"] = year
    return await check_api_list(ctx, "/employee_tax_statements", params=params or None)


async def get_employee_tax_statement(ctx: Ctx, statement_id: str) -> dict:
    """Get a specific employee tax statement.

    Args:
        statement_id: The tax statement ID.
    """
    return await check_api_get(ctx, f"/employee_tax_statements/{statement_id}")


# --- Tax Packages ---


async def request_tax_package(
    ctx: Ctx,
    company: str,
    contents: str | None = None,
) -> dict:
    """Request a tax package.

    Args:
        company: The Check company ID.
        contents: JSON string of employee_tax_statements IDs to generate.
    """
    body: dict = {"company": company}
    if contents is not None:
        body["contents"] = contents
    return await check_api_post(ctx, "/tax_packages", data=body)


async def get_tax_package(ctx: Ctx, tax_package_id: str) -> dict:
    """Get a specific tax package.

    Args:
        tax_package_id: The tax package ID.
    """
    return await check_api_get(ctx, f"/tax_packages/{tax_package_id}")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    # Company Tax Params
    mcp.add_tool(get_company_tax_params)
    mcp.add_tool(list_company_tax_param_settings)
    mcp.add_tool(get_company_tax_param_setting)
    mcp.add_tool(list_company_jurisdictions)
    # Employee Tax Params
    mcp.add_tool(list_employee_tax_params)
    mcp.add_tool(get_employee_tax_params)
    mcp.add_tool(list_employee_tax_param_settings)
    mcp.add_tool(get_employee_tax_param_setting)
    mcp.add_tool(list_employee_jurisdictions)
    mcp.add_tool(bulk_get_employee_tax_param_settings)
    # Company Tax Elections
    mcp.add_tool(list_company_tax_elections)
    # Employee Tax Elections
    mcp.add_tool(list_employee_tax_elections)
    # Tax Filings
    mcp.add_tool(list_tax_filings)
    mcp.add_tool(get_tax_filing)
    # Tax Filing Events
    mcp.add_tool(get_tax_filing_event)
    # Exempt Status
    mcp.add_tool(get_exempt_status)
    # Exemptible Taxes
    mcp.add_tool(list_exemptible_taxes)
    # Employee Tax Statements
    mcp.add_tool(list_employee_tax_statements)
    mcp.add_tool(get_employee_tax_statement)
    # Tax Packages
    mcp.add_tool(get_tax_package)
    if not read_only:
        mcp.add_tool(update_company_tax_params)
        mcp.add_tool(update_employee_tax_params)
        mcp.add_tool(bulk_update_employee_tax_param_settings)
        mcp.add_tool(create_company_tax_elections)
        mcp.add_tool(update_company_tax_elections)
        mcp.add_tool(update_employee_tax_elections)
        mcp.add_tool(request_tax_filing_refile)
        mcp.add_tool(update_exempt_status)
        mcp.add_tool(update_exemptible_tax)
        mcp.add_tool(bulk_update_exemptible_taxes)
        mcp.add_tool(request_tax_package)
