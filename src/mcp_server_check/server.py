"""MCP server for the Check Payroll API."""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from mcp.server.fastmcp import FastMCP

from mcp_server_check.helpers import CheckContext
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


read_only = os.environ.get("CHECK_READ_ONLY", "").lower() in ("1", "true", "yes")

mcp = FastMCP("Check Payroll API", lifespan=lifespan)
register_all(mcp, read_only=read_only)


def main():
    if not os.environ.get("CHECK_API_KEY"):
        print("Error: CHECK_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    if read_only:
        print("Running in read-only mode (CHECK_READ_ONLY is set)", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
