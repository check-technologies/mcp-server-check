"""Tests for the MicroVM code-mode backend.

A runner on a local port stands in for the MicroVM, so the WebSocket protocol
and the host's tool calls run without AWS. launch_microvm itself runs against
a fake boto3 client.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import threading

import httpx
import pytest
from mcp_server_check import microvm_host, microvm_runner
from mcp_server_check.server import CheckMCP, lifespan, setup_tools
from websockets.asyncio.server import serve

from tests.test_code_mode import COMPANIES, _run

ARN = "arn:aws:lambda:us-east-1:123456789012:microvm-image:test"


@pytest.fixture(autouse=True)
def code_env(monkeypatch):
    monkeypatch.setenv("CHECK_API_KEY", "test-key")
    monkeypatch.delenv("CHECK_API_BASE_URL", raising=False)
    monkeypatch.setenv("CHECK_CODE_TIMEOUT_SECS", "20")
    monkeypatch.setenv("CHECK_CODE_MODE", "1")
    monkeypatch.setenv("CHECK_CODE_MICROVM_IMAGE", ARN)


async def _run_in_microvm(monkeypatch, code: str, handler=microvm_runner.handle):
    # The runner starts inside the test, on the test's event loop: an async
    # fixture may run on another loop that never serves the connection.
    async with serve(handler, "127.0.0.1", 0) as ws_server:
        port = ws_server.sockets[0].getsockname()[1]

        @contextlib.asynccontextmanager
        async def launch(image_arn, timeout):
            yield f"ws://127.0.0.1:{port}/", {}

        monkeypatch.setattr(microvm_host, "launch_microvm", launch)
        server = CheckMCP("Test MicroVM", lifespan=lifespan)
        setup_tools(server)
        return await _run(server, code)


# --- the runner and the host, over a local WebSocket ---


def test_last_expression_becomes_result():
    namespace: dict = {}
    exec(microvm_runner.compile_program("x = 2\nx * 21"), namespace)
    assert namespace["__result__"] == 42


@pytest.mark.anyio
async def test_runs_full_python(mock_api, monkeypatch):
    mock_api.get("/companies").mock(return_value=httpx.Response(200, json=COMPANIES))
    for cid, state in (("com_1", "CA"), ("com_2", "NY")):
        mock_api.get(f"/companies/{cid}").mock(
            return_value=httpx.Response(
                200, json={"id": cid, "legal_name": "x", "address": {"state": state}}
            )
        )
    code = """
import asyncio
from collections import Counter

class Missing(KeyError):
    pass

limit = asyncio.Semaphore(2)

async def state(cid):
    async with limit:
        company = await check.get_company(company_id=cid)
    return next(s for s in [company["address"]["state"]])

page = await check.list_companies(limit=2)
states = await asyncio.gather(*[state(c["id"]) for c in page["results"]])
print("fetched", len(states))
dict(Counter(states))
"""
    is_error, payload = await _run_in_microvm(monkeypatch, code)

    assert not is_error, payload
    assert payload["result"] == {"CA": 1, "NY": 1}
    assert payload["logs"] == "fetched 2\n"
    assert [c["tool"] for c in payload["calls"]] == [
        "list_companies",
        "get_company",
        "get_company",
    ]


@pytest.mark.anyio
async def test_api_error_is_catchable(mock_api, monkeypatch):
    mock_api.get("/companies/com_missing").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )
    code = """
import json
try:
    await check.get_company(company_id="com_missing")
except RuntimeError as e:
    outcome = json.loads(str(e))["status_code"]
outcome
"""
    is_error, payload = await _run_in_microvm(monkeypatch, code)
    assert not is_error, payload
    assert payload["result"] == 404
    assert payload["calls"][0]["error"]["status_code"] == 404


@pytest.mark.anyio
async def test_undeclared_write_is_not_in_the_module(mock_api, monkeypatch):
    is_error, payload = await _run_in_microvm(
        monkeypatch, 'await check.create_company(legal_name="x")'
    )
    assert is_error
    assert payload["kind"] == "runtime_error"
    assert "create_company" in payload["detail"]
    assert payload["calls"] == []
    assert mock_api.calls.call_count == 0


@pytest.mark.anyio
async def test_host_refuses_forged_write(monkeypatch, mock_api):
    """Code that reaches the socket still cannot call an undeclared write."""

    async def forge(ws):
        await ws.recv()
        call = {"type": "call", "id": 1, "tool": "create_company", "args": []}
        await ws.send(json.dumps({**call, "kwargs": {"legal_name": "x"}}))
        reply = json.loads(await ws.recv())
        await ws.send(json.dumps({"type": "done", "value": reply, "logs": ""}))

    is_error, payload = await _run_in_microvm(monkeypatch, "1", forge)

    assert not is_error, payload
    assert payload["result"]["type"] == "error"
    assert "not callable" in payload["result"]["message"]
    assert mock_api.calls.call_count == 0


@pytest.mark.anyio
async def test_host_does_not_trust_a_forged_failure_kind(monkeypatch):
    async def forge(ws):
        await ws.recv()
        failed = {"type": "failed", "kind": "timeout", "detail": "x", "logs": ""}
        await ws.send(json.dumps(failed))

    is_error, payload = await _run_in_microvm(monkeypatch, "1", forge)
    assert is_error
    assert payload["kind"] == "runtime_error"


@pytest.mark.anyio
async def test_syntax_error(monkeypatch):
    is_error, payload = await _run_in_microvm(monkeypatch, "x = (")
    assert is_error
    assert payload["kind"] == "syntax_error"


@pytest.mark.anyio
async def test_runtime_error_keeps_logs_and_line(monkeypatch):
    is_error, payload = await _run_in_microvm(monkeypatch, "print('hi')\n\n1 / 0")
    assert is_error
    assert payload["kind"] == "runtime_error"
    assert payload["logs"] == "hi\n"
    assert 'File "<program>", line 3' in payload["detail"]
    assert "ZeroDivisionError" in payload["detail"]


@pytest.mark.anyio
async def test_sys_exit_keeps_logs(monkeypatch):
    is_error, payload = await _run_in_microvm(
        monkeypatch, "import sys\nprint('hi')\nsys.exit(3)"
    )
    assert is_error
    assert payload["kind"] == "runtime_error"
    assert payload["logs"] == "hi\n"
    assert "SystemExit" in payload["detail"]


@pytest.mark.anyio
async def test_call_budget_hint(mock_api, monkeypatch):
    monkeypatch.setenv("CHECK_CODE_MAX_CALLS", "1")
    mock_api.get("/companies").mock(return_value=httpx.Response(200, json=COMPANIES))
    code = "await check.list_companies()\nawait check.list_companies()"
    is_error, payload = await _run_in_microvm(monkeypatch, code)
    assert is_error
    assert "budget of 1 tool calls" in payload["detail"]
    assert "Split the work" in payload["hint"]


@pytest.mark.anyio
async def test_timeout(monkeypatch):
    monkeypatch.setenv("CHECK_CODE_TIMEOUT_SECS", "1")
    is_error, payload = await _run_in_microvm(
        monkeypatch, "import asyncio\nawait asyncio.sleep(5)"
    )
    assert is_error
    assert payload["kind"] == "timeout"


@pytest.mark.anyio
async def test_dates_serialize_as_strings(monkeypatch):
    is_error, payload = await _run_in_microvm(
        monkeypatch, "from datetime import date\n{'day': date(2026, 1, 5)}"
    )
    assert not is_error, payload
    assert payload["result"] == {"day": "2026-01-05"}


# --- launch_microvm against a fake boto3 client ---


class _FakeMicrovms:
    """The lambda-microvms client calls launch_microvm makes."""

    def __init__(self, states, run_started=None):
        self.states = list(states)
        self.run_started = run_started
        self.release = threading.Event()
        self.calls: list[str] = []

    def run_microvm(self, **kwargs):
        self.calls.append("run")
        if self.run_started is not None:
            self.run_started.set()
            self.release.wait(5)
        return {"microvmId": "mvm-1", "state": "PENDING", "endpoint": "mvm-1.example"}

    def get_microvm(self, **kwargs):
        self.calls.append("get")
        return {"state": self.states.pop(0)}

    def create_microvm_auth_token(self, **kwargs):
        self.calls.append("token")
        return {"authToken": {"X-aws-proxy-auth": "tok"}}

    def terminate_microvm(self, **kwargs):
        self.calls.append("terminate")


@pytest.fixture
def use_fake(monkeypatch):
    def install(fake):
        monkeypatch.setattr(microvm_host, "_client", lambda region: fake)
        monkeypatch.setattr(microvm_host, "POLL_SECS", 0)
        return fake

    return install


@pytest.mark.anyio
async def test_launch_waits_for_running_then_mints_token(use_fake):
    fake = use_fake(_FakeMicrovms(["PENDING", "RUNNING"]))

    async with microvm_host.launch_microvm(ARN, 10) as (url, headers):
        assert url == "wss://mvm-1.example/"
        assert headers == {"X-aws-proxy-auth": "tok"}
    assert fake.calls == ["run", "get", "get", "token", "terminate"]


@pytest.mark.anyio
async def test_launch_terminates_a_microvm_that_never_runs(use_fake):
    fake = use_fake(_FakeMicrovms(["TERMINATED"]))

    with pytest.raises(RuntimeError, match="TERMINATED"):
        async with microvm_host.launch_microvm(ARN, 10):
            pass
    assert fake.calls == ["run", "get", "terminate"]


@pytest.mark.anyio
async def test_launch_cancelled_during_run_still_terminates(use_fake):
    started = threading.Event()
    fake = use_fake(_FakeMicrovms(["RUNNING"], run_started=started))

    async def launch():
        async with microvm_host.launch_microvm(ARN, 10):
            pass

    task = asyncio.create_task(launch())
    await asyncio.to_thread(started.wait, 5)
    task.cancel()
    # RunMicrovm returns after the cancel, as a slow AWS call would.
    fake.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert fake.calls == ["run", "terminate"]
