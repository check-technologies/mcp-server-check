"""Agency tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_params,
    check_api_get,
    check_api_list,
)


async def list_agencies(
    ctx: Ctx,
    ids: list[str] | None = None,
    jurisdiction: list[str] | None = None,
    label_contains: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List agencies — the counterparties Check files and remits to.

    An agency (e.g. the IRS or a state revenue department) is the authority
    employers register with and the recipient of payments and filings. Agencies
    are global reference data: the same across all companies and environments.

    Args:
        ids: Agency IDs to look up, for batch lookups (max 500 per request).
        jurisdiction: Filter by lowercase region code(s), e.g. ["fed", "ny"].
            Multiple values are OR'd.
        label_contains: Case-insensitive substring match on the agency label.
        limit: Maximum number of results to return (default 25, max 500).
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx,
        "/agencies",
        params=build_params(
            id=ids,
            jurisdiction=jurisdiction,
            label_contains=label_contains,
            limit=limit,
            cursor=cursor,
        ),
    )


async def get_agency(ctx: Ctx, agency_id: str) -> dict:
    """Get a single agency by ID.

    Args:
        agency_id: The Check agency ID (e.g. "agc_xxxxx").
    """
    return await check_api_get(ctx, f"/agencies/{agency_id}")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_agencies)
    add_annotated_tool(mcp, get_agency)
