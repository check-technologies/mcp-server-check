"""Tax tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.types import TaxParamUpdate
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
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
    ctx: Ctx, company_id: str, data: list[TaxParamUpdate]
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
    return await check_api_list(
        ctx,
        f"/company_tax_params/{company_id}/settings",
        params=build_params(
            limit=limit,
            cursor=cursor,
            as_of=as_of,
            jurisdiction=jurisdiction,
            submitter=submitter,
        ),
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
    return await check_api_list(
        ctx,
        f"/company_tax_params/{company_id}/jurisdictions",
        params=build_params(limit=limit, cursor=cursor),
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
    return await check_api_list(
        ctx,
        "/employee_tax_params",
        params=build_params(
            employee=employee,
            limit=limit,
            cursor=cursor,
            company=company,
            as_of=as_of,
            jurisdiction=jurisdiction,
            submitter=submitter,
        ),
    )


async def get_employee_tax_params(ctx: Ctx, employee_id: str) -> dict:
    """Get tax parameters for a specific employee.

    Args:
        employee_id: The Check employee ID.
    """
    return await check_api_get(ctx, f"/employee_tax_params/{employee_id}")


async def update_employee_tax_params(
    ctx: Ctx, employee_id: str, data: list[TaxParamUpdate]
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
    return await check_api_list(
        ctx,
        f"/employee_tax_params/{employee_id}/settings",
        params=build_params(
            limit=limit,
            cursor=cursor,
            as_of=as_of,
            jurisdiction=jurisdiction,
            submitter=submitter,
        ),
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
    return await check_api_list(
        ctx,
        f"/employee_tax_params/{employee_id}/jurisdictions",
        params=build_params(limit=limit, cursor=cursor),
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
    company: str | None = None,
    tax: str | None = None,
    as_of: str | None = None,
    exemptible: bool | None = None,
    jurisdiction: str | None = None,
) -> dict:
    """List tax elections (exemption settings) for company-paid taxes.

    Tax elections replace the former exempt status and exemptible taxes
    endpoints. Each election has an ``exemptible`` flag and a ``setting``
    object holding the current ``exempt`` value and its effective dates.

    Args:
        company: Filter to this Check company ID (e.g. "com_xxxxx").
        tax: Filter to this Check tax ID (e.g. "tax_xxxxx").
        as_of: Return elections applicable on this date (defaults to today).
        exemptible: If true, only return taxes that qualify for exemption.
        jurisdiction: Filter by region code (e.g. "fed", "ny", "pa").
    """
    return await check_api_list(
        ctx,
        "/company_tax_elections",
        params=build_params(
            company=company,
            tax=tax,
            as_of=as_of,
            exemptible=exemptible,
            jurisdiction=jurisdiction,
        ),
    )


async def create_company_tax_elections(ctx: Ctx, data: list[dict]) -> dict:
    """Create tax elections for a company.

    The request body is a JSON array of tax elections. Each item requires
    ``id`` (the ``txe_*`` tax election ID) and ``company`` (the ``com_*``
    company ID), plus a ``setting`` object with ``exempt`` (bool),
    ``effective_start`` (date), and optionally ``effective_end`` (date).

    Args:
        data: List of tax elections to create.
    """
    return await check_api_post(ctx, "/company_tax_elections", data=data)


async def update_company_tax_elections(ctx: Ctx, data: list[dict]) -> dict:
    """Update tax elections (exemption settings) for a company.

    The request body is a JSON array of tax election updates. Each item
    requires ``id`` (the ``txe_*`` tax election ID) and ``company`` (the
    ``com_*`` company ID), plus a ``setting`` object with ``exempt`` (bool),
    ``effective_start`` (date), and optionally ``effective_end`` (date).

    Args:
        data: List of tax election updates.
    """
    return await check_api_patch(ctx, "/company_tax_elections", data=data)


# --- Employee Tax Elections ---


async def list_employee_tax_elections(
    ctx: Ctx,
    employee: str | None = None,
    company: str | None = None,
    tax: str | None = None,
    as_of: str | None = None,
    exemptible: bool | None = None,
    jurisdiction: str | None = None,
) -> dict:
    """List tax elections (exemption settings) for employee-paid taxes.

    Tax elections replace the former per-employee exempt status endpoint.
    Each election has an ``exemptible`` flag and a ``setting`` object holding
    the current ``exempt`` value and its effective dates.

    Args:
        employee: Filter to this Check employee ID (e.g. "emp_xxxxx").
        company: Filter to this Check company ID (e.g. "com_xxxxx").
        tax: Filter to this Check tax ID (e.g. "tax_xxxxx").
        as_of: Return elections applicable on this date (defaults to today).
        exemptible: If true, only return taxes that qualify for exemption.
        jurisdiction: Filter by region code (e.g. "fed", "ny", "pa").
    """
    return await check_api_list(
        ctx,
        "/employee_tax_elections",
        params=build_params(
            employee=employee,
            company=company,
            tax=tax,
            as_of=as_of,
            exemptible=exemptible,
            jurisdiction=jurisdiction,
        ),
    )


async def update_employee_tax_elections(ctx: Ctx, data: list[dict]) -> dict:
    """Update tax elections (exemption settings) for an employee.

    The request body is a JSON array of tax election updates. Each item
    requires ``id`` (the ``txe_*`` tax election ID) and ``employee`` (the
    ``emp_*`` employee ID), plus a ``setting`` object with ``exempt`` (bool),
    ``effective_start`` (date), and optionally ``effective_end`` (date).

    Args:
        data: List of tax election updates.
    """
    return await check_api_patch(ctx, "/employee_tax_elections", data=data)


# --- Filings ---


async def list_filings(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    year: int | None = None,
    period: str | None = None,
    status: str | None = None,
) -> dict:
    """List filings, optionally filtered by company.

    Returns filing history and expected upcoming filings. Each filing includes
    its current status, status_history, blocked_reasons, and amendment
    relationships.

    Args:
        company: Filter to filings belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return (1-500, default 25).
        cursor: Pagination cursor.
        year: Filter by tax year.
        period: Filter by filing period (e.g. "annual", "q1", "q2", "q3", "q4", "january", etc.).
        status: Filter by filing status ("pending", "blocked", "submitted", "filed", or "inapplicable").
    """
    return await check_api_list(
        ctx,
        "/filings",
        params=build_params(
            company=company,
            limit=limit,
            cursor=cursor,
            year=year,
            period=period,
            status=status,
        ),
    )


async def get_filing(ctx: Ctx, filing_id: str) -> dict:
    """Get details for a specific filing.

    Returns the full filing object including status, status_history,
    blocked_reasons, document, and amendment relationships (amends/amended_by).

    Args:
        filing_id: The Check filing ID (prefixed with "com_fil_").
    """
    return await check_api_get(ctx, f"/filings/{filing_id}")


async def add_filing_blockers(ctx: Ctx, filing_id: str, data: dict) -> dict:
    """Add blockers to a filing.

    In production, you can add the "held_by_customer" blocker to any filing
    with a pending status. This communicates that the employer is not ready
    for this filing to be filed with the agency.

    Args:
        filing_id: The Check filing ID (prefixed with "com_fil_").
        data: Request body with blocked_reasons to add (e.g. {"blocked_reasons": ["held_by_customer"]}).
    """
    return await check_api_post(ctx, f"/filings/{filing_id}/add_blockers", data=data)


async def remove_filing_blockers(ctx: Ctx, filing_id: str, data: dict) -> dict:
    """Remove blockers from a filing.

    Removes eligible blockers from a filing. In production, you can remove
    the "held_by_customer" blocker.

    Args:
        filing_id: The Check filing ID (prefixed with "com_fil_").
        data: Request body with blocked_reasons to remove (e.g. {"blocked_reasons": ["held_by_customer"]}).
    """
    return await check_api_post(ctx, f"/filings/{filing_id}/remove_blockers", data=data)


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
    return await check_api_list(
        ctx,
        "/employee_tax_statements",
        params=build_params(
            employee=employee, limit=limit, cursor=cursor, company=company, year=year
        ),
    )


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
    return await check_api_post(
        ctx, "/tax_packages", data=build_body({"company": company}, contents=contents)
    )


async def get_tax_package(ctx: Ctx, tax_package_id: str) -> dict:
    """Get a specific tax package.

    Args:
        tax_package_id: The tax package ID.
    """
    return await check_api_get(ctx, f"/tax_packages/{tax_package_id}")


# --- Taxes (reference data) ---


async def list_taxes(
    ctx: Ctx,
    ids: list[str] | None = None,
    jurisdiction: list[str] | None = None,
    supported: bool | None = None,
    remittable: bool | None = None,
    effective: bool | None = None,
    label_contains: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List tax objects — the levies that arise when running payroll.

    A tax (e.g. Federal Income Tax, a state's SUI) is global reference data:
    the same across all companies and environments. Distinct from company/
    employee tax *parameters* and *elections*, which configure how a given
    company or employee relates to these taxes.

    Args:
        ids: Tax IDs to look up, for batch lookups (max 500 per request).
        jurisdiction: Filter by lowercase region code(s), e.g. ["fed", "ny"].
            Multiple values are OR'd.
        supported: Filter by whether Check calculates and files the tax.
        remittable: Filter by whether Check remits the tax to the agency.
        effective: Filter by whether the tax obligation is currently in
            effect (defaults to true on the API side).
        label_contains: Case-insensitive substring match on the tax label.
        limit: Maximum number of results to return (default 25, max 500).
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/taxes",
        params=build_params(
            id=ids,
            jurisdiction=jurisdiction,
            supported=supported,
            remittable=remittable,
            effective=effective,
            label_contains=label_contains,
            limit=limit,
            cursor=cursor,
        ),
    )


async def get_tax(ctx: Ctx, tax_id: str) -> dict:
    """Get a single tax object by ID.

    Args:
        tax_id: The Check tax ID (e.g. "tax_xxxxx").
    """
    return await check_api_get(ctx, f"/taxes/{tax_id}")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    # Company Tax Params
    add_annotated_tool(mcp, get_company_tax_params)
    add_annotated_tool(mcp, list_company_tax_param_settings)
    add_annotated_tool(mcp, get_company_tax_param_setting)
    add_annotated_tool(mcp, list_company_jurisdictions)
    # Employee Tax Params
    add_annotated_tool(mcp, list_employee_tax_params)
    add_annotated_tool(mcp, get_employee_tax_params)
    add_annotated_tool(mcp, list_employee_tax_param_settings)
    add_annotated_tool(mcp, get_employee_tax_param_setting)
    add_annotated_tool(mcp, list_employee_jurisdictions)
    add_annotated_tool(mcp, bulk_get_employee_tax_param_settings)
    # Company Tax Elections
    add_annotated_tool(mcp, list_company_tax_elections)
    # Employee Tax Elections
    add_annotated_tool(mcp, list_employee_tax_elections)
    # Filings
    add_annotated_tool(mcp, list_filings)
    add_annotated_tool(mcp, get_filing)
    # Employee Tax Statements
    add_annotated_tool(mcp, list_employee_tax_statements)
    add_annotated_tool(mcp, get_employee_tax_statement)
    # Tax Packages
    add_annotated_tool(mcp, get_tax_package)
    # Taxes (reference data)
    add_annotated_tool(mcp, list_taxes)
    add_annotated_tool(mcp, get_tax)
    if not read_only:
        add_annotated_tool(mcp, update_company_tax_params)
        add_annotated_tool(mcp, update_employee_tax_params)
        add_annotated_tool(mcp, bulk_update_employee_tax_param_settings)
        add_annotated_tool(mcp, create_company_tax_elections)
        add_annotated_tool(mcp, update_company_tax_elections)
        add_annotated_tool(mcp, update_employee_tax_elections)
        add_annotated_tool(mcp, add_filing_blockers)
        add_annotated_tool(mcp, remove_filing_blockers)
        add_annotated_tool(mcp, request_tax_package)
