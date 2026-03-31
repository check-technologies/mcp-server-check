"""Form tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.types import FormParameter
from mcp_server_check.helpers import (
    Ctx,
    build_params,
    check_api_get,
    check_api_list,
    check_api_post,
)


async def list_forms(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    state: str | None = None,
    lang: str | None = None,
    type: str | None = None,
) -> dict:
    """List forms, optionally filtered by company.

    Args:
        company: Filter to forms belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
        state: Filter by two-letter state abbreviation.
        lang: Filter by ISO 639-1 language code.
        type: Filter by form type (e.g. "contractor_setup").
    """
    return await check_api_list(
        ctx,
        "/forms",
        params=build_params(
            company=company,
            limit=limit,
            cursor=cursor,
            state=state,
            lang=lang,
            type=type,
        ),
    )


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
    parameters: list[FormParameter],
) -> dict:
    """Validate form data before submission.

    Args:
        form_id: The Check form ID.
        parameters: List of name/value dicts representing form fields.
            Example: [{"name": "field_name", "value": "field_value"}].
    """
    return await check_api_post(
        ctx, f"/forms/{form_id}/validate", data={"parameters": parameters}
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_forms)
    mcp.add_tool(get_form)
    mcp.add_tool(render_form)
    mcp.add_tool(validate_form)
