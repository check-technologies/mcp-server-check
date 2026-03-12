"""Form tools for the Check API."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server_check.helpers import (
    Ctx,
    check_api_get,
    check_api_list,
    check_api_post,
)


async def list_forms(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List forms, optionally filtered by company.

    Args:
        company: Filter to forms belonging to this Check company ID (e.g. "com_xxxxx").
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
    return await check_api_list(ctx, "/forms", params=params or None)


async def get_form(ctx: Ctx, form_id: str) -> dict:
    """Get details for a specific form.

    Args:
        form_id: The Check form ID.
    """
    return await check_api_get(ctx, f"/forms/{form_id}")


async def render_form(ctx: Ctx, form_id: str) -> dict:
    """Render a form for display.

    Args:
        form_id: The Check form ID.
    """
    return await check_api_get(ctx, f"/forms/{form_id}/render")


async def validate_form(
    ctx: Ctx,
    form_id: str,
    parameters: list[dict],
) -> dict:
    """Validate form data before submission.

    Args:
        form_id: The Check form ID.
        parameters: List of name/value dicts representing form fields.
            Example: [{"name": "field_name", "value": "field_value"}].
    """
    body: dict = {"parameters": parameters}
    return await check_api_post(ctx, f"/forms/{form_id}/validate", data=body)


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_forms)
    mcp.add_tool(get_form)
    mcp.add_tool(render_form)
    mcp.add_tool(validate_form)
