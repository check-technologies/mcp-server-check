"""Document tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
    check_api_download,
    check_api_get,
    check_api_list,
    check_api_post,
)


# Setup document types whose files carry unmasked SSNs and bank numbers.
SENSITIVE_SETUP_DOCUMENT_PREFIX = "sensitive_"


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
        "/documents/company_tax_documents",
        params=build_params(
            limit=limit, cursor=cursor, company=company, year=year, quarter=quarter
        ),
    )


async def get_company_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Get a specific company tax document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/documents/company_tax_documents/{document_id}")


async def download_company_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Download a company tax document and return its contents.

    The file comes back as text: a PDF as its text layer page by page, a CSV
    as-is. Long files are cut at the download limit with ``truncated`` set
    and a ``note`` saying what was left out.

    Args:
        document_id: The document ID.
    """
    return await check_api_download(
        ctx, f"/documents/company_tax_documents/{document_id}/download"
    )


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
        "/documents/company_authorization_documents",
        params=build_params(limit=limit, cursor=cursor, company=company, year=year),
    )


async def get_company_authorization_document(ctx: Ctx, document_id: str) -> dict:
    """Get a specific company authorization document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(
        ctx, f"/documents/company_authorization_documents/{document_id}"
    )


async def download_company_authorization_document(ctx: Ctx, document_id: str) -> dict:
    """Download a company authorization document and return its contents.

    The file comes back as text: a PDF as its text layer page by page, a CSV
    as-is. Long files are cut at the download limit with ``truncated`` set
    and a ``note`` saying what was left out.

    Args:
        document_id: The document ID.
    """
    return await check_api_download(
        ctx, f"/documents/company_authorization_documents/{document_id}/download"
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
        "/documents/employee_tax_documents",
        params=build_params(
            limit=limit, cursor=cursor, employee=employee, company=company, year=year
        ),
    )


async def get_employee_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Get a specific employee tax document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/documents/employee_tax_documents/{document_id}")


async def download_employee_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Download an employee tax document and return its contents.

    The file comes back as text: a PDF as its text layer page by page, a CSV
    as-is. Long files are cut at the download limit with ``truncated`` set
    and a ``note`` saying what was left out.

    Args:
        document_id: The document ID.
    """
    return await check_api_download(
        ctx, f"/documents/employee_tax_documents/{document_id}/download"
    )


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
        "/documents/contractor_tax_documents",
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
    return await check_api_get(
        ctx, f"/documents/contractor_tax_documents/{document_id}"
    )


async def download_contractor_tax_document(ctx: Ctx, document_id: str) -> dict:
    """Download a contractor tax document and return its contents.

    The file comes back as text: a PDF as its text layer page by page, a CSV
    as-is. Long files are cut at the download limit with ``truncated`` set
    and a ``note`` saying what was left out.

    Args:
        document_id: The document ID.
    """
    return await check_api_download(
        ctx, f"/documents/contractor_tax_documents/{document_id}/download"
    )


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
        "/documents/setup_documents",
        params=build_params(limit=limit, cursor=cursor, company=company),
    )


async def get_setup_document(ctx: Ctx, document_id: str) -> dict:
    """Get a specific setup document.

    Args:
        document_id: The document ID.
    """
    return await check_api_get(ctx, f"/documents/setup_documents/{document_id}")


async def download_setup_document(ctx: Ctx, document_id: str) -> dict:
    """Download a setup document and return its contents.

    The file comes back as text: a PDF as its text layer page by page, a CSV
    as-is. Long files are cut at the download limit with ``truncated`` set
    and a ``note`` saying what was left out.

    The ``sensitive_*`` setup documents (sensitive_employee_setup,
    sensitive_contractor_setup, sensitive_bank_account_setup) hold unmasked
    SSNs and bank account numbers and are refused; every other document type,
    including the HLD report, is readable.

    Args:
        document_id: The document ID.
    """
    document = await check_api_get(ctx, f"/documents/setup_documents/{document_id}")
    if document.get("error"):
        return document
    document_type = document.get("document_type") or ""
    if document_type.startswith(SENSITIVE_SETUP_DOCUMENT_PREFIX):
        return {
            "error": True,
            "document_type": document_type,
            "detail": (
                f"Setup documents of type {document_type!r} hold unmasked SSNs "
                "and bank account numbers and are not available through the "
                "MCP. Use get_setup_document for the document's metadata."
            ),
        }
    return await check_api_download(
        ctx, f"/documents/setup_documents/{document_id}/download"
    )


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
    idempotency_key: str | None = None,
) -> dict:
    """Create a company-provided document.

    Args:
        company: The Check company ID.
        document_type: Type of document — one of "940", "941", "943", "944", "945",
            "cp_575", "147_c", "signatory_photo_id", "voided_check", "bank_statement",
            "ss4", "bank_account_owner_id", "bank_letter", "profit_and_loss",
            "cash_flow_statement", "balance_sheet", "articles_of_incorporation",
            "articles_of_incorporation_signatory_amendment", "state_registration".
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/company_provided_documents",
        data=build_body({"company": company}, document_type=document_type),
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
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
    add_annotated_tool(mcp, list_company_tax_documents)
    add_annotated_tool(mcp, get_company_tax_document)
    add_annotated_tool(mcp, download_company_tax_document)
    # Company Authorization Documents
    add_annotated_tool(mcp, list_company_authorization_documents)
    add_annotated_tool(mcp, get_company_authorization_document)
    add_annotated_tool(mcp, download_company_authorization_document)
    # Employee Tax Documents
    add_annotated_tool(mcp, list_employee_tax_documents)
    add_annotated_tool(mcp, get_employee_tax_document)
    add_annotated_tool(mcp, download_employee_tax_document)
    # Contractor Tax Documents
    add_annotated_tool(mcp, list_contractor_tax_documents)
    add_annotated_tool(mcp, get_contractor_tax_document)
    add_annotated_tool(mcp, download_contractor_tax_document)
    # Setup Documents
    add_annotated_tool(mcp, list_setup_documents)
    add_annotated_tool(mcp, get_setup_document)
    add_annotated_tool(mcp, download_setup_document)
    # Company Provided Documents
    add_annotated_tool(mcp, list_company_provided_documents)
    add_annotated_tool(mcp, get_company_provided_document)
    if not read_only:
        add_annotated_tool(mcp, create_company_provided_document)
        add_annotated_tool(mcp, upload_company_provided_document_file)
