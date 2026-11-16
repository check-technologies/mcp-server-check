"""Form filing configuration tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_params,
    check_api_get,
    check_api_list,
    check_api_patch,
)


async def list_form_filing_configs(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List form filing configurations, optionally filtered by company.

    Args:
        company: Filter to configurations belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    return await check_api_list(
        ctx,
        "/form_filing_configs",
        params=build_params(
            company=company,
            limit=limit,
            cursor=cursor,
        ),
    )


async def get_form_filing_config(ctx: Ctx, config_id: str) -> dict:
    """Get details for a specific form filing configuration.

    Returns the full configuration including applicability rules, form metadata,
    and any other configuration settings.

    Args:
        config_id: The Check form filing configuration ID (prefixed with "flc_").
    """
    return await check_api_get(ctx, f"/form_filing_configs/{config_id}")


async def update_form_filing_config(ctx: Ctx, config_id: str, data: dict) -> dict:
    """Update a form filing configuration.

    Updates configuration settings such as applicability rules. The request body
    should contain the fields to update (e.g. applicability_rules, parameters).

    Args:
        config_id: The Check form filing configuration ID (prefixed with "flc_").
        data: Configuration updates to apply.
    """
    return await check_api_patch(ctx, f"/form_filing_configs/{config_id}", data=data)


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_form_filing_configs)
    add_annotated_tool(mcp, get_form_filing_config)
    if not read_only:
        add_annotated_tool(mcp, update_form_filing_config)
