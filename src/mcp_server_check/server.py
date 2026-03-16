"""MCP server for the Check Payroll API."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import Tool as MCPTool

from mcp_server_check.helpers import CheckContext
from mcp_server_check.tool_filter import ToolFilter
from mcp_server_check.tool_index import ToolIndex
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
        self._tool_index: ToolIndex | None = None

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
        if self._tool_index is not None:
            # Dynamic mode: the 3 meta-tools are always visible
            return all_tools
        tf = self._get_active_filter()
        return [
            t
            for t in all_tools
            if tf.is_tool_allowed(t.name, self._registry.get(t.name, ""))
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Sequence[Any]:
        """Call a tool, blocking if it's filtered out."""
        if self._tool_index is not None:
            # Dynamic mode: meta-tools handle their own filtering
            return await super().call_tool(name, arguments)
        tf = self._get_active_filter()
        toolset = self._registry.get(name, "")
        if not tf.is_tool_allowed(name, toolset):
            raise ToolError(
                f"Tool '{name}' is not available in the current configuration"
            )
        return await super().call_tool(name, arguments)


def _setup_dynamic_mode(server: CheckMCP) -> None:
    """Configure the server with 3 meta-tools instead of individual tools."""
    index = ToolIndex()
    index.build()
    server._tool_index = index

    @server.tool()
    def search_tools(
        query: str = "",
        toolset: str | None = None,
        limit: int = 20,
    ) -> str:
        """Search for available API tools by keyword.

        Returns matching tools with their full parameter schemas, ready for use
        with run_tool. Call with an empty query to see all available toolsets.
        Supports synonym matching (e.g. "pay employees" finds payroll tools).

        query: Search keywords (e.g. "list companies", "create employee", "payroll").
        toolset: Optional toolset name to restrict search (e.g. "companies", "employees").
        limit: Maximum number of results (default 20).
        """
        tf = server._get_active_filter()
        results = index.search(query, tool_filter=tf, toolset=toolset, limit=limit)
        return json.dumps(results, indent=2)

    @server.tool()
    def list_toolsets() -> str:
        """List all available API toolsets with descriptions.

        Returns a summary of each toolset including its name, description,
        tool count, and example tools. Use this to understand what's available
        before searching for specific tools.
        """
        tf = server._get_active_filter()
        results = index.search("", tool_filter=tf)
        return json.dumps(results, indent=2)

    @server.tool()
    async def run_tool(
        ctx: Context,
        tool_name: str,
        arguments: str | dict | None = None,
    ) -> str:
        """Execute an API tool by name with the given arguments.

        Use search_tools first to find the tool name and its parameter schema.

        tool_name: The exact tool name (e.g. "list_companies", "get_employee").
        arguments: Tool arguments as a JSON string or dict (e.g. '{"company_id": "com_xxx"}'
            or {"company_id": "com_xxx"}).
        """
        tf = server._get_active_filter()
        parsed_args: dict = {}
        if arguments is not None:
            if isinstance(arguments, str):
                try:
                    parsed_args = json.loads(arguments)
                except json.JSONDecodeError as e:
                    return json.dumps({"error": f"Invalid JSON arguments: {e}"})
                if not isinstance(parsed_args, dict):
                    return json.dumps({"error": "Arguments must be a JSON object"})
            elif isinstance(arguments, dict):
                parsed_args = arguments
            else:
                return json.dumps({"error": "Arguments must be a JSON string or object"})

        try:
            result = await index.run(
                name=tool_name,
                arguments=parsed_args,
                context=ctx,
                tool_filter=tf,
            )
        except ValueError as e:
            return json.dumps({"error": str(e)})

        return json.dumps(result) if isinstance(result, dict) else str(result)


def _register_resources(server: CheckMCP) -> None:
    """Register MCP resources for enum values and reference data."""
    from mcp_server_check.tool_index import _TOOLSET_DESCRIPTIONS
    from mcp_server_check.tools.companies import COMPANY_REPORT_TYPES
    from mcp_server_check.tools.components import (
        COMPANY_COMPONENTS,
        CONTRACTOR_COMPONENTS,
        EMPLOYEE_COMPONENTS,
    )

    # --- Enum resources ---

    _ENUMS: dict[str, dict] = {
        "business_type": {
            "description": "Valid values for the business_type field on companies.",
            "values": [
                "sole_proprietorship",
                "partnership",
                "c_corporation",
                "s_corporation",
                "llc",
            ],
        },
        "pay_frequency": {
            "description": "Valid values for pay_frequency on companies and payrolls.",
            "values": [
                "weekly",
                "biweekly",
                "semimonthly",
                "monthly",
                "quarterly",
                "annually",
            ],
        },
        "processing_period": {
            "description": "Valid values for processing_period on companies and payrolls.",
            "values": ["four_day", "three_day", "two_day", "one_day"],
        },
        "payment_method_preference": {
            "description": "Valid values for payment_method_preference on employees.",
            "values": ["direct_deposit", "manual"],
        },
        "payroll_type": {
            "description": "Valid values for the type field on payrolls.",
            "values": ["regular", "off_cycle", "amendment"],
        },
        "funding_payment_method": {
            "description": "Valid values for funding_payment_method on payrolls.",
            "values": ["ach", "wire"],
        },
        "bank_account_subtype": {
            "description": "Valid values for bank account subtype.",
            "values": ["checking", "savings"],
        },
        "report_type": {
            "description": "Valid report_type values for get_company_report.",
            "values": COMPANY_REPORT_TYPES,
        },
        "company_component_type": {
            "description": "Valid component_type values for company components.",
            "values": COMPANY_COMPONENTS,
        },
        "employee_component_type": {
            "description": "Valid component_type values for employee components.",
            "values": EMPLOYEE_COMPONENTS,
        },
        "contractor_component_type": {
            "description": "Valid component_type values for contractor components.",
            "values": CONTRACTOR_COMPONENTS,
        },
    }

    @server.resource("check://enums")
    def list_enums() -> str:
        """List all available enum types."""
        return json.dumps(
            {name: data["description"] for name, data in sorted(_ENUMS.items())},
            indent=2,
        )

    def _make_enum_handler(data: dict):
        def handler() -> str:
            return json.dumps(data, indent=2)

        return handler

    for enum_name, enum_data in _ENUMS.items():
        handler = _make_enum_handler(enum_data)
        handler.__name__ = f"enum_{enum_name}"
        handler.__qualname__ = f"enum_{enum_name}"
        server.resource(f"check://enums/{enum_name}", name=f"enum_{enum_name}")(handler)

    # --- Toolset reference ---

    @server.resource("check://toolsets")
    def list_toolset_descriptions() -> str:
        """Human-readable descriptions of all toolsets."""
        return json.dumps(_TOOLSET_DESCRIPTIONS, indent=2)


def _create_server() -> CheckMCP:
    """Create and configure the MCP server based on CHECK_TOOL_MODE."""
    server = CheckMCP("Check Payroll API", lifespan=lifespan)
    tool_mode = os.environ.get("CHECK_TOOL_MODE", "dynamic").lower()
    if tool_mode == "all":
        register_all(server, registry=server._registry)
    else:
        _setup_dynamic_mode(server)
    _register_resources(server)
    return server


mcp = _create_server()


def main():
    if not os.environ.get("CHECK_API_KEY"):
        print("Error: CHECK_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    tool_mode = os.environ.get("CHECK_TOOL_MODE", "dynamic").lower()
    if tool_mode != "all":
        print("Running in dynamic tool mode (3 meta-tools)", file=sys.stderr)
    else:
        print("Running in all-tools mode (legacy)", file=sys.stderr)
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
