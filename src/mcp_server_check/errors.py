"""Tool errors reported to MCP clients as JSON objects."""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from fastmcp.exceptions import ToolError

from mcp_server_check.recovery import Failure, Remedies

_ErrorT = TypeVar("_ErrorT", bound="CheckToolError")


class CheckToolError(ToolError):
    """A tool failure whose message is its JSON payload."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(json.dumps(payload))
        self.payload = payload

    @property
    def failure(self) -> Failure | None:
        return Failure.from_payload(self.payload)

    def with_remedies(self: _ErrorT, remedies: Remedies) -> _ErrorT:
        """Return a copy of this error, of the same type, listing the remedies."""
        # Subclass constructors take other arguments, so build the copy by hand.
        error = type(self).__new__(type(self))
        CheckToolError.__init__(error, {**self.payload, **remedies.to_dict()})
        return error


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
