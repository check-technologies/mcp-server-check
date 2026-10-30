"""Shared test fixtures for the Check MCP server."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import pytest
import respx
from fastmcp import Context, FastMCP
from fastmcp.server.context import _current_context
from mcp.server.lowlevel.server import request_ctx
from mcp_server_check.helpers import CheckContext

BASE_URL = "https://sandbox.checkhq.com"


@dataclass
class FakeRequestContext:
    lifespan_context: CheckContext
    request: None = None


class FakeCtx:
    """Minimal stand-in for fastmcp Context that provides lifespan_context.

    Used for direct tool function calls in tests.
    """

    def __init__(self, check_ctx: CheckContext) -> None:
        self.request_context = FakeRequestContext(lifespan_context=check_ctx)


@pytest.fixture
def mock_api():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
        yield mock


@pytest.fixture
def ctx(mock_api):
    """Create a fake context with an httpx client routed through respx.

    Sets both the MCP request_ctx ContextVar (for lifespan_context access)
    and the fastmcp _current_context ContextVar (for FunctionTool.run()
    dependency injection).
    """
    client = httpx.AsyncClient(
        base_url=BASE_URL,
        headers={"Authorization": "Bearer test-key"},
        timeout=30.0,
    )
    check_ctx = CheckContext(client=client, base_url=BASE_URL)
    fake_ctx = FakeCtx(check_ctx)

    # Set MCP SDK ContextVar so ctx.request_context.lifespan_context works
    rc_token = request_ctx.set(fake_ctx.request_context)

    # Set fastmcp ContextVar so FunctionTool.run() can inject Context
    _server = FastMCP("test")
    real_context = Context(_server)
    ctx_token = _current_context.set(real_context)

    yield fake_ctx

    _current_context.reset(ctx_token)
    request_ctx.reset(rc_token)


MICROVM_IMAGE = "arn:aws:lambda:us-east-1:123456789012:microvm-image:test"


@pytest.fixture
def local_microvm(monkeypatch):
    """Run code-mode programs in a runner on a local port instead of a MicroVM.

    The runner gets its own thread and event loop, so it serves the host no
    matter which loop the test runs on. Yields the runner's port.
    """
    import asyncio
    import contextlib
    import threading

    from mcp_server_check import microvm_host, microvm_runner
    from websockets.asyncio.server import serve

    loop = asyncio.new_event_loop()
    started = threading.Event()
    state: dict = {}

    async def start() -> None:
        state["server"] = await serve(microvm_runner.handle, "127.0.0.1", 0)
        state["port"] = state["server"].sockets[0].getsockname()[1]

    def run() -> None:
        loop.run_until_complete(start())
        started.set()
        loop.run_forever()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    started.wait(5)
    port = state["port"]

    @contextlib.asynccontextmanager
    async def launch(image_arn, timeout):
        yield f"ws://127.0.0.1:{port}/", {}

    monkeypatch.setattr(microvm_host, "launch_microvm", launch)
    monkeypatch.setenv("CHECK_CODE_MICROVM_IMAGE", MICROVM_IMAGE)
    yield port

    async def stop() -> None:
        # Like terminating a MicroVM: a program still running is cut off.
        state["server"].close()
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
        await asyncio.sleep(0)

    asyncio.run_coroutine_threadsafe(stop(), loop).result(5)
    loop.call_soon_threadsafe(loop.stop)
    thread.join(5)
