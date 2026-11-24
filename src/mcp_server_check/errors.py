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
        # ToolErrorLogMiddleware logs it with the Check tool and payload.
        super().__init__(payload, log_level=logging.DEBUG)
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

    def __init__(
        self,
        tool: str,
        size: int,
        limit: int,
        unit: str = "byte",
        largest: list[str] | None = None,
        shape: dict[str, Any] | None = None,
    ) -> None:
        advice = (
            # A program's result is whatever it returned, so the fix is in
            # what it returns, not in the calls it made.
            "Return only what the answer needs: pick the fields you need, "
            "filter, or count inside the program instead of returning whole "
            "records or list pages."
            if tool == "run_code"
            else "Narrow the request with filters, a lower limit, or specific IDs."
        )
        if largest:
            # Without this a program rerun tends to cut the wrong thing and
            # fail again on the same oversized field.
            advice += f" Largest parts: {'; '.join(largest)}."
        if shape is not None:
            # Without this the next program is usually a probe of the same
            # result (its keys, its length) rather than a narrower answer.
            advice += (
                ' "shape" below describes the result, so the next program can '
                "pick its part without probing it first."
            )
        payload: dict[str, Any] = {
            "error": True,
            Failure.TOO_LARGE.value: True,
            "detail": (
                f"The {tool} result is {size} {unit}s, over the {limit}-{unit} "
                f"response limit. {advice}"
            ),
            "size": size,
            "limit": limit,
        }
        if shape is not None:
            payload["shape"] = shape
        super().__init__(payload)


SHAPE_MAX_KEYS = 25
SHAPE_MAX_CHARS = 2_000


def result_shape(
    value: Any, max_keys: int = SHAPE_MAX_KEYS, max_chars: int = SHAPE_MAX_CHARS
) -> dict[str, Any]:
    """Describe a JSON value by size, one level deep, for a too-large error.

    A dict lists its keys, biggest value first, each with the characters its
    value serializes to; a list value also says how long it is and what keys
    its first item has, and a dict value which keys it has. A list says its
    length, its size and the keys (or type) of its first item. A scalar says
    its type and, for a string, its length. The description keeps at most
    max_keys keys and max_chars characters, so the error itself stays small.
    """
    if isinstance(value, dict):
        ranked = sorted(value.items(), key=lambda item: _size(item[1]), reverse=True)
        keys = {str(k): _describe(v, max_keys) for k, v in ranked[:max_keys]}
        shape = {"type": "dict", "size": _size(value), "length": len(value)}
        shape["keys"] = keys
        _note_omitted(shape, "keys", len(value))
        while keys and _size(shape) > max_chars:
            keys.popitem()
            _note_omitted(shape, "keys", len(value))
        return shape
    shape = _describe(value, max_keys)
    names = shape.get("item_keys")
    while names and _size(shape) > max_chars:
        names.pop()
        _note_omitted(shape, "item_keys", len(value[0]))
    return shape


def _describe(value: Any, max_keys: int) -> dict[str, Any]:
    """One value's type and size, with its own keys or items named but not sized."""
    shape: dict[str, Any] = {"type": _type_name(value), "size": _size(value)}
    if isinstance(value, dict):
        shape["length"] = len(value)
        shape["keys"] = [str(k) for k in list(value)[:max_keys]]
        _note_omitted(shape, "keys", len(value))
    elif isinstance(value, list):
        shape["length"] = len(value)
        if value and isinstance(value[0], dict):
            shape["item_keys"] = [str(k) for k in list(value[0])[:max_keys]]
            _note_omitted(shape, "item_keys", len(value[0]))
        elif value:
            shape["item_type"] = _type_name(value[0])
    elif isinstance(value, str):
        shape["length"] = len(value)
    return shape


def _note_omitted(shape: dict[str, Any], field: str, total: int) -> None:
    omitted = total - len(shape[field])
    if omitted > 0:
        shape[f"{field}_omitted"] = omitted
    else:
        shape.pop(f"{field}_omitted", None)


def _size(value: Any) -> int:
    """Characters of the compact JSON a tool result is delivered as."""
    return len(json.dumps(value, separators=(",", ":"), default=str))


def _type_name(value: Any) -> str:
    return "None" if value is None else type(value).__name__
