"""Tests for the tool-agnostic recovery framework."""

from __future__ import annotations

import pytest
from mcp_server_check.recovery import (
    Alternative,
    Failure,
    Hint,
    Recovery,
    Remedies,
)

RETRY = Alternative(tool="retry_tool", description="Try again.", arguments={"x": 1})
FALLBACK = Alternative(tool="fallback_tool", description="Use the fallback.")
NARROW = Hint(tool="slow_tool", description="Ask for less.", arguments=("limit",))


def always(tool: str) -> bool:
    return True


@pytest.fixture
def registry():
    registry = Recovery()

    @registry.recoverable(lambda arguments, failure: [RETRY, FALLBACK, NARROW])
    async def slow_tool():
        pass

    return registry


class TestFailure:
    @pytest.mark.parametrize(
        ("payload", "expected"),
        [
            ({"error": True, "timeout": True}, Failure.TIMED_OUT),
            ({"error": True, "response_too_large": True}, Failure.TOO_LARGE),
            ({"error": True, "status_code": 400}, None),
        ],
    )
    def test_from_payload(self, payload, expected):
        assert Failure.from_payload(payload) is expected


class TestRemedies:
    def test_empty_is_falsy(self):
        assert not Remedies()
        assert Remedies(hints=(NARROW,))

    def test_to_dict(self):
        remedies = Remedies((RETRY,), (NARROW,))

        assert remedies.to_dict() == {
            "alternatives": [
                {
                    "tool": "retry_tool",
                    "description": "Try again.",
                    "arguments": {"x": 1},
                }
            ],
            "hints": [
                {
                    "tool": "slow_tool",
                    "description": "Ask for less.",
                    "arguments": ["limit"],
                }
            ],
        }


class TestRecovery:
    def test_recoverable_returns_the_tool_unchanged(self):
        registry = Recovery()

        async def tool():
            pass

        assert registry.recoverable(lambda arguments, failure: [])(tool) is tool

    @pytest.mark.parametrize(
        ("available", "expected"),
        [
            pytest.param(
                {"retry_tool", "slow_tool"}, Remedies((RETRY,), (NARROW,)), id="some"
            ),
            pytest.param({"fallback_tool"}, Remedies((FALLBACK,)), id="hint hidden"),
        ],
    )
    def test_keeps_remedies_whose_tool_is_available(
        self, registry, available, expected
    ):
        remedies = registry.remedies(
            "slow_tool", {}, Failure.TIMED_OUT, lambda tool: tool in available
        )

        assert remedies == expected

    def test_merges_arguments_for_the_same_tool(self):
        registry = Recovery()
        csv = Alternative(tool="report", description="CSV.", arguments={"fmt": "csv"})

        @registry.recoverable(lambda arguments, failure: [csv, RETRY])
        async def report():
            pass

        remedies = registry.remedies(
            "report", {"id": "a", "fmt": "json"}, Failure.TOO_LARGE, always
        )

        assert [a.arguments for a in remedies.alternatives] == [
            {"id": "a", "fmt": "csv"},
            {"x": 1},
        ]

    def test_passes_arguments_and_failure_to_provider(self):
        registry = Recovery()
        calls = []

        def provider(arguments, failure):
            calls.append((arguments, failure))
            return []

        @registry.recoverable(provider)
        async def big_tool():
            pass

        registry.remedies("big_tool", {"id": "a"}, Failure.TOO_LARGE, always)

        assert calls == [({"id": "a"}, Failure.TOO_LARGE)]

    @pytest.mark.parametrize(
        ("tool", "failure"),
        [
            pytest.param("slow_tool", None, id="not recoverable failure"),
            pytest.param("plain_tool", Failure.TIMED_OUT, id="no provider"),
        ],
    )
    def test_returns_no_remedies(self, registry, tool, failure):
        assert registry.remedies(tool, {}, failure, always) == Remedies()
