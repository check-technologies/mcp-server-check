"""Tool errors reported to MCP clients as JSON objects."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastmcp.exceptions import ToolError

from mcp_server_check.recovery import Failure, Remedies


class CheckToolError(ToolError):
    """A tool failure whose message is its JSON payload, remedies included."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload)
        self._payload = payload
        self.remedies = Remedies()

    def __str__(self) -> str:
        return json.dumps(self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        if not self.remedies:
            return self._payload
        return {**self._payload, **self.remedies.to_dict()}

    @property
    def failure(self) -> Failure | None:
        return Failure.from_payload(self._payload)


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
                Failure.TOO_LARGE.value: True,
                "detail": (
                    f"The {tool} result is {size} bytes, over the {limit}-byte "
                    "response limit. Narrow the request with filters, a lower "
                    "limit, or specific IDs."
                ),
                "size": size,
                "limit": limit,
            }
        )


class ExpectedToolErrorFilter(logging.Filter):
    """Log a CheckToolError as one warning line instead of an error traceback.

    fastmcp logs every exception a tool raises with its traceback. A
    CheckToolError is an expected outcome the client is told about, such as a
    Check API 4xx, so the traceback is noise.
    """

    @classmethod
    def install(cls, logger: logging.Logger) -> None:
        if not any(isinstance(existing, cls) for existing in logger.filters):
            logger.addFilter(cls())

    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info and isinstance(record.exc_info[1], CheckToolError):
            record.msg, record.args = (
                "%s: %s",
                (record.getMessage(), record.exc_info[1]),
            )
            record.exc_info = None
            record.exc_text = None
            record.levelno = logging.WARNING
            record.levelname = logging.getLevelName(logging.WARNING)
        return True
