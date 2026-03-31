"""Document tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
    check_api_get,
    check_api_list,
    check_api_post,
)


# --- Company Tax Documents ---


async def list_company_tax_documents(
    ctx: Ctx,
    limit: int | None = None,
    cursor: str | None = None,
    company: str | None = None,
    year: int | None = None,
    quarter: str | None = None,
) -> dict:
    """List company tax documents.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        company: Filter by company ID.
        year: Filter by tax year.
        quarter: Filter by tax quarter.
    """
    return await check_api_list(
        ctx,
        "/company_tax_documents",
        params=build_params(
            limit=limit, cursor=cursor, company=company, year=year, quarter=quarter
        ),
    )


async def get_company_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Get a specific company tax document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/company_tax_documents/{document_id}")


async def download_company_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Download a company tax document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/company_tax_documents/{document_id}/download")


# --- Company Authorization Documents ---


async def list_company_authorization_documents(
    ctx: Ctx,
    limit: int | None = None,
    cursor: str | None = None,
    company: str | None = None,
    year: int | None = None,
) -> dict:
    """List company authorization documents.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        company: Filter by company ID.
        year: Filter by year.
    """
    return await check_api_list(
        ctx,
        "/company_authorization_documents",
        params=build_params(limit=limit, cursor=cursor, company=company, year=year),
    )


async def get_company_authorization_document(ctx: Ctx, document_id: str) -> dict:
    """Get a specific company authorization document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/company_authorization_documents/{document_id}")


async def download_company_authorization_document(ctx: Ctx, document_id: str) -> dict:
    """Download a company authorization document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(
        ctx, f"/company_authorization_documents/{document_id}/download"
    )


# --- Employee Tax Documents ---


async def list_employee_tax_documents(
    ctx: Ctx,
    limit: int | None = None,
    cursor: str | None = None,
    employee: str | None = None,
    company: str | None = None,
    year: int | None = None,
) -> dict:
    """List employee tax documents.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        employee: Filter by employee ID.
        company: Filter by company ID.
        year: Filter by tax year.
    """
    return await check_api_list(
        ctx,
        "/employee_tax_documents",
        params=build_params(
            limit=limit, cursor=cursor, employee=employee, company=company, year=year
        ),
    )


async def get_employee_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Get a specific employee tax document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/employee_tax_documents/{document_id}")


async def download_employee_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Download an employee tax document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/employee_tax_documents/{document_id}/download")


# --- Contractor Tax Documents ---


async def list_contractor_tax_documents(
    ctx: Ctx,
    limit: int | None = None,
    cursor: str | None = None,
    contractor: str | None = None,
    company: str | None = None,
    year: int | None = None,
) -> dict:
    """List contractor tax documents.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        contractor: Filter by contractor ID.
        company: Filter by company ID.
        year: Filter by tax year.
    """
    return await check_api_list(
        ctx,
        "/contractor_tax_documents",
        params=build_params(
            limit=limit,
            cursor=cursor,
            contractor=contractor,
            company=company,
            year=year,
        ),
    )


async def get_contractor_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Get a specific contractor tax document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/contractor_tax_documents/{document_id}")


async def download_contractor_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Download a contractor tax document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/contractor_tax_documents/{document_id}/download")


# --- Setup Documents ---


async def list_setup_documents(
    ctx: Ctx,
    limit: int | None = None,
    cursor: str | None = None,
    company: str | None = None,
) -> dict:
    """List setup documents.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        company: Filter by company ID.
    """
    return await check_api_list(
        ctx,
        "/setup_documents",
        params=build_params(limit=limit, cursor=cursor, company=company),
    )


async def get_setup_document(ctx: Ctx, document_id: str) -> dict:
    """Get a specific setup document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/setup_documents/{document_id}")


async def download_setup_document(ctx: Ctx, document_id: str) -> dict:
    """Download a setup document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/setup_documents/{document_id}/download")


# --- Company Provided Documents ---


async def list_company_provided_documents(
    ctx: Ctx,
    limit: int | None = None,
    cursor: str | None = None,
    company: str | None = None,
) -> dict:
    """List company-provided documents.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        company: Filter by company ID.
    """
    return await check_api_list(
        ctx,
        "/company_provided_documents",
        params=build_params(limit=limit, cursor=cursor, company=company),
    )


async def get_company_provided_document(ctx: Ctx, document_id: str) -> dict:
    """Get a specific company-provided document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/company_provided_documents/{document_id}")


async def create_company_provided_document(
    ctx: Ctx,
    company: str,
    document_type: str | None = None,
) -> dict:
    """Create a company-provided document.

    Args:
        company: The Check company ID.
        document_type: Type of document — one of "940", "941", "943", "944", "945",
            "cp_575", "147_c", "signatory_photo_id", "voided_check", "bank_statement",
            "ss4", "bank_account_owner_id", "bank_letter", "profit_and_loss",
            "cash_flow_statement", "balance_sheet", "articles_of_incorporation",
            "articles_of_incorporation_signatory_amendment", "state_registration".
    """
    return await check_api_post(
        ctx,
        "/company_provided_documents",
        data=build_body({"company": company}, document_type=document_type),
    )


async def upload_company_provided_document_file(
    ctx: Ctx, document_id: str, data: dict | None = None
) -> dict:
    """Upload a file for a company-provided document.

    Args:
        document_id: The document ID.
        data: Upload metadata.
    """
    return await check_api_post(
        ctx, f"/company_provided_documents/{document_id}/upload", data=data
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    # Company Tax Documents
    mcp.add_tool(list_company_tax_documents)
    mcp.add_tool(get_company_tax_document)
    mcp.add_tool(download_company_tax_document)
    # Company Authorization Documents
    mcp.add_tool(list_company_authorization_documents)
    mcp.add_tool(get_company_authorization_document)
    mcp.add_tool(download_company_authorization_document)
    # Employee Tax Documents
    mcp.add_tool(list_employee_tax_documents)
    mcp.add_tool(get_employee_tax_document)
    mcp.add_tool(download_employee_tax_document)
    # Contractor Tax Documents
    mcp.add_tool(list_contractor_tax_documents)
    mcp.add_tool(get_contractor_tax_document)
    mcp.add_tool(download_contractor_tax_document)
    # Setup Documents
    mcp.add_tool(list_setup_documents)
    mcp.add_tool(get_setup_document)
    mcp.add_tool(download_setup_document)
    # Company Provided Documents
    mcp.add_tool(list_company_provided_documents)
    mcp.add_tool(get_company_provided_document)
    if not read_only:
        mcp.add_tool(create_company_provided_document)
        mcp.add_tool(upload_company_provided_document_file)
