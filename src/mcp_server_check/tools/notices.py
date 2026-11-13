"""Notice tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
    check_api_get,
    check_api_list,
    check_api_post,
)


async def list_notices(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List tax notices submitted through the Notices API.

    Args:
        company: Filter to notices for this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return (default 10, max 100).
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/notices",
        params=build_params(company=company, limit=limit, cursor=cursor),
    )


async def get_notice(ctx: Ctx, notice_id: str) -> dict:
    """Get a single tax notice by ID.

    Args:
        notice_id: The Check notice ID (e.g. "ntc_xxxxx").
    """
    return await check_api_get(ctx, f"/notices/{notice_id}")


async def create_notice(
    ctx: Ctx,
    company: str,
    attachments: list[str],
    description: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Submit a tax notice with one or more file attachments.

    Attachments must be ready file IDs from create_file (purpose "notice").
    Poll get_notice for processing_status: "processing", "processed", or
    "failed".

    Args:
        company: The Check company ID (e.g. "com_xxxxx").
        attachments: One to ten unique file IDs (e.g. "file_xxxxx").
        description: Optional context for Check's triage agent (max 10,000
            characters).
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/notices",
        data=build_body(
            {"company": company, "attachments": attachments},
            description=description,
        ),
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_notices)
    add_annotated_tool(mcp, get_notice)
    if not read_only:
        add_annotated_tool(mcp, create_notice)
