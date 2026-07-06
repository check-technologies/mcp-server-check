"""API request log tools for the Check API."""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_server_check.annotations import add_annotated_tool
from mcp_server_check.helpers import (
    Ctx,
    build_params,
    check_api_get,
    check_api_list,
)


async def list_logs(
    ctx: Ctx,
    limit: int | None = None,
    cursor: str | None = None,
    path: str | None = None,
    method: list[str] | None = None,
    status_code: list[str] | None = None,
    idempotency_key: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
) -> dict:
    """List your API request logs, most recent first.

    Every request made with your API key is recorded — method, path, status
    code, timing, and (PII-scrubbed) request/response bodies. Use this to debug
    an integration, e.g. "yesterday's 400s for the payrolls endpoint". The list
    view is compact; call get_log with an id for the full record (headers, query
    params, bodies).

    Args:
        limit: Maximum number of results to return (default 25, max 100).
        cursor: Pagination cursor from a previous response.
        path: Case-insensitive substring match on the request path
            (e.g. "/payrolls").
        method: Filter by HTTP method(s), e.g. ["GET", "POST"]. Repeated values
            are OR'd.
        status_code: Filter by exact status code(s) and/or class(es). Accepts
            exact codes ("404") and the classes "2xx", "3xx", "4xx", "5xx".
            Multiple values are OR'd, so ["4xx", "500"] returns all 4xx plus 500.
        idempotency_key: Filter to requests sent with this idempotency key.
        created_after: ISO-8601 datetime lower bound on created_at (inclusive),
            e.g. "2026-06-01T00:00:00Z".
        created_before: ISO-8601 datetime upper bound on created_at (inclusive).
    """
    return await check_api_list(
        ctx,
        "/logs",
        params=build_params(
            limit=limit,
            cursor=cursor,
            path=path,
            method=method,
            status_code=status_code,
            idempotency_key=idempotency_key,
            created_after=created_after,
            created_before=created_before,
        ),
    )


async def get_log(ctx: Ctx, log_id: str) -> dict:
    """Get the full record for a single API request log.

    Returns headers, query params, and the (PII-scrubbed) request/response
    bodies in addition to the summary fields. The log id is also returned in the
    ``X-Request-Id`` response header of every API call, so you can go straight
    from a response in hand to its log.

    Args:
        log_id: The Check log ID (e.g. "log_xxxxx").
    """
    return await check_api_get(ctx, f"/logs/{log_id}")


def register(mcp: FastMCP, *, read_only: bool = False) -> None:
    add_annotated_tool(mcp, list_logs)
    add_annotated_tool(mcp, get_log)
