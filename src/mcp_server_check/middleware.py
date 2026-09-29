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
from mcp_server_check.recovery import recovery

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


class RecoveryMiddleware(Middleware):
    """Add the registered alternatives to a failed call's tool error.

    Only alternatives whose tool the caller can use in this configuration are
    kept. Add it before ResponseSizeLimitMiddleware so it sees that error too.
    """

    def __init__(self, is_tool_available: Callable[[str], bool]) -> None:
        self._is_tool_available = is_tool_available

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        try:
            return await call_next(context)
        except CheckToolError as error:
            call = ToolCall.from_request(context.message)
            payload = recovery.enrich(
                error.payload, call.name, call.arguments, self._is_tool_available
            )
            if payload is error.payload:
                raise
            raise CheckToolError(payload) from error
