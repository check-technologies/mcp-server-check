"""Webhook tools for the Check API."""

from __future__ import annotations

import uuid

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
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


async def list_events(
    ctx: Ctx,
    webhook_config: str | None = None,
    company: str | None = None,
    topic: str | None = None,
    status: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List webhook events generated for your provider, newest first, with
    delivery status and embedded delivery attempts.

    Args:
        webhook_config: Filter to events sent to this webhook config (e.g. "whc_xxxxx").
        company: Filter to events associated with this Check company ID (e.g. "com_xxxxx").
        topic: Filter by webhook topic (e.g. "payroll", "employee"); invalid topics
            return a validation error.
        status: Filter by delivery status: "pending", "retrying", "delivered", or "failed".
        created_after: ISO-8601 lower bound on when the event was created.
        created_before: ISO-8601 upper bound on when the event was created.
        limit: Maximum number of results to return (max 100).
        cursor: Pagination cursor.
    """
    return await check_api_list(
        ctx,
        "/events",
        params=build_params(
            webhook_config=webhook_config,
            company=company,
            topic=topic,
            status=status,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            cursor=cursor,
        ),
    )


async def get_event(ctx: Ctx, event_id: str) -> dict:
    """Get a webhook event, including its delivery status and the attempts
    made to deliver it (a null attempt status_code means no HTTP response was
    received — e.g. a timeout or TLS failure).

    Args:
        event_id: The Check webhook event ID (e.g. "whe_xxxxx").
    """
    return await check_api_get(ctx, f"/events/{event_id}")


async def retry_event(ctx: Ctx, event_id: str) -> dict:
    """Re-enqueue a webhook event. Sandbox only — returns a 400 in the live
    environment, where Check's automatic retry schedule handles redelivery.

    Args:
        event_id: The Check webhook event ID (e.g. "whe_xxxxx").
    """
    return await check_api_post(
        ctx,
        f"/events/{event_id}/retry",
        headers={"X-Idempotency-Key": str(uuid.uuid4())},
    )


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_webhook_configs)
    add_annotated_tool(mcp, get_webhook_config)
    add_annotated_tool(mcp, list_events)
    add_annotated_tool(mcp, get_event)
    if not read_only:
        add_annotated_tool(mcp, create_webhook_config)
        add_annotated_tool(mcp, update_webhook_config)
        add_annotated_tool(mcp, delete_webhook_config)
        add_annotated_tool(mcp, ping_webhook_config)
        add_annotated_tool(mcp, retry_event)
