"""Tool errors reported to MCP clients as JSON objects."""

from __future__ import annotations

import json
from typing import Any

from fastmcp.exceptions import ToolError


class CheckToolError(ToolError):
    """A tool failure whose message is a JSON object with an error key."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(json.dumps(payload))
        self.payload = payload


class CheckAPIError(CheckToolError):
    """Raised when a tool result reports a failed Check API call."""

    @classmethod
    def from_result(cls, result: Any) -> CheckAPIError | None:
        if isinstance(result, dict) and result.get("error") is True:
            return cls(result)
        return None


class ResponseTooLargeError(CheckToolError):
    """Raised when a tool result is too large to deliver to the client."""

    def __init__(self, tool: str, size: int, limit: int) -> None:
        super().__init__(
            {
                "error": True,
                "response_too_large": True,
                "detail": (
                    f"The {tool} result is {size} bytes, over the {limit}-byte "
                    "response limit. Narrow the request with filters, a lower "
                    "limit, or specific IDs."
                ),
                "size": size,
                "limit": limit,
            }
        )
