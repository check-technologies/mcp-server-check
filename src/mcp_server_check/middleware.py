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
from mcp_server_check.recovery import Recovery, recovery

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolCall:
    """The Check tool a request runs, seen through the run_tool meta-tool."""

    RUN_TOOL = "run_tool"

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
    def json_rpc_body(result: ToolResult) -> int:
        return len(ResponseSize._body(result).encode())

    @staticmethod
    def lambda_proxy(result: ToolResult) -> int:
        """Measure the JSON-RPC body as an AWS Lambda proxy response carries it.

        The proxy wraps the body in a JSON string, escaping it again. Non-ASCII
        text is counted as UTF-8, which assumes the proxy does not escape it.
        """
        return len(json.dumps(ResponseSize._body(result), ensure_ascii=False).encode())

    @staticmethod
    def _body(result: ToolResult) -> str:
        return CallToolResult(
            content=result.content, structuredContent=result.structured_content
        ).model_dump_json(by_alias=True, exclude_none=True)


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
        logger.warning(
            "Tool result exceeds the response size limit",
            extra={"tool": tool, "size": size, "limit": self.max_bytes},
        )
        raise ResponseTooLargeError(tool, size, self.max_bytes)


class RecoveryMiddleware(Middleware):
    """List the registered remedies on a failed call's tool error.

    Only alternatives whose tool the caller can use in this configuration are
    kept. Add it before ResponseSizeLimitMiddleware so it sees that error too.
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
            remedies = self._registry.remedies(
                call.name, call.arguments, error.failure, self._is_tool_available
            )
            if not remedies:
                raise
            raise error.with_remedies(remedies) from error
