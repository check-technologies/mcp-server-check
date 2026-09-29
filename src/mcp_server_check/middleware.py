"""Middleware that keeps tool failures explicit and actionable for MCP clients."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools import ToolResult
from mcp.types import CallToolRequestParams, CallToolResult

from mcp_server_check.errors import CheckToolError, ResponseTooLargeError
from mcp_server_check.reports import ReportRequest
from mcp_server_check.tool_filter import ToolFilter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolCall:
    """The Check tool a request runs, seen through the run_tool meta-tool."""

    name: str
    arguments: dict[str, Any]

    @classmethod
    def from_request(cls, params: CallToolRequestParams) -> ToolCall:
        arguments = params.arguments or {}
        if params.name != "run_tool":
            return cls(params.name, arguments)
        inner_arguments = arguments.get("arguments")
        if isinstance(inner_arguments, str):
            try:
                inner_arguments = json.loads(inner_arguments)
            except json.JSONDecodeError:
                inner_arguments = None
        return cls(
            str(arguments.get("tool_name", params.name)),
            inner_arguments if isinstance(inner_arguments, dict) else {},
        )


class ResponseSizeLimitMiddleware(Middleware):
    """Raise ResponseTooLargeError for a tool result over max_bytes.

    The hosted server runs on AWS Lambda, which drops a buffered response over
    6,291,556 bytes and leaves the client with an unexplained transport failure.
    fastmcp's ResponseLimitingMiddleware truncates instead, which hands the
    model broken JSON.
    """

    ENV_VAR = "CHECK_MAX_RESPONSE_BYTES"
    DEFAULT_MAX_BYTES = 6_000_000

    def __init__(self, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        if max_bytes <= 0:
            raise ValueError(f"max_bytes must be positive, got {max_bytes}")
        self.max_bytes = max_bytes

    @classmethod
    def from_env(cls) -> ResponseSizeLimitMiddleware | None:
        """Configure from CHECK_MAX_RESPONSE_BYTES; a 0 value disables the limit."""
        max_bytes = int(os.environ.get(cls.ENV_VAR, cls.DEFAULT_MAX_BYTES))
        return cls(max_bytes) if max_bytes else None

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        result = await call_next(context)
        if not isinstance(result, ToolResult):
            return result
        size = self.proxied_size(result)
        if size <= self.max_bytes:
            return result
        tool = ToolCall.from_request(context.message).name
        logger.warning(
            "Tool result exceeds the response size limit",
            extra={"tool": tool, "size": size, "limit": self.max_bytes},
        )
        raise ResponseTooLargeError(tool, size, self.max_bytes)

    @staticmethod
    def proxied_size(result: ToolResult) -> int:
        """Return the bytes a result takes inside the Lambda proxy response.

        The proxy carries the JSON-RPC body as a JSON string, escaping it again.
        """
        body = CallToolResult(
            content=result.content, structuredContent=result.structured_content
        ).model_dump_json(by_alias=True, exclude_none=True)
        return len(json.dumps(body, ensure_ascii=False).encode())


class ReportAlternativesMiddleware(Middleware):
    """Add the calls that can still get a report to a timeout or size failure.

    A report's cost depends on how much payroll data falls in its range, mostly
    company size, so which requests are too big cannot be told up front: a
    full-year journal returns in seconds for most companies and times out for
    the largest. Reports are therefore tried synchronously, and the report run
    and narrower alternatives are offered only once a request fails. They name
    MCP tools and depend on which ones the active filter allows, so they are
    added here rather than by the tool function.
    """

    def __init__(self, active_tool_filter: Callable[[], ToolFilter]) -> None:
        self._active_tool_filter = active_tool_filter

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        try:
            return await call_next(context)
        except CheckToolError as error:
            timed_out = error.payload.get("timeout") is True
            if not (timed_out or error.payload.get("response_too_large")):
                raise
            call = ToolCall.from_request(context.message)
            if call.name != "get_company_report":
                raise
            try:
                request = ReportRequest.from_arguments(call.arguments)
            except ValueError:
                raise error from None
            report_runs_available = self._active_tool_filter().is_tool_allowed(
                "create_report_run", "report_runs"
            )
            alternatives = request.alternatives(
                report_runs_available=report_runs_available, timed_out=timed_out
            )
            raise CheckToolError(
                {
                    **error.payload,
                    "alternatives": [
                        alternative.to_dict() for alternative in alternatives
                    ],
                }
            ) from error
