"""MCP server for the Check Payroll API."""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import Tool as MCPTool

from mcp_server_check.helpers import CheckContext
from mcp_server_check.tool_filter import ToolFilter
from mcp_server_check.tools import register_all

DEFAULT_BASE_URL = "https://sandbox.checkhq.com"


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[CheckContext]:
    base_url = os.environ.get("CHECK_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    api_key = os.environ["CHECK_API_KEY"]
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0,
    ) as client:
        yield CheckContext(client=client, base_url=base_url)


class CheckMCP(FastMCP):
    """FastMCP subclass that applies toolset-based filtering at request time."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._registry: dict[str, str] = {}
        self._static_filter: ToolFilter = ToolFilter.from_env()

    def _get_active_filter(self) -> ToolFilter:
        """Return the filter for the current request.

        For HTTP transports, checks request headers and merges with the
        static (env-based) filter. For stdio, returns the static filter.
        """
        try:
            request = self._mcp_server.request_context.request
            if request is not None and hasattr(request, "headers"):
                header_filter = ToolFilter.from_headers(request.headers)
                # If headers provide any configuration, use it; otherwise fall back
                if header_filter != ToolFilter():
                    return header_filter
        except LookupError:
            pass
        return self._static_filter

    async def list_tools(self) -> list[MCPTool]:
        """List tools, filtered by the active configuration."""
        all_tools = await super().list_tools()
        tf = self._get_active_filter()
        return [
            t
            for t in all_tools
            if tf.is_tool_allowed(t.name, self._registry.get(t.name, ""))
        ]

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> Sequence[Any]:
        """Call a tool, blocking if it's filtered out."""
        tf = self._get_active_filter()
        toolset = self._registry.get(name, "")
        if not tf.is_tool_allowed(name, toolset):
            raise ToolError(f"Tool '{name}' is not available in the current configuration")
        return await super().call_tool(name, arguments)


mcp = CheckMCP("Check Payroll API", lifespan=lifespan)
register_all(mcp, registry=mcp._registry)


def main():
    if not os.environ.get("CHECK_API_KEY"):
        print("Error: CHECK_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    if mcp._static_filter.read_only:
        print("Running in read-only mode (CHECK_READ_ONLY is set)", file=sys.stderr)
    if mcp._static_filter.toolsets:
        print(
            f"Active toolsets: {', '.join(sorted(mcp._static_filter.toolsets))}",
            file=sys.stderr,
        )
    transport = os.environ.get("CHECK_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
