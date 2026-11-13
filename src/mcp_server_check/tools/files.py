"""File tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    check_api_get,
    check_api_post,
)


async def create_file(
    ctx: Ctx,
    company: str,
    purpose: str,
    filename: str,
    content_type: str,
    size: int,
    idempotency_key: str | None = None,
) -> dict:
    """Declare a file and receive a presigned upload URL.

    After declaring the file, upload the bytes with HTTP PUT to upload_url before
    upload_url_expires_at. Poll get_file until status is ready or failed.

    Args:
        company: The Check company ID (e.g. "com_xxxxx").
        purpose: Why the file exists. Currently only "notice" (tax notice
            attachments).
        filename: Original filename without slashes or control characters (max 255).
        content_type: Declared MIME type — "application/pdf", "image/jpeg", or
            "image/png".
        size: Declared file size in bytes (1 through 25,000,000).
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/files",
        data=build_body(
            {
                "company": company,
                "purpose": purpose,
                "filename": filename,
                "content_type": content_type,
                "size": size,
            }
        ),
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


async def get_file(ctx: Ctx, file_id: str) -> dict:
    """Get a declared file, including upload status and any validation error.

    Args:
        file_id: The Check file ID (e.g. "file_xxxxx").
    """
    return await check_api_get(ctx, f"/files/{file_id}")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, get_file)
    if not read_only:
        add_annotated_tool(mcp, create_file)
