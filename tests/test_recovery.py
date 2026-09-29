"""Tests for the tool-agnostic recovery framework."""

from __future__ import annotations

import pytest
from mcp_server_check.recovery import Alternative, Failure, Recovery

RETRY = Alternative(tool="retry_tool", description="Try again.", arguments={"x": 1})
FALLBACK = Alternative(tool="fallback_tool", description="Use the fallback.")


@pytest.fixture
def registry():
    registry = Recovery()

    @registry.recoverable(lambda arguments, failure: [RETRY, FALLBACK])
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


class TestRecovery:
    def test_recoverable_returns_the_tool_unchanged(self):
        registry = Recovery()

        async def tool():
            pass

        assert registry.recoverable(lambda arguments, failure: [])(tool) is tool

    def test_enrich_adds_available_alternatives(self, registry):
        payload = {"error": True, "timeout": True}

        enriched = registry.enrich(
            payload, "slow_tool", {}, is_available=lambda tool: tool == "retry_tool"
        )

        assert enriched == {
            "error": True,
            "timeout": True,
            "alternatives": [RETRY.to_dict()],
        }
        assert payload == {"error": True, "timeout": True}

    def test_enrich_merges_arguments_for_the_same_tool(self):
        registry = Recovery()
        csv = Alternative(tool="report", description="CSV.", arguments={"fmt": "csv"})

        @registry.recoverable(lambda arguments, failure: [csv, RETRY])
        async def report():
            pass

        enriched = registry.enrich(
            {"timeout": True}, "report", {"id": "a", "fmt": "json"}, lambda tool: True
        )

        assert [a["arguments"] for a in enriched["alternatives"]] == [
            {"id": "a", "fmt": "csv"},
            {"x": 1},
        ]

    def test_enrich_passes_arguments_and_failure_to_provider(self):
        registry = Recovery()
        calls = []

        def provider(arguments, failure):
            calls.append((arguments, failure))
            return []

        @registry.recoverable(provider)
        async def big_tool():
            pass

        registry.enrich(
            {"response_too_large": True}, "big_tool", {"id": "a"}, lambda tool: True
        )

        assert calls == [({"id": "a"}, Failure.TOO_LARGE)]

    @pytest.mark.parametrize(
        ("payload", "tool"),
        [
            pytest.param(
                {"error": True, "status_code": 400}, "slow_tool", id="other error"
            ),
            pytest.param(
                {"error": True, "timeout": True}, "plain_tool", id="no provider"
            ),
        ],
    )
    def test_enrich_returns_payload_unchanged(self, registry, payload, tool):
        assert registry.enrich(payload, tool, {}, lambda tool: True) is payload
