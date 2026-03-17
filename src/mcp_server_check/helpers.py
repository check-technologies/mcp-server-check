"""Shared helpers for the Check MCP server."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Sequence
from urllib.parse import parse_qs, urlparse

import httpx
from fastmcp import Context


@dataclass
class CheckContext:
    client: httpx.AsyncClient
    base_url: str
    token_resolver: Callable[[], str] | None = field(default=None, repr=False)


Ctx = Context

# Default max results for list endpoints to avoid blowing context windows.
DEFAULT_LIST_LIMIT = 10

# Fields to keep in summary mode per entity type (by ID prefix or path hint).
# When a list response contains many records, only these fields are returned
# unless the caller explicitly requests full details.
_SUMMARY_FIELDS: dict[str, Sequence[str]] = {
    "com_": ("id", "legal_name", "trade_name", "status", "pay_frequency"),
    "emp_": ("id", "first_name", "last_name", "email", "status", "start_date"),
    "ctr_": ("id", "first_name", "last_name", "business_name", "type", "status"),
    "prl_": (
        "id",
        "status",
        "payday",
        "period_start",
        "period_end",
        "type",
        "approval_status",
    ),
    "pit_": ("id", "employee", "payment_method", "status"),
    "pmt_": ("id", "status", "amount", "payment_method", "direction"),
    "bnk_": ("id", "institution_name", "subtype", "status", "last_four"),
    "wrk_": ("id", "name", "active", "address"),
    "ben_": (
        "id",
        "benefit",
        "description",
        "employee",
        "effective_start",
        "effective_end",
    ),
    "nps_": ("id", "employee", "contractor", "is_default"),
    "psc_": ("id", "name", "pay_frequency", "company"),
}


def _detect_entity_prefix(results: list[dict]) -> str | None:
    """Detect the entity type prefix from the first result's ID."""
    if not results:
        return None
    first_id = results[0].get("id", "")
    if isinstance(first_id, str) and "_" in first_id:
        prefix = first_id.split("_")[0] + "_"
        return prefix
    return None


def _summarize_record(record: dict, fields: Sequence[str]) -> dict:
    """Return only the specified fields from a record."""
    return {k: v for k, v in record.items() if k in fields}


def _summarize_results(results: list[dict]) -> list[dict]:
    """Return summary views of list results to reduce context size.

    If the entity type is recognized (by ID prefix), only key fields are kept.
    Unrecognized entities are returned as-is.
    """
    prefix = _detect_entity_prefix(results)
    if prefix and prefix in _SUMMARY_FIELDS:
        fields = _SUMMARY_FIELDS[prefix]
        return [_summarize_record(r, fields) for r in results]
    return results


def _extract_cursor(url: str | None) -> str | None:
    """Extract the cursor parameter from a Check API pagination URL."""
    if not url:
        return None
    parsed = urlparse(url)
    cursor_values = parse_qs(parsed.query).get("cursor")
    return cursor_values[0] if cursor_values else None


def _format_list_response(data: dict, *, summarize: bool = True) -> dict:
    """Normalize a paginated Check API response.

    Args:
        data: Raw API response dict with results, next, previous.
        summarize: If True, return only key fields per entity to save context.
    """
    results = data.get("results", [])
    formatted_results = _summarize_results(results) if summarize else results
    return {
        "results": formatted_results,
        "result_count": len(results),
        "next_cursor": _extract_cursor(data.get("next")),
        "previous_cursor": _extract_cursor(data.get("previous")),
    }


async def _check_api_request(
    ctx: Ctx,
    method: str,
    path: str,
    params: dict | None = None,
    data: dict | list | None = None,
) -> dict:
    """Make a request to the Check API with shared error handling."""
    check_ctx = ctx.request_context.lifespan_context
    headers: dict[str, str] = {}
    if check_ctx.token_resolver is not None:
        headers["Authorization"] = f"Bearer {check_ctx.token_resolver()}"
    try:
        response = await check_ctx.client.request(
            method, path, params=params, json=data, headers=headers or None
        )
        response.raise_for_status()
        if response.status_code == 204:
            return {"success": True}
        return response.json()
    except httpx.HTTPStatusError as e:
        try:
            error_body = e.response.json()
        except Exception:
            error_body = e.response.text
        return {
            "error": True,
            "status_code": e.response.status_code,
            "detail": error_body,
        }
    except httpx.RequestError as e:
        return {"error": True, "detail": str(e)}


async def check_api_get(ctx: Ctx, path: str, params: dict | None = None) -> dict:
    """Make a GET request to the Check API."""
    return await _check_api_request(ctx, "GET", path, params=params)


async def check_api_post(ctx: Ctx, path: str, data: dict | None = None) -> dict:
    """Make a POST request to the Check API."""
    return await _check_api_request(ctx, "POST", path, data=data)


async def check_api_patch(ctx: Ctx, path: str, data: dict | list) -> dict:
    """Make a PATCH request to the Check API."""
    return await _check_api_request(ctx, "PATCH", path, data=data)


async def check_api_put(ctx: Ctx, path: str, data: dict) -> dict:
    """Make a PUT request to the Check API."""
    return await _check_api_request(ctx, "PUT", path, data=data)


async def check_api_delete(ctx: Ctx, path: str, params: dict | None = None) -> dict:
    """Make a DELETE request to the Check API."""
    return await _check_api_request(ctx, "DELETE", path, params=params)


async def check_api_list(
    ctx: Ctx,
    path: str,
    params: dict | None = None,
    *,
    summarize: bool = True,
) -> dict:
    """GET a list endpoint and return a normalized paginated response.

    Args:
        ctx: MCP context.
        path: API path.
        params: Query parameters.
        summarize: If True (default), return summary views of results.
    """
    data = await check_api_get(ctx, path, params=params)
    if "error" in data:
        return data
    return _format_list_response(data, summarize=summarize)
