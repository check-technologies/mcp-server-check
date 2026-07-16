"""Tests for the destructive-tool consent gate (MCP elicitation)."""

from __future__ import annotations

import json

import pytest
import respx
from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult
from fastmcp.exceptions import ToolError
from httpx import Response

from mcp_server_check.server import CheckMCP, lifespan, setup_tools
from mcp_server_check.tool_filter import ToolFilter

BASE_URL = "https://sandbox.checkhq.com"


@pytest.fixture(autouse=True)
def api_key_env(monkeypatch):
    monkeypatch.setenv("CHECK_API_KEY", "test-key")
    monkeypatch.delenv("CHECK_API_BASE_URL", raising=False)
    monkeypatch.delenv("CHECK_CONFIRM_DESTRUCTIVE", raising=False)


@pytest.fixture
def mock_api():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
        yield mock


def _dynamic_server(tool_filter: ToolFilter | None = None) -> CheckMCP:
    server = CheckMCP("Test Dynamic", lifespan=lifespan)
    setup_tools(server, tool_mode="dynamic")
    if tool_filter is not None:
        server._static_filter = tool_filter
    return server


def _all_tools_server(tool_filter: ToolFilter | None = None) -> CheckMCP:
    server = CheckMCP("Test All", lifespan=lifespan)
    setup_tools(server, tool_mode="all")
    if tool_filter is not None:
        server._static_filter = tool_filter
    return server


def _make_handler(action: str, log: list | None = None):
    async def handler(message, response_type, params, context):
        if log is not None:
            log.append(message)
        if action == "accept":
            return ElicitResult(action="accept", content={})
        return ElicitResult(action=action)

    return handler


# --- Dynamic mode (run_tool) ---


class TestDynamicModeGate:
    async def test_accept_runs_the_tool(self, mock_api):
        route = mock_api.post("/payments/pay_123/cancel").mock(
            return_value=Response(200, json={"id": "pay_123", "status": "cancelled"})
        )
        prompts: list[str] = []
        server = _dynamic_server()
        async with Client(
            server, elicitation_handler=_make_handler("accept", prompts)
        ) as client:
            result = await client.call_tool(
                "run_tool",
                {"tool_name": "cancel_payment", "arguments": {"payment_id": "pay_123"}},
            )
        assert route.called
        assert "cancelled" in result.content[0].text
        # The user-visible prompt names the tool and shows its arguments
        assert len(prompts) == 1
        assert "cancel_payment" in prompts[0]
        assert "pay_123" in prompts[0]

    async def test_decline_blocks_the_call(self, mock_api):
        route = mock_api.post("/payments/pay_123/cancel").mock(
            return_value=Response(200, json={})
        )
        server = _dynamic_server()
        async with Client(
            server, elicitation_handler=_make_handler("decline")
        ) as client:
            result = await client.call_tool(
                "run_tool",
                {"tool_name": "cancel_payment", "arguments": {"payment_id": "pay_123"}},
            )
        assert not route.called
        payload = json.loads(result.content[0].text)
        assert payload["confirmation_required"] is True
        assert "declined" in payload["error"]

    async def test_no_elicitation_support_fails_closed(self, mock_api):
        route = mock_api.post("/payments/pay_123/cancel").mock(
            return_value=Response(200, json={})
        )
        server = _dynamic_server()
        async with Client(server) as client:  # no elicitation handler
            result = await client.call_tool(
                "run_tool",
                {"tool_name": "cancel_payment", "arguments": {"payment_id": "pay_123"}},
            )
        assert not route.called
        payload = json.loads(result.content[0].text)
        assert payload["confirmation_required"] is True
        assert "does not support MCP elicitation" in payload["error"]

    async def test_non_destructive_tool_skips_prompt(self, mock_api):
        route = mock_api.get("/companies").mock(
            return_value=Response(200, json={"results": [], "next": None})
        )
        prompts: list[str] = []
        server = _dynamic_server()
        async with Client(
            server, elicitation_handler=_make_handler("accept", prompts)
        ) as client:
            await client.call_tool("run_tool", {"tool_name": "list_companies"})
        assert route.called
        assert prompts == []

    async def test_operator_opt_out_disables_gate(self, mock_api):
        route = mock_api.post("/payments/pay_123/cancel").mock(
            return_value=Response(200, json={"id": "pay_123"})
        )
        prompts: list[str] = []
        server = _dynamic_server(ToolFilter(confirm_destructive=False))
        async with Client(
            server, elicitation_handler=_make_handler("accept", prompts)
        ) as client:
            await client.call_tool(
                "run_tool",
                {"tool_name": "cancel_payment", "arguments": {"payment_id": "pay_123"}},
            )
        assert route.called
        assert prompts == []

    async def test_gates_upstream_instruction_tools(self, mock_api):
        """create_payroll (shapes disbursements) is gated, not just money movers."""
        route = mock_api.post("/payrolls").mock(
            return_value=Response(200, json={"id": "prl_1"})
        )
        server = _dynamic_server()
        async with Client(
            server, elicitation_handler=_make_handler("decline")
        ) as client:
            result = await client.call_tool(
                "run_tool",
                {
                    "tool_name": "create_payroll",
                    "arguments": {
                        "company": "com_1",
                        "period_start": "2026-07-01",
                        "period_end": "2026-07-15",
                        "payday": "2026-07-18",
                    },
                },
            )
        assert not route.called
        assert json.loads(result.content[0].text)["confirmation_required"] is True


# --- All-tools mode (middleware) ---


class TestAllToolsModeGate:
    async def test_accept_runs_the_tool(self, mock_api):
        route = mock_api.post("/payments/pay_123/cancel").mock(
            return_value=Response(200, json={"id": "pay_123", "status": "cancelled"})
        )
        prompts: list[str] = []
        server = _all_tools_server()
        async with Client(
            server, elicitation_handler=_make_handler("accept", prompts)
        ) as client:
            result = await client.call_tool("cancel_payment", {"payment_id": "pay_123"})
        assert route.called
        assert "cancelled" in result.content[0].text
        assert len(prompts) == 1
        assert "cancel_payment" in prompts[0]

    async def test_decline_blocks_the_call(self, mock_api):
        route = mock_api.post("/payments/pay_123/cancel").mock(
            return_value=Response(200, json={})
        )
        server = _all_tools_server()
        async with Client(
            server, elicitation_handler=_make_handler("decline")
        ) as client:
            with pytest.raises(ToolError, match="declined"):
                await client.call_tool("cancel_payment", {"payment_id": "pay_123"})
        assert not route.called

    async def test_no_elicitation_support_fails_closed(self, mock_api):
        route = mock_api.post("/payments/pay_123/cancel").mock(
            return_value=Response(200, json={})
        )
        server = _all_tools_server()
        async with Client(server) as client:
            with pytest.raises(ToolError, match="does not support MCP elicitation"):
                await client.call_tool("cancel_payment", {"payment_id": "pay_123"})
        assert not route.called

    async def test_non_destructive_tool_skips_prompt(self, mock_api):
        route = mock_api.get("/companies").mock(
            return_value=Response(200, json={"results": [], "next": None})
        )
        prompts: list[str] = []
        server = _all_tools_server()
        async with Client(
            server, elicitation_handler=_make_handler("accept", prompts)
        ) as client:
            await client.call_tool("list_companies", {})
        assert route.called
        assert prompts == []
