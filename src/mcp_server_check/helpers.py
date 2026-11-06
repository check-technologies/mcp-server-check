"""Shared helpers for the Check MCP server."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from fastmcp import Context

from mcp_server_check.recovery import Failure

try:
    _VERSION = version("mcp-server-check")
except PackageNotFoundError:
    _VERSION = "dev"

_USER_AGENT = f"mcp-server-check/{_VERSION}"


@dataclass
class CheckContext:
    client: httpx.AsyncClient
    base_url: str
    token_resolver: Callable[[], str] | None = field(default=None, repr=False)
    user_agent: str = field(default_factory=lambda: _USER_AGENT)


Ctx = Context

# Default max results for list endpoints to avoid blowing context windows.
DEFAULT_LIST_LIMIT = 10

# Fields to keep in summary mode per entity type (by ID prefix or path hint).
# When a list response contains many records, only these fields are returned
# unless the caller explicitly requests full details.
_SUMMARY_FIELDS: dict[str, Sequence[str]] = {
    "com_": (
        "id",
        "legal_name",
        "trade_name",
        "pay_frequency",
        "onboard",
        "implementation",
    ),
    "emp_": ("id", "first_name", "last_name", "email", "status", "start_date"),
    "ctr_": ("id", "first_name", "last_name", "business_name", "type", "status"),
    "pay_": (
        "id",
        "status",
        "payday",
        "period_start",
        "period_end",
        "type",
        "approval_status",
    ),
    "itm_": ("id", "employee", "payment_method", "status"),
    "pyt_": ("id", "status", "amount", "payment_method", "direction"),
    "bnk_": ("id", "institution_name", "subtype", "status", "last_four"),
    "wrk_": ("id", "name", "active", "address"),
    # Logs carry request/response bodies; keep the list view compact and let
    # get_log return the full record (headers, query params, bodies).
    "log_": (
        "id",
        "method",
        "path",
        "status_code",
        "created_at",
        "processing_duration",
    ),
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
    "run_": ("id", "report", "status", "company", "created_at", "completed_at"),
    # Filings are prefixed "com_fil_". This entry must be matched before the
    # bare "com_" company entry — see _detect_entity_prefix for the longest-
    # prefix logic that makes that happen.
    "com_fil_": (
        "id",
        "company",
        "status",
        "period",
        "year",
        "name",
        "blocked_reasons",
    ),
}


def _detect_entity_prefix(results: list[dict]) -> str | None:
    """Detect the entity type prefix from the first result's ID.

    Returns the longest known ``_SUMMARY_FIELDS`` prefix that the ID starts
    with. Matching longest-first is essential for multi-segment prefixes like
    ``com_fil_`` (filings), which would otherwise collide with ``com_``
    (companies) and get summarized with the wrong field set.
    """
    if not results:
        return None
    first_id = results[0].get("id", "")
    if not isinstance(first_id, str):
        return None
    for prefix in sorted(_SUMMARY_FIELDS, key=len, reverse=True):
        if first_id.startswith(prefix):
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


_INLINE_PAYROLL_LISTS = (
    ("items", "items_count"),
    ("contractor_payments", "contractor_payments_count"),
)


def shape_payroll(payroll: dict, *, include_items: bool = False) -> dict:
    """Replace a payroll's inlined ``items`` and ``contractor_payments`` with counts.

    The MCP sends no Check-Version header, so a key pinned before API version
    2025-01-01 gets every payroll item inlined on every payroll response (a
    single payroll with a few hundred items is about a megabyte). Later
    versions omit both lists unless the request asks with ``include_items`` /
    ``include_contractor_payments``.

    When ``include_items`` is false, each inlined list is removed and
    ``<field>_count`` records how many entries it held. A response that never
    carried the list is returned unchanged, with no count, so the caller can
    tell "omitted by the API" from "removed here". Error payloads and
    non-dict values pass through untouched.
    """
    if include_items or not isinstance(payroll, dict) or payroll.get("error"):
        return payroll
    shaped = dict(payroll)
    for name, count_field in _INLINE_PAYROLL_LISTS:
        value = shaped.get(name)
        if isinstance(value, list):
            del shaped[name]
            shaped[count_field] = len(value)
    return shaped


def build_body(required: dict, **optional: object) -> dict:
    """Build a request body from required fields and optional keyword arguments.

    Required fields are included unconditionally. Optional keyword arguments
    are included only when their value is not ``None``.

    Example::

        build_body({"company": company}, trade_name=trade_name, email=email)
    """
    body: dict = dict(required)
    for key, val in optional.items():
        if val is not None:
            body[key] = val
    return body


def build_params(**kwargs: object) -> dict | None:
    """Build query parameters from keyword arguments, dropping ``None`` values.

    Booleans are lowercased (``True`` → ``"true"``). Lists are passed through so
    httpx serializes them as repeated params (``ids=a&ids=b``) — the convention
    the Check API uses for multi-value filters. All other values pass through.
    Returns ``None`` when no parameters remain (avoids sending an empty ``?``).

    Example::

        build_params(company=company, limit=limit, active=active, ids=ids)
    """
    params: dict = {}
    for key, val in kwargs.items():
        if val is None:
            continue
        if isinstance(val, bool):
            params[key] = str(val).lower()
        else:
            params[key] = val
    return params or None


def merge_metadata_filter_params(
    params: dict | None, metadata: dict[str, str] | None
) -> dict | None:
    """Add metadata[key]=value query params for list metadata filtering."""
    if not metadata:
        return params
    merged = dict(params or {})
    for key, value in metadata.items():
        merged[f"metadata[{key}]"] = value
    return merged


async def _check_api_request(
    ctx: Ctx,
    method: str,
    path: str,
    params: dict | None = None,
    data: dict | list | None = None,
    extra_headers: dict[str, str] | None = None,
    parse: Callable[[httpx.Response], dict] = lambda response: response.json(),
) -> dict:
    """Make a request to the Check API with shared error handling.

    parse turns a successful response into the tool result; the default decodes
    a JSON body. A 204 or an empty 200 body (the sandbox simulate actions on
    companies answer that way) becomes ``{"success": True}``.
    """
    check_ctx = ctx.request_context.lifespan_context
    headers: dict[str, str] = {"User-Agent": check_ctx.user_agent}
    if extra_headers:
        headers.update(extra_headers)
    if check_ctx.token_resolver is not None:
        headers["Authorization"] = f"Bearer {check_ctx.token_resolver()}"
    try:
        response = await check_ctx.client.request(
            method, path, params=params, json=data, headers=headers or None
        )
        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return {"success": True}
        return parse(response)
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
    except httpx.TimeoutException as e:
        # Surfaced separately so callers can offer an asynchronous alternative
        # instead of reporting an opaque transport error.
        return {"error": True, Failure.TIMED_OUT.value: True, "detail": str(e)}
    except httpx.RequestError as e:
        # A dropped connection or similar. httpx often leaves the message
        # empty, so the class name stands in; transport_error lets code mode
        # retry a read without parsing the message.
        return {
            "error": True,
            "transport_error": type(e).__name__,
            "detail": str(e) or type(e).__name__,
        }


async def check_api_get(ctx: Ctx, path: str, params: dict | None = None) -> dict:
    """Make a GET request to the Check API."""
    return await _check_api_request(ctx, "GET", path, params=params)


async def check_api_get_csv(ctx: Ctx, path: str, params: dict | None = None) -> dict:
    """Make a GET request for a CSV rendering, returned under the csv key."""
    return await _check_api_request(
        ctx,
        "GET",
        path,
        params=params,
        extra_headers={"Accept": "text/csv"},
        parse=_csv_body,
    )


def _csv_body(response: httpx.Response) -> dict:
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("text/csv"):
        return {
            "error": True,
            "detail": f"Expected a CSV response, got {content_type or 'no content type'}.",
        }
    return {"csv": response.text}


# Downloaded documents are returned as text so the model can read them; this
# bounds how much of one lands in its context. It sits under
# ResultBudgetMiddleware's default of 50,000 characters, with room for the
# JSON envelope and page markers: a document result over that budget is not a
# list, so the middleware would reject it whole instead of trimming it.
DOWNLOAD_TEXT_LIMIT = 40_000

_READABLE_DOWNLOADS = "PDF, CSV, plain text, or JSON"


async def check_api_download(ctx: Ctx, path: str) -> dict:
    """GET a document download and return it as text, by content type.

    The document download routes return the file itself, not JSON. A PDF comes
    back as its text layer, page by page; a CSV or plain-text file as-is; a
    JSON body (for example one carrying a URL) decoded. Text longer than
    ``DOWNLOAD_TEXT_LIMIT`` characters is cut, with ``truncated`` set and a
    ``note`` saying what was left out. Anything else is a structured error.
    """
    return await _check_api_request(ctx, "GET", path, parse=_download_body)


def _download_body(response: httpx.Response) -> dict:
    raw_type = response.headers.get("content-type", "")
    content_type = raw_type.split(";", 1)[0].strip().lower()
    filename = _content_disposition_filename(response)
    if content_type == "application/json" or content_type.endswith("+json"):
        return response.json()
    if content_type == "application/pdf":
        return _pdf_download(response.content, filename)
    if content_type == "text/csv" or content_type.startswith("text/"):
        result = _capped_text(response.text)
        result.update(content_type=content_type, filename=filename)
        return result
    return {
        "error": True,
        "content_type": content_type or None,
        "size_bytes": len(response.content),
        "filename": filename,
        "detail": (
            f"Cannot read a {content_type or 'untyped'} download "
            f"({len(response.content)} bytes) here; only a {_READABLE_DOWNLOADS} "
            "download is readable."
        ),
    }


def _content_disposition_filename(response: httpx.Response) -> str | None:
    """Pull the filename out of a Content-Disposition header, if any."""
    header = response.headers.get("content-disposition", "")
    for part in header.split(";")[1:]:
        key, _, value = part.strip().partition("=")
        key = key.strip().lower()
        value = value.strip().strip('"')
        if key == "filename*":
            # RFC 5987: charset'lang'percent-encoded-name
            _, _, encoded = value.rpartition("'")
            return unquote(encoded) or None
        if key == "filename" and value:
            return value
    return None


def _capped_text(text: str) -> dict:
    """Return text under the download limit, flagging what was cut."""
    if len(text) <= DOWNLOAD_TEXT_LIMIT:
        return {"text": text, "truncated": False}
    omitted = len(text) - DOWNLOAD_TEXT_LIMIT
    return {
        "text": text[:DOWNLOAD_TEXT_LIMIT],
        "truncated": True,
        "note": (
            f"Showing the first {DOWNLOAD_TEXT_LIMIT:,} of {len(text):,} characters; "
            f"{omitted:,} were omitted."
        ),
    }


def _pdf_download(data: bytes, filename: str | None) -> dict:
    """Extract a PDF's text layer, page by page, under the download limit."""
    from pypdf import PdfReader  # imported here: only downloads need it
    from pypdf.errors import PyPdfError

    try:
        reader = PdfReader(BytesIO(data))
        page_texts = [(page.extract_text() or "").strip() for page in reader.pages]
    except PyPdfError as e:
        return {
            "error": True,
            "content_type": "application/pdf",
            "filename": filename,
            "detail": f"Could not parse the PDF: {e}",
        }
    total_pages = len(page_texts)
    if not any(page_texts):
        return {
            "error": True,
            "content_type": "application/pdf",
            "filename": filename,
            "pages": total_pages,
            "detail": (
                "The PDF has no text layer (it is a scan or an image), so it "
                "cannot be read here."
            ),
        }
    chunks: list[str] = []
    length = 0
    pages_shown = 0
    page_cut = False
    for number, text in enumerate(page_texts, 1):
        chunk = f"--- page {number} ---\n{text}"
        if chunks:
            chunk = "\n\n" + chunk
        if length + len(chunk) > DOWNLOAD_TEXT_LIMIT:
            room = DOWNLOAD_TEXT_LIMIT - length
            if room > 0 and not chunks:
                # One page alone is over the limit; show what fits of it.
                chunks.append(chunk[:room])
                pages_shown = 1
                page_cut = True
            break
        chunks.append(chunk)
        length += len(chunk)
        pages_shown = number
    result: dict = {
        "content_type": "application/pdf",
        "filename": filename,
        "pages": total_pages,
        "text": "".join(chunks),
        "truncated": page_cut or pages_shown < total_pages,
    }
    if page_cut:
        result["note"] = (
            f"Page 1 alone is over the {DOWNLOAD_TEXT_LIMIT:,}-character "
            f"limit; showing its first {DOWNLOAD_TEXT_LIMIT:,} characters"
            + (
                f" and omitting {total_pages - 1} more pages."
                if total_pages > 1
                else "."
            )
        )
    elif result["truncated"]:
        result["note"] = (
            f"Showing {pages_shown} of {total_pages} pages, under the "
            f"{DOWNLOAD_TEXT_LIMIT:,}-character limit; "
            f"{total_pages - pages_shown} pages were omitted."
        )
    return result


async def check_api_post(
    ctx: Ctx,
    path: str,
    data: dict | list | None = None,
    headers: dict[str, str] | None = None,
    params: dict | None = None,
) -> dict:
    """Make a POST request to the Check API."""
    return await _check_api_request(
        ctx, "POST", path, params=params, data=data, extra_headers=headers
    )


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
