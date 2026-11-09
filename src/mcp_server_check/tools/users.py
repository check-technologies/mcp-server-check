"""User tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_params,
    check_api_get,
    check_api_list,
)


async def list_users(
    ctx: Ctx, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List the Console users visible to your API key.

    Each user carries a stable `usr_` ID, name, email, created_at, and a
    read-only status ("active" or "inactive"). Inactive users are still listed.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx, "/users", params=build_params(limit=limit, cursor=cursor)
    )


async def get_user(ctx: Ctx, user_id: str) -> dict:
    """Get a specific Console user.

    Args:
        user_id: The user ID (e.g. "usr_xxxxx"). A legacy user UUID is also accepted.
    """
    return await check_api_get(ctx, f"/users/{user_id}")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_users)
    add_annotated_tool(mcp, get_user)
