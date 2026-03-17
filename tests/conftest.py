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
