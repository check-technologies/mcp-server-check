"""Workplace tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.types import Address
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)


async def list_workplaces(
    ctx: Ctx,
    company: str | None = None,
    limit: int = 500,
    cursor: str | None = None,
) -> dict:
    """List workplaces, optionally filtered by company.

    Args:
        company: Filter to workplaces belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return (max 500, default 500).
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/workplaces",
        params=build_params(company=company, limit=limit, cursor=cursor),
    )


async def get_workplace(ctx: Ctx, workplace_id: str) -> dict:
    """Get details for a specific workplace.

    Args:
        workplace_id: The Check workplace ID (e.g. "wrk_xxxxx").
    """
    return await check_api_get(ctx, f"/workplaces/{workplace_id}")


async def create_workplace(
    ctx: Ctx,
    company: str,
    address: Address,
    name: str | None = None,
    active: bool | None = None,
    metadata: str | None = None,
) -> dict:
    """Create a new workplace.

    Args:
        company: The Check company ID.
        address: Workplace address with keys: line1 (required), line2, city
            (required), state (required), postal_code (required), country.
        name: Human-readable name for the workplace.
        active: Whether the workplace can be associated with employees. Default: true.
        metadata: Additional JSON metadata string.
    """
    return await check_api_post(
        ctx,
        "/workplaces",
        data=build_body(
            {"company": company, "address": address},
            name=name,
            active=active,
            metadata=metadata,
        ),
    )


async def update_workplace(
    ctx: Ctx,
    workplace_id: str,
    company: str | None = None,
    name: str | None = None,
    address: Address | None = None,
    active: bool | None = None,
    metadata: str | None = None,
) -> dict:
    """Update an existing workplace.

    Args:
        workplace_id: The Check workplace ID.
        company: The Check company ID.
        name: Human-readable name for the workplace.
        address: Address with keys: line1, line2, city, state, postal_code, country.
        active: Whether the workplace can be associated with employees.
        metadata: Additional JSON metadata string.
    """
    return await check_api_patch(
        ctx,
        f"/workplaces/{workplace_id}",
        data=build_body(
            {},
            company=company,
            name=name,
            address=address,
            active=active,
            metadata=metadata,
        ),
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_workplaces)
    mcp.add_tool(get_workplace)
    if not read_only:
        mcp.add_tool(create_workplace)
        mcp.add_tool(update_workplace)
