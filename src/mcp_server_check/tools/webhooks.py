"""Webhook tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.helpers import (
    Ctx,
    build_body,
    build_params,
    check_api_delete,
    check_api_get,
    check_api_list,
    check_api_patch,
    check_api_post,
)


async def list_webhook_configs(
    ctx: Ctx,
    company: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List webhook configurations, optionally filtered by company.

    Args:
        company: Filter to webhook configs belonging to this Check company ID (e.g. "com_xxxxx").
        limit: Maximum number of results to return.
        cursor: Pagination cursor.
    """
    return await check_api_list(
        ctx,
        "/webhook_configs",
        params=build_params(company=company, limit=limit, cursor=cursor),
    )


async def get_webhook_config(ctx: Ctx, webhook_config_id: str) -> dict:
    """Get details for a specific webhook configuration.

    Args:
        webhook_config_id: The Check webhook config ID.
    """
    return await check_api_get(ctx, f"/webhook_configs/{webhook_config_id}")


async def create_webhook_config(ctx: Ctx, url: str) -> dict:
    """Create a new webhook configuration.

    Args:
        url: The webhook endpoint URL.
    """
    return await check_api_post(ctx, "/webhook_configs", data={"url": url})


async def update_webhook_config(
    ctx: Ctx,
    webhook_config_id: str,
    url: str | None = None,
    active: bool | None = None,
) -> dict:
    """Update a webhook configuration.

    Args:
        webhook_config_id: The Check webhook config ID.
        url: The webhook endpoint URL.
        active: Whether the webhook config is active.
    """
    return await check_api_patch(
        ctx,
        f"/webhook_configs/{webhook_config_id}",
        data=build_body({}, url=url, active=active),
    )


async def delete_webhook_config(ctx: Ctx, webhook_config_id: str) -> dict:
    """Delete a webhook configuration.

    Args:
        webhook_config_id: The Check webhook config ID.
    """
    return await check_api_delete(ctx, f"/webhook_configs/{webhook_config_id}")


async def ping_webhook_config(ctx: Ctx, webhook_config_id: str) -> dict:
    """Send a test ping to a webhook configuration.

    Args:
        webhook_config_id: The Check webhook config ID.
    """
    return await check_api_post(ctx, f"/webhook_configs/{webhook_config_id}/ping")


async def retry_webhook_events(ctx: Ctx, data: dict) -> dict:
    """Retry failed webhook events.

    The payload structure varies — pass the full request body as a dict with
    event IDs or filters.

    Args:
        data: Retry configuration (event IDs or filters).
    """
    return await check_api_post(ctx, "/webhook_events/retry", data=data)


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    mcp.add_tool(list_webhook_configs)
    mcp.add_tool(get_webhook_config)
    if not read_only:
        mcp.add_tool(create_webhook_config)
        mcp.add_tool(update_webhook_config)
        mcp.add_tool(delete_webhook_config)
        mcp.add_tool(ping_webhook_config)
        mcp.add_tool(retry_webhook_events)
