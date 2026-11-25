"""Tests for check.save / check.load: values kept across run_code programs."""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest
from fastmcp import Client
from key_value.aio.stores.memory import MemoryStore
from mcp_server_check.code_state import (
    LOCAL_SCOPE,
    ProgramState,
    StateLimits,
    state_scope,
)
from mcp_server_check.server import CheckMCP, lifespan, setup_tools

COMPANIES = {
    "results": [{"id": "com_1"}, {"id": "com_2"}],
    "next": None,
    "previous": None,
}


def _request(**headers: str) -> SimpleNamespace:
    return SimpleNamespace(headers={k.replace("_", "-"): v for k, v in headers.items()})


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


def test_scope_without_a_request_is_local_only_when_allowed():
    assert state_scope(None, allow_local=True) == LOCAL_SCOPE
    assert state_scope(None) is None


def test_scope_needs_the_conversation_header():
    assert state_scope(_request(authorization="Bearer a")) is None


def test_scope_is_per_credential_and_conversation():
    a = state_scope(_request(authorization="Bearer a", x_mcp_conversation_id="cnv_1"))
    assert a is not None and a.startswith("c-")
    assert "cnv_1" not in a and "Bearer" not in a
    # The same conversation ID under another credential is another scope, so
    # a guessed ID reads nothing.
    assert a != state_scope(
        _request(authorization="Bearer b", x_mcp_conversation_id="cnv_1")
    )
    assert a != state_scope(
        _request(authorization="Bearer a", x_mcp_conversation_id="cnv_2")
    )
    assert a == state_scope(
        _request(authorization="Bearer a", x_mcp_conversation_id="cnv_1")
    )


# ---------------------------------------------------------------------------
# ProgramState
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_save_then_load_round_trips_json():
    state = ProgramState(MemoryStore(), "s1")
    await state.save("ids", ["emp_1", "emp_2"])
    await state.save("params", {"emp_1": {"fit": "0"}})
    assert await state.load("ids") == ["emp_1", "emp_2"]
    assert await state.load("params") == {"emp_1": {"fit": "0"}}
    assert await state.load("missing") is None
    assert await state.load("missing", default=[]) == []
    assert set(await state.saved()) == {"ids", "params"}


@pytest.mark.anyio
async def test_scopes_do_not_see_each_other():
    store = MemoryStore()
    await ProgramState(store, "s1").save("ids", [1])
    assert await ProgramState(store, "s2").load("ids") is None


@pytest.mark.anyio
async def test_save_rejects_values_that_are_not_json():
    state = ProgramState(MemoryStore(), "s1")
    with pytest.raises(ValueError, match="JSON-serializable"):
        await state.save("x", {1, 2})


@pytest.mark.anyio
async def test_save_rejects_bad_and_reserved_names():
    state = ProgramState(MemoryStore(), "s1")
    for name in ("", "a b", "__index__", "x" * 65, 3):
        with pytest.raises(ValueError):
            await state.save(name, 1)


@pytest.mark.anyio
async def test_save_enforces_size_and_key_limits():
    limits = StateLimits(max_value_bytes=100, max_total_bytes=150, max_keys=2)
    state = ProgramState(MemoryStore(), "s1", limits)
    with pytest.raises(ValueError, match="limit is 100"):
        await state.save("big", "x" * 200)
    await state.save("a", "x" * 80)
    with pytest.raises(ValueError, match="limit is 150"):
        await state.save("b", "x" * 80)
    await state.save("b", "x")
    with pytest.raises(ValueError, match="limit is 2"):
        await state.save("c", "x")
    # Overwriting a name is not a new name.
    await state.save("a", "y")


# ---------------------------------------------------------------------------
# End to end through run_code
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _runs_in_local_microvm(local_microvm):
    """Every program in this module runs in the local runner."""


def _server(monkeypatch, *, store=None, local=True) -> CheckMCP:
    monkeypatch.setenv("CHECK_API_KEY", "test-key")
    monkeypatch.delenv("CHECK_API_BASE_URL", raising=False)
    monkeypatch.setenv("CHECK_CODE_TIMEOUT_SECS", "20")
    monkeypatch.setenv("CHECK_CODE_MODE", "1")
    server = CheckMCP("Test Code State", lifespan=lifespan)
    setup_tools(server, code_state_store=store, code_state_local_scope=local)
    return server


async def _run(client: Client, code: str) -> dict:
    result = await client.call_tool("run_code", {"code": code}, raise_on_error=False)
    return json.loads(result.content[0].text)


@pytest.mark.anyio
async def test_a_later_program_loads_what_an_earlier_one_saved(mock_api, monkeypatch):
    route = mock_api.get("/companies").mock(
        return_value=httpx.Response(200, json=COMPANIES)
    )
    server = _server(monkeypatch, store=MemoryStore())
    async with Client(server) as client:
        first = await _run(
            client,
            """
page = await check.list_companies()
ids = [c["id"] for c in page["results"]]
await check.save("company_ids", ids)
len(ids)
""",
        )
        second = await _run(
            client,
            """
ids = await check.load("company_ids")
{"ids": ids, "saved": await check.saved()}
""",
        )
    assert first["result"] == 2
    assert second["result"]["ids"] == ["com_1", "com_2"]
    assert "company_ids" in second["result"]["saved"]
    # The second program read the saved list instead of the API.
    assert route.call_count == 1


@pytest.mark.anyio
async def test_save_without_a_scope_explains_itself(monkeypatch):
    server = _server(monkeypatch, store=MemoryStore(), local=False)
    async with Client(server) as client:
        result = await _run(
            client,
            """
try:
    await check.save("x", 1)
    outcome = "saved"
except ValueError as e:
    outcome = str(e)
outcome
""",
        )
    assert "x-mcp-conversation-id" in result["result"]


@pytest.mark.anyio
async def test_without_a_store_programs_have_no_save(monkeypatch):
    server = _server(monkeypatch)
    async with Client(server) as client:
        result = await _run(client, 'hasattr(check, "save")')
        stubs = (
            (await client.call_tool("get_stubs", {"toolset": "platform"}))
            .content[0]
            .text
        )
    assert result["result"] is False
    assert "check.save(" not in stubs
    assert "Each program starts empty" in stubs


@pytest.mark.anyio
async def test_stubs_header_documents_save_when_a_store_is_set(monkeypatch):
    server = _server(monkeypatch, store=MemoryStore())
    async with Client(server) as client:
        stubs = (
            (await client.call_tool("get_stubs", {"toolset": "platform"}))
            .content[0]
            .text
        )
        resource = await client.read_resource("check://stubs")
    assert "Each program starts empty" in stubs
    assert 'await check.save("name",' in stubs
    assert 'check.load("name")' in stubs
    assert "check.save(" in resource[0].text
