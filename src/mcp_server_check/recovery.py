"""Alternatives a failed tool call can point to, declared per tool.

A tool registers a provider with the recoverable decorator. When a call fails
in a way the caller can work around, recovery.enrich adds the provider's
alternatives to the error payload. The MCP server and the CLI both call it,
each with its own test of which tools the caller can use, and each renders
the alternatives for its surface.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

_ToolFunction = TypeVar("_ToolFunction", bound=Callable[..., Any])


class Failure(str, Enum):
    TIMED_OUT = "timed_out"
    TOO_LARGE = "too_large"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Failure | None:
        if payload.get("timeout") is True:
            return cls.TIMED_OUT
        if payload.get("response_too_large") is True:
            return cls.TOO_LARGE
        return None


@dataclass(frozen=True)
class Alternative:
    """Another tool call that can get what a failed call asked for."""

    tool: str
    description: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "description": self.description,
            "arguments": self.arguments,
        }


AlternativesProvider = Callable[[dict[str, Any], Failure], list[Alternative]]


class Recovery:
    """Registry of alternatives providers, keyed by tool function name."""

    def __init__(self) -> None:
        self._providers: dict[str, AlternativesProvider] = {}

    def recoverable(
        self, provider: AlternativesProvider
    ) -> Callable[[_ToolFunction], _ToolFunction]:
        def register(tool: _ToolFunction) -> _ToolFunction:
            self._providers[tool.__name__] = provider
            return tool

        return register

    def enrich(
        self,
        payload: dict[str, Any],
        tool: str,
        arguments: dict[str, Any],
        is_available: Callable[[str], bool],
    ) -> dict[str, Any]:
        """Return payload with the available alternatives, or payload unchanged."""
        failure = Failure.from_payload(payload)
        provider = self._providers.get(tool)
        if failure is None or provider is None:
            return payload
        alternatives = [
            alternative.to_dict()
            for alternative in provider(arguments, failure)
            if is_available(alternative.tool)
        ]
        return {**payload, "alternatives": alternatives}


recovery = Recovery()
recoverable = recovery.recoverable
