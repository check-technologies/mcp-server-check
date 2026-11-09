"""Company group tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)


async def list_company_groups(
    ctx: Ctx, limit: int | None = None, cursor: str | None = None
) -> dict:
    """List company groups.

    Args:
        limit: Maximum number of results to return.
        cursor: Pagination cursor from a previous response.
    """
    return await check_api_list(
        ctx, "/company_groups", params=build_params(limit=limit, cursor=cursor)
    )


async def get_company_group(ctx: Ctx, company_group_id: str) -> dict:
    """Get a company group, including its companies and users.

    Args:
        company_group_id: The company group ID (e.g. "pcg_xxxxx").
    """
    return await check_api_get(ctx, f"/company_groups/{company_group_id}")


async def create_company_group(
    ctx: Ctx,
    name: str,
    companies: list[str] | None = None,
    users: list[str] | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Create a company group.

    Users in a group see only the group's companies in Console.

    Args:
        name: Name of the company group.
        companies: Check company IDs in the group (e.g. ["com_xxxxx"]).
        users: User IDs in the group (e.g. ["usr_xxxxx"]), from list_users.
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        "/company_groups",
        data=build_body({"name": name}, companies=companies, users=users),
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


async def update_company_group(
    ctx: Ctx,
    company_group_id: str,
    name: str | None = None,
    companies: list[str] | None = None,
    users: list[str] | None = None,
) -> dict:
    """Update a company group.

    A list you send replaces that membership in full, so [] removes every
    member of that kind; a list you omit is left unchanged. To add or remove a few members without restating the rest, use
    add_company_group_companies, remove_company_group_companies,
    add_company_group_users, or remove_company_group_users.

    Args:
        company_group_id: The company group ID (e.g. "pcg_xxxxx").
        name: New name for the company group.
        companies: The complete list of Check company IDs for the group.
        users: The complete list of user IDs for the group (e.g. ["usr_xxxxx"]).
    """
    return await check_api_patch(
        ctx,
        f"/company_groups/{company_group_id}",
        data=build_body({}, name=name, companies=companies, users=users),
    )


async def add_company_group_companies(
    ctx: Ctx,
    company_group_id: str,
    companies: list[str],
    idempotency_key: str | None = None,
) -> dict:
    """Add companies to a company group. Companies already in it are unchanged.

    Args:
        company_group_id: The company group ID (e.g. "pcg_xxxxx").
        companies: Check company IDs to add (e.g. ["com_xxxxx"]).
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        f"/company_groups/{company_group_id}/add_companies",
        data={"companies": companies},
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


async def remove_company_group_companies(
    ctx: Ctx,
    company_group_id: str,
    companies: list[str],
    idempotency_key: str | None = None,
) -> dict:
    """Remove companies from a company group. Companies not in it are ignored.

    Args:
        company_group_id: The company group ID (e.g. "pcg_xxxxx").
        companies: Check company IDs to remove (e.g. ["com_xxxxx"]).
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        f"/company_groups/{company_group_id}/remove_companies",
        data={"companies": companies},
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


async def add_company_group_users(
    ctx: Ctx,
    company_group_id: str,
    users: list[str],
    idempotency_key: str | None = None,
) -> dict:
    """Add users to a company group. Users already in it are unchanged.

    Args:
        company_group_id: The company group ID (e.g. "pcg_xxxxx").
        users: User IDs to add (e.g. ["usr_xxxxx"]), from list_users.
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        f"/company_groups/{company_group_id}/add_users",
        data={"users": users},
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


async def remove_company_group_users(
    ctx: Ctx,
    company_group_id: str,
    users: list[str],
    idempotency_key: str | None = None,
) -> dict:
    """Remove users from a company group. Users not in it are ignored.

    Args:
        company_group_id: The company group ID (e.g. "pcg_xxxxx").
        users: User IDs to remove (e.g. ["usr_xxxxx"]), from list_users.
        idempotency_key: Sent as the X-Idempotency-Key header to make retries safe.
    """
    return await check_api_post(
        ctx,
        f"/company_groups/{company_group_id}/remove_users",
        data={"users": users},
        headers={"X-Idempotency-Key": idempotency_key} if idempotency_key else None,
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_company_groups)
    add_annotated_tool(mcp, get_company_group)
    if not read_only:
        add_annotated_tool(mcp, create_company_group)
        add_annotated_tool(mcp, update_company_group)
        add_annotated_tool(mcp, add_company_group_companies)
        add_annotated_tool(mcp, remove_company_group_companies)
        add_annotated_tool(mcp, add_company_group_users)
        add_annotated_tool(mcp, remove_company_group_users)
