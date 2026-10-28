"""Tax tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.types import TaxParamUpdate
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
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List a company's tax exemptions (tax elections) for employer-paid taxes — FUTA/SUI unemployment, employer Social Security/Medicare, workers' comp; check this before escalating a company exemption (e.g. a church/nonprofit unemployment exemption) to Check Support.

    Each result is a tax election (``txe_*``) with the ``tax`` ID, its
    ``description``, an ``exemptible`` flag, and a ``setting`` object holding
    the current ``exempt`` value and its effective dates (``setting_timeline``
    has the history). Use it to answer "is this company exempt from X?" and to
    find the ``txe_*`` ID to pass to update_company_tax_elections.

    ``exemptible: true`` means the partner can set the exemption directly with
    update_company_tax_elections. ``exemptible: false`` means the exemption
    cannot be set through the API and only Check Support can apply it — this
    is the case for state unemployment (SUI) and FUTA exemptions, so for those
    report the current setting and draft a support request instead of
    attempting an update.

    A minister's/clergy Social Security and Medicare (FICA) exemption is set
    per employee — including the employer halves — with
    update_employee_tax_elections, not here.

    Results are paginated. When ``next`` is non-null in the response, pass it
    back as ``cursor`` to fetch the following page — required to enumerate
    companies with many elections (e.g. heavy PA/OH local tax exposure), which
    span more than one page.

    Args:
        company: Filter to this Check company ID (e.g. "com_xxxxx").
        tax: Filter to this Check tax ID (e.g. "tax_xxxxx").
        as_of: Return elections applicable on this date (defaults to today).
        exemptible: If true, only return taxes whose exemption the partner can set via the API (exemptible); if false, only taxes that require Check Support to exempt.
        jurisdiction: Filter by region code (e.g. "fed", "ny", "pa").
        limit: Maximum number of results to return per page.
        cursor: Pagination cursor from a previous response's ``next`` field.
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
            limit=limit,
            cursor=cursor,
        ),
    )


async def create_company_tax_elections(
    ctx: Ctx, data: list[dict], idempotency_key: str | None = None
) -> dict:
    """Create company tax exemptions (tax elections) for employer-paid taxes when no election exists yet; prefer update_company_tax_elections for existing ones.

    The request body is a JSON array of tax elections. Each item requires
    ``id`` (the ``txe_*`` tax election ID) and ``company`` (the ``com_*``
    company ID), plus a ``setting`` object with ``exempt`` (bool),
    ``effective_start`` (date), and optionally ``effective_end`` (date).

    Only taxes whose election shows ``exemptible: true`` in
    list_company_tax_elections can be set here; the API rejects the rest
    ("Tax ... is not exemptible"), and those (e.g. SUI/FUTA unemployment)
    require a Check Support request.

    Args:
        data: List of tax elections to create, e.g. [{"id": "txe_...", "company": "com_...", "setting": {"exempt": true, "effective_start": "2026-01-01"}}].
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/company_tax_elections",
        data=data,
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


async def update_company_tax_elections(ctx: Ctx, data: list[dict]) -> dict:
    """Set or remove a company's exemption from an employer-paid tax (mark the company exempt or not exempt) — partners can do this directly for taxes whose election shows exemptible: true.

    First call list_company_tax_elections for the company to get the ``txe_*``
    ID of the tax and confirm ``exemptible`` is true. Then send a JSON array
    of updates: each item requires ``id`` (the ``txe_*`` tax election ID) and
    ``company`` (the ``com_*`` company ID), plus a ``setting`` object with
    ``exempt`` (bool), ``effective_start`` (date), and optionally
    ``effective_end`` (date). Set ``exempt: false`` to end an exemption.

    Taxes with ``exemptible: false`` — notably state unemployment (SUI) and
    FUTA, which churches and some nonprofits ask to be exempted from — are
    rejected by the API ("Tax ... is not exemptible") and must be requested
    from Check Support. A minister's Social Security/Medicare (FICA)
    exemption is an employee-level election: use
    update_employee_tax_elections.

    Args:
        data: List of tax election updates, e.g. [{"id": "txe_...", "company": "com_...", "setting": {"exempt": true, "effective_start": "2026-01-01"}}].
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
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List an employee's tax exemptions (tax elections): whether they are exempt from Social Security, Medicare (FICA), federal/state income tax withholding, paid leave, or local taxes — use this to check an employee's exempt status and to find the txe_ ID needed to set an exemption.

    Each result is a tax election (``txe_*``) with the ``tax`` ID, its
    ``description`` (e.g. "Social Security Tax", "Medicare", "Employer Social
    Security Tax"), an ``exemptible`` flag, and a ``setting`` object holding
    the current ``exempt`` value and its effective dates
    (``setting_timeline`` has the history). Employee elections also cover the
    employer halves of Social Security and Medicare, so a minister/clergy
    FICA exemption is handled entirely here.

    ``exemptible: true`` means the partner can set the exemption directly with
    update_employee_tax_elections — no Check Support request is needed.
    ``exemptible: false`` means only Check Support can apply it.

    Results are paginated. When ``next`` is non-null in the response, pass it
    back as ``cursor`` to fetch the following page.

    Args:
        employee: Filter to this Check employee ID (e.g. "emp_xxxxx").
        company: Filter to this Check company ID (e.g. "com_xxxxx").
        tax: Filter to this Check tax ID (e.g. "tax_xxxxx").
        as_of: Return elections applicable on this date (defaults to today).
        exemptible: If true, only return taxes whose exemption the partner can set via the API (exemptible); if false, only taxes that require Check Support to exempt.
        jurisdiction: Filter by region code (e.g. "fed", "ny", "pa").
        limit: Maximum number of results to return per page.
        cursor: Pagination cursor from a previous response's ``next`` field.
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
            limit=limit,
            cursor=cursor,
        ),
    )


async def update_employee_tax_elections(ctx: Ctx, data: list[dict]) -> dict:
    """Set or remove an employee's tax exemption (mark them exempt from Social Security, Medicare/FICA, federal or state income tax withholding, etc.) — e.g. a minister/clergy FICA exemption; partners can do this directly without contacting Check Support.

    Workflow: call list_employee_tax_elections for the employee to get the
    ``txe_*`` ID of each tax to exempt and confirm ``exemptible`` is true, then
    send a JSON array of updates. Each item requires ``id`` (the ``txe_*`` tax
    election ID) and ``employee`` (the ``emp_*`` employee ID), plus a
    ``setting`` object with ``exempt`` (bool), ``effective_start`` (date), and
    optionally ``effective_end`` (date). Set ``exempt: false`` to end an
    exemption.

    A full FICA exemption (e.g. a minister with an approved IRS Form 4361)
    means exempting the employee from Social Security Tax, Medicare,
    Additional Medicare, Employer Social Security Tax, and Employer Medicare
    Tax — all of which appear as employee tax elections and can be updated in
    one call. Taxes whose election shows ``exemptible: false`` are rejected by
    the API ("Tax ... is not exemptible") and must be requested from Check
    Support.

    Args:
        data: List of tax election updates, e.g. [{"id": "txe_...", "employee": "emp_...", "setting": {"exempt": true, "effective_start": "2026-01-01"}}].
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
    correction: str | None = None,
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
        correction: Filter to filings produced by this correction session (e.g. "cor_xxxxx").
            Requires the corrections API for the provider.
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
            correction=correction,
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
    form: str | None = None,
    published_from: str | None = None,
) -> dict:
    """List employee tax statements, optionally filtered by employee.

    Args:
        employee: Filter to tax statements for this Check employee ID (e.g. "emp_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        company: Filter by company ID.
        year: Filter by tax year.
        form: Filter by tax form ("fed_w2" or "vi_w2vi").
        published_from: ISO-8601 datetime lower bound on published_at (inclusive),
            e.g. "2026-01-15T00:00:00Z".
    """
    return await check_api_list(
        ctx,
        "/employee_tax_statements",
        params=build_params(
            employee=employee,
            limit=limit,
            cursor=cursor,
            company=company,
            year=year,
            form=form,
            published_from=published_from,
        ),
    )


async def get_employee_tax_statement(ctx: Ctx, statement_id: str) -> dict:
    """Get a specific employee tax statement.

    Args:
        statement_id: The tax statement ID.
    """
    return await check_api_get(ctx, f"/employee_tax_statements/{statement_id}")


# --- Employee Tax Statement Overrides ---


async def list_employee_tax_statement_overrides(
    ctx: Ctx,
    company: str | None = None,
    employee: str | None = None,
    year: int | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List employee tax statement overrides (W-2 supplement line values).

    Either company or employee is required. Overrides adjust values such as
    qualified overtime compensation and other labeled lines on an employee's
    tax statement for a given year.

    Args:
        company: Filter to overrides for this Check company ID (e.g. "com_xxxxx").
        employee: Filter to overrides for this Check employee ID (e.g. "emp_xxxxx").
        year: Filter by tax year.
        limit: Maximum number of results to return (max 500).
        cursor: Pagination cursor.
    """
    return await check_api_list(
        ctx,
        "/employee_tax_statement_overrides",
        params=build_params(
            company=company,
            employee=employee,
            year=year,
            limit=limit,
            cursor=cursor,
        ),
    )


async def get_employee_tax_statement_override(ctx: Ctx, override_id: str) -> dict:
    """Get a specific employee tax statement override.

    Args:
        override_id: The override ID (e.g. "ets_ovr_xxxxx").
    """
    return await check_api_get(ctx, f"/employee_tax_statement_overrides/{override_id}")


async def create_employee_tax_statement_overrides(
    ctx: Ctx,
    company: str,
    overrides: list[dict],
    idempotency_key: str | None = None,
) -> dict:
    """Create or update employee tax statement overrides (upsert by employee and year).

    The request body requires company and a non-empty overrides array (max 500
    rows). Each row requires employee and year, and may include
    qualified_overtime_compensation (money string or null), other_lines (list
    of objects with label and amount money strings), and metadata. Every row
    applies atomically or none do.

    Args:
        company: The Check company ID (e.g. "com_xxxxx").
        overrides: Override rows to upsert, e.g. [{"employee": "emp_xxxxx",
            "year": 2026, "qualified_overtime_compensation": "900.00",
            "other_lines": [{"label": "PUCC", "amount": "4200.00"}]}].
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/employee_tax_statement_overrides",
        data={"company": company, "overrides": overrides},
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


async def update_employee_tax_statement_override(
    ctx: Ctx,
    override_id: str,
    qualified_overtime_compensation: str | None = None,
    other_lines: list[dict] | None = None,
    metadata: dict | None = None,
) -> dict:
    """Update an employee tax statement override.

    employee and year cannot be changed; delete and create a new override instead.

    Args:
        override_id: The override ID (e.g. "ets_ovr_xxxxx").
        qualified_overtime_compensation: Money string (e.g. "900.00") or null to clear.
        other_lines: List of line objects, each with label (string) and amount
            (money string).
        metadata: Arbitrary key-value metadata for the override.
    """
    return await check_api_patch(
        ctx,
        f"/employee_tax_statement_overrides/{override_id}",
        data=build_body(
            {},
            qualified_overtime_compensation=qualified_overtime_compensation,
            other_lines=other_lines,
            metadata=metadata,
        ),
    )


async def delete_employee_tax_statement_override(ctx: Ctx, override_id: str) -> dict:
    """Delete an employee tax statement override.

    Args:
        override_id: The override ID (e.g. "ets_ovr_xxxxx").
    """
    return await check_api_delete(
        ctx, f"/employee_tax_statement_overrides/{override_id}"
    )


# --- Tax Packages ---


async def request_tax_package(
    ctx: Ctx,
    company: str,
    employee_tax_statements: list[str] | None = None,
    filings: list[str] | None = None,
    statement_csv_format: str | None = None,
) -> dict:
    """Request a tax package.

    Args:
        company: The Check company ID (e.g. "com_xxxxx").
        employee_tax_statements: Employee tax statement IDs to include
            (e.g. ["ets_xxxxx"]).
        filings: Company filing IDs to include employer copies for
            (e.g. ["com_fil_xxxxx"]).
        statement_csv_format: Layout of the statement CSVs in the package.
            One of "standard" (default) or "with_ids" (adds a leading statement
            ID column). The with_ids value requires the provider feature flag
            ENABLE_TAX_PACKAGE_STATEMENT_CSV_IDS.
    """
    contents: dict[str, list[str]] = {}
    if employee_tax_statements is not None:
        contents["employee_tax_statements"] = employee_tax_statements
    if filings is not None:
        contents["filings"] = filings

    return await check_api_post(
        ctx,
        "/tax_packages",
        data=build_body(
            {"company": company},
            contents=contents if contents else None,
            statement_csv_format=statement_csv_format,
        ),
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
    # Employee Tax Params
    add_annotated_tool(mcp, list_employee_tax_params)
    add_annotated_tool(mcp, get_employee_tax_params)
    add_annotated_tool(mcp, list_employee_tax_param_settings)
    add_annotated_tool(mcp, get_employee_tax_param_setting)
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
    # Employee Tax Statement Overrides
    add_annotated_tool(mcp, list_employee_tax_statement_overrides)
    add_annotated_tool(mcp, get_employee_tax_statement_override)
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
        add_annotated_tool(mcp, create_employee_tax_statement_overrides)
        add_annotated_tool(mcp, update_employee_tax_statement_override)
        add_annotated_tool(mcp, delete_employee_tax_statement_override)
        add_annotated_tool(mcp, request_tax_package)
