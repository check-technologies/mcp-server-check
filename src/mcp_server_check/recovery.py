"""Remedies a failed tool call can point to, declared per tool.

A tool registers a provider with the recoverable decorator. When a call fails
in a way the caller can work around, Recovery.remedies collects the provider's
alternatives (complete calls to run instead) and hints (advice with no call
attached), keeping only the alternatives the caller can use. The MCP server
and the CLI each render the result for their surface.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, TypeVar, Union

_ToolFunction = TypeVar("_ToolFunction", bound=Callable[..., Any])


class Failure(str, Enum):
    """A failure a caller can work around; each value is its payload flag."""

    TIMED_OUT = "timeout"
    TOO_LARGE = "response_too_large"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Failure | None:
        return next((failure for failure in cls if payload.get(failure.value)), None)


@dataclass(frozen=True)
class Alternative:
    """A complete tool call that can get what a failed call asked for.

    An alternative for the failed tool itself names only the arguments it
    changes; Recovery.remedies merges them into the failed call's.
    """

    tool: str
    description: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "description": self.description,
            "arguments": self.arguments,
        }


@dataclass(frozen=True)
class Hint:
    """Advice that needs input only the caller has, so it names no call."""

    description: str


Remedy = Union[Alternative, Hint]
RemedyProvider = Callable[[dict[str, Any], Failure], list[Remedy]]


@dataclass(frozen=True)
class Remedies:
    alternatives: tuple[Alternative, ...] = ()
    hints: tuple[Hint, ...] = ()

    def __bool__(self) -> bool:
        return bool(self.alternatives or self.hints)

    def to_dict(self) -> dict[str, Any]:
        return {
            "alternatives": [
                alternative.to_dict() for alternative in self.alternatives
            ],
            "hints": [hint.description for hint in self.hints],
        }


class Recovery:
    """Registry of remedy providers, keyed by tool function name."""

    def __init__(self) -> None:
        self._providers: dict[str, RemedyProvider] = {}

    def recoverable(
        self, provider: RemedyProvider
    ) -> Callable[[_ToolFunction], _ToolFunction]:
        def register(tool: _ToolFunction) -> _ToolFunction:
            self._providers[tool.__name__] = provider
            return tool

        return register

    def remedies(
        self,
        tool: str,
        arguments: dict[str, Any],
        failure: Failure | None,
        is_available: Callable[[str], bool],
    ) -> Remedies:
        provider = self._providers.get(tool)
        if failure is None or provider is None:
            return Remedies()
        alternatives = []
        hints = []
        for remedy in provider(arguments, failure):
            if isinstance(remedy, Hint):
                hints.append(remedy)
            elif is_available(remedy.tool):
                alternatives.append(
                    replace(remedy, arguments={**arguments, **remedy.arguments})
                    if remedy.tool == tool
                    else remedy
                )
        return Remedies(tuple(alternatives), tuple(hints))


recovery = Recovery()
recoverable = recovery.recoverable
