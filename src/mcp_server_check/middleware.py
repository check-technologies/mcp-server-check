"""Middleware that keeps tool failures explicit and actionable for MCP clients."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar

from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools import ToolResult
from fastmcp.tools.base import default_serializer
from mcp.types import CallToolRequestParams, CallToolResult, TextContent

from mcp_server_check.errors import CheckToolError, ResponseTooLargeError
from mcp_server_check.recovery import Recovery, recovery

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolCall:
    """The Check tool a request runs, seen through the run_tool meta-tool."""

    RUN_TOOL: ClassVar[str] = "run_tool"

    name: str
    arguments: dict[str, Any]

    @classmethod
    def from_run_tool(cls, tool_name: str, arguments: str | dict | None) -> ToolCall:
        """Parse run_tool arguments, given as a JSON object string or a dict."""
        if arguments is None:
            return cls(tool_name, {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                raise CheckToolError({"error": f"Invalid JSON arguments: {e}"}) from e
            if not isinstance(arguments, dict):
                raise CheckToolError({"error": "Arguments must be a JSON object"})
        if not isinstance(arguments, dict):
            raise CheckToolError({"error": "Arguments must be a JSON string or object"})
        return cls(tool_name, arguments)

    @classmethod
    def from_request(cls, params: CallToolRequestParams) -> ToolCall:
        """Return the Check tool call a request runs; malformed arguments read as none."""
        arguments = params.arguments or {}
        if params.name != cls.RUN_TOOL:
            return cls(params.name, arguments)
        tool_name = str(arguments.get("tool_name", params.name))
        try:
            return cls.from_run_tool(tool_name, arguments.get("arguments"))
        except CheckToolError:
            return cls(tool_name, {})


class ResponseSize:
    """Ways to measure the bytes a tool result takes on the wire."""

    @staticmethod
    def lambda_proxy(result: ToolResult) -> int:
        """Measure the JSON-RPC body as an AWS Lambda proxy response carries it.

        The proxy wraps the body in a JSON string. The body has no raw control
        characters, so that adds a byte per quote and backslash plus the two
        enclosing quotes. The body is serialized once, as UTF-8 bytes.
        """
        message = CallToolResult(
            content=result.content, structuredContent=result.structured_content
        )
        body = message.__pydantic_serializer__.to_json(
            message, by_alias=True, exclude_none=True
        )
        return len(body) + body.count(b'"') + body.count(b"\\") + 2


class ResponseSizeLimitMiddleware(Middleware):
    """Raise ResponseTooLargeError for a tool result over max_bytes.

    The hosted server runs on AWS Lambda, which drops a buffered response over
    6,291,556 bytes and leaves the client with an unexplained transport failure.
    fastmcp's ResponseLimitingMiddleware truncates instead, which hands the
    model broken JSON. Results of background tasks are delivered outside the
    middleware chain, so this does not limit them.
    """

    ENV_VAR = "CHECK_MAX_RESPONSE_BYTES"
    DEFAULT_MAX_BYTES = 6_000_000

    def __init__(
        self,
        max_bytes: int = DEFAULT_MAX_BYTES,
        measure: Callable[[ToolResult], int] = ResponseSize.lambda_proxy,
    ) -> None:
        if max_bytes <= 0:
            raise ValueError(f"max_bytes must be positive, got {max_bytes}")
        self.max_bytes = max_bytes
        self._measure = measure

    @classmethod
    def from_env(cls) -> ResponseSizeLimitMiddleware | None:
        """Configure from CHECK_MAX_RESPONSE_BYTES; a 0 value disables the limit."""
        value = os.environ.get(cls.ENV_VAR, str(cls.DEFAULT_MAX_BYTES))
        try:
            max_bytes = int(value)
        except ValueError:
            raise ValueError(
                f"{cls.ENV_VAR} must be a whole number of bytes, got {value!r}"
            ) from None
        return cls(max_bytes) if max_bytes else None

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        result = await call_next(context)
        if not isinstance(result, ToolResult):
            return result
        size = self._measure(result)
        if size <= self.max_bytes:
            return result
        tool = ToolCall.from_request(context.message).name
        raise ResponseTooLargeError(tool, size, self.max_bytes)


class ResultBudgetMiddleware(Middleware):
    """Keep a tool result within the characters a model can sensibly read.

    ResponseSizeLimitMiddleware protects the transport; this protects the
    model's context window, where a megabyte result fails the next model call
    with "prompt is too long". A list result over the budget keeps the records
    that fit and says how many were left out. Any other result over the budget
    becomes a ResponseTooLargeError, so the model narrows the call instead of
    reading a document cut off mid-way.
    """

    ENV_VAR = "CHECK_MAX_RESULT_CHARS"
    # About 12k tokens. Prod results sit well under it (p99 about 50k), so it
    # only catches the outliers.
    DEFAULT_MAX_CHARS = 50_000
    # The tool catalog itself: the model needs all of it to find a tool, and
    # an error there would leave it with nothing to call.
    EXEMPT_TOOLS: ClassVar[frozenset[str]] = frozenset(
        {"search_tools", "list_toolsets", "get_stubs"}
    )

    def __init__(self, max_chars: int = DEFAULT_MAX_CHARS) -> None:
        if max_chars <= 0:
            raise ValueError(f"max_chars must be positive, got {max_chars}")
        self.max_chars = max_chars

    @classmethod
    def from_env(cls) -> ResultBudgetMiddleware | None:
        """Configure from CHECK_MAX_RESULT_CHARS; a 0 value disables the budget."""
        value = os.environ.get(cls.ENV_VAR, str(cls.DEFAULT_MAX_CHARS))
        try:
            max_chars = int(value)
        except ValueError:
            raise ValueError(
                f"{cls.ENV_VAR} must be a whole number of characters, got {value!r}"
            ) from None
        return cls(max_chars) if max_chars else None

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        result = await call_next(context)
        if (
            not isinstance(result, ToolResult)
            or context.message.name in self.EXEMPT_TOOLS
        ):
            return result
        size = _text_length(result)
        if size <= self.max_chars:
            return result
        trimmed = self._trim_list(result)
        if trimmed is not None:
            return trimmed
        tool = ToolCall.from_request(context.message).name
        raise ResponseTooLargeError(tool, size, self.max_chars, unit="character")

    def _trim_list(self, result: ToolResult) -> ToolResult | None:
        """Keep the leading records of a list result that fit the budget."""
        if result.structured_content is not None or len(result.content) != 1:
            return None
        block = result.content[0]
        if not isinstance(block, TextContent):
            return None
        try:
            data = json.loads(block.text)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            return None
        text = None
        low, high = 1, len(data["results"]) - 1
        while low <= high:
            middle = (low + high) // 2
            candidate = default_serializer(_page_of(data, middle))
            if len(candidate) <= self.max_chars:
                text = candidate
                low = middle + 1
            else:
                high = middle - 1
        if text is None:
            return None
        return ToolResult(
            content=[TextContent(type="text", text=text)], meta=result.meta
        )


def _text_length(result: ToolResult) -> int:
    return sum(len(b.text) for b in result.content if isinstance(b, TextContent))


def _page_of(data: dict[str, Any], kept: int) -> dict[str, Any]:
    records = data["results"]
    page = {**data, "results": records[:kept], "results_omitted": len(records) - kept}
    # The cursor starts after the full page, so following it would skip the
    # omitted records.
    page.pop("next_cursor", None)
    page["hint"] = (
        f"Only the first {kept} of {len(records)} results fit in one response. "
        f"Call again with limit={kept} to page through the rest, or narrow the "
        "request with filters."
    )
    return page


def _loggable(tool: str, payload: dict[str, Any]) -> dict[str, Any]:
    """The part of an error payload that is safe to log.

    A run_code failure carries the program's printed output, every call's
    arguments, and a traceback quoting the source, any of which can hold
    employee PII. Log its shape only; the client still gets the full payload.
    """
    if tool != "run_code":
        return payload
    calls = []
    for call in payload.get("calls") or []:
        error = call.get("error")
        calls.append(
            {
                "tool": call.get("tool"),
                "status": call.get("status"),
                "status_code": error.get("status_code")
                if isinstance(error, dict)
                else None,
            }
        )
    return {"kind": payload.get("kind"), "calls": calls}


class ToolErrorLogMiddleware(Middleware):
    """Log each CheckToolError once, with the Check tool it came from.

    fastmcp's own line names only the called tool, which is run_tool in dynamic
    mode, and carries no detail, so CheckToolError logs there at DEBUG.
    """

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        try:
            return await call_next(context)
        except CheckToolError as error:
            tool = ToolCall.from_request(context.message).name
            logged = _loggable(tool, error.payload)
            # Formatted now: RecoveryMiddleware adds remedies to the error later.
            payload = json.dumps(logged)
            logger.warning(
                "Tool call failed: tool=%s error=%s",
                tool,
                payload,
                extra={"tool": tool, "error": logged},
            )
            raise


class RecoveryMiddleware(Middleware):
    """List the registered remedies on a failed call's tool error.

    Only alternatives whose tool the caller can use in this configuration are
    kept. Add it first, so it sees every other middleware's errors and they
    are logged without the remedies.
    """

    def __init__(
        self, is_tool_available: Callable[[str], bool], registry: Recovery = recovery
    ) -> None:
        self._is_tool_available = is_tool_available
        self._registry = registry

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        try:
            return await call_next(context)
        except CheckToolError as error:
            call = ToolCall.from_request(context.message)
            error.remedies = self._registry.remedies(
                call.name, call.arguments, error.failure, self._is_tool_available
            )
            raise
