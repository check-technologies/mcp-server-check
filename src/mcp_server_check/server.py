"""MCP server for the Check Payroll API."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import httpx
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools import FunctionTool
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server_check.helpers import CheckContext
from mcp_server_check.tool_filter import ToolFilter
from mcp_server_check.tool_index import ToolIndex
from mcp_server_check.tools import register_all

DEFAULT_BASE_URL = "https://sandbox.checkhq.com"

SERVER_INSTRUCTIONS = """\
You are connected to the Check Payroll API — a payroll infrastructure platform \
that lets you manage companies, employees, contractors, payrolls, tax filings, \
and payments programmatically.

**Important:** Use of this MCP server is subject to Check's MCP Usage Terms \
(see TERMS_OF_SERVICE.md). The user is responsible for all actions performed \
using their credentials, including actions taken by AI agents. Always confirm \
before executing write operations that affect payroll, money movement, or \
sensitive employee/contractor data.

## Entity Model
- **Company** → has Workplaces, Employees, Contractors, Pay Schedules, Bank Accounts
- **Employee** (W-2) → has Earning Rates, Benefits, Post-Tax Deductions, Tax Params, Forms
- **Contractor** (1099) → has Contractor Payments
- **Payroll** → has Payroll Items (one per employee) and Contractor Payments
- **Payroll Item** → has Earnings, Reimbursements, Benefit/Deduction overrides
- **Payment** → tracks actual money movement (ACH/wire), has Payment Attempts

## Key Workflows

### Creating a payroll (most common workflow):
1. Ensure the company has at least one Workplace and one Bank Account
2. Create the Payroll with period_start, period_end, and payday dates
3. Add Payroll Items (one per employee being paid), each with earnings
4. Add Contractor Payments for any 1099 contractors
5. Call preview_payroll to see calculated taxes and net pay
6. Call approve_payroll to submit for processing

### Onboarding a new company:
1. create_company with legal_name and address
2. create_workplace for each work location
3. create_employee / create_contractor for each worker
4. Set up bank_accounts for funding
5. Configure tax params and benefits
6. Call onboard_company when setup is complete

## Important Concepts
- **Payroll** is the batch container; **Payroll Item** is a single employee's pay stub within it
- **Earning Rate** defines an employee's pay rate; **Earning Code** defines the type of earning (regular, overtime, bonus, etc.)
- **Benefits** are pre-tax deductions (401k, health insurance); **Post-Tax Deductions** are after-tax (garnishments, Roth 401k)
- **Tax Params** control withholding (W-4 info, state elections); they use `spa_*` IDs
- Payrolls must be **approved** before they process — approval triggers real money movement
- All IDs use prefixes: `com_` (company), `emp_` (employee), `ctr_` (contractor), `prl_` (payroll), `pit_` (payroll item), `pmt_` (payment), `wrk_` (workplace), `bnk_` (bank account)

## Composite Tools (Use These First)
Prefer the workflow tools when they fit — they combine multiple API calls in one round-trip:
- **get_company_overview**: Company + employees + payrolls + bank accounts
- **get_employee_snapshot**: Employee + tax params + paystubs
- **diagnose_payment**: Payment + attempts + originating payroll item
- **get_payroll_details**: Payroll + all items + contractor payments
- **get_contractor_snapshot**: Contractor + payments + forms
- **get_company_tax_overview**: Company tax params + elections + filings
- **get_onboarding_status**: Company + workplaces + employees + bank accounts + setup requirements

## Common Gotchas
- You need a Workplace before you can add earnings to a payroll item
- Payroll period dates must not overlap with existing payrolls
- Bank accounts require verification before they can fund payrolls
- Employee SSNs are write-once; after setting, only last 4 digits are readable
- Tax parameter updates require the `spa_*` setting ID, not the parameter name
"""


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[CheckContext]:
    base_url = os.environ.get("CHECK_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    api_key = os.environ["CHECK_API_KEY"]
    try:
        pkg_version = version("mcp-server-check")
    except PackageNotFoundError:
        pkg_version = "dev"
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": f"mcp-server-check/{pkg_version}",
        },
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

        For HTTP transports, merges request-header overrides with the
        static (env-based) filter, taking the most restrictive value
        for each field.  The env filter acts as a policy floor that
        clients cannot relax.  For stdio, returns the static filter.
        """
        try:
            request = self._mcp_server.request_context.request
            if request is not None and hasattr(request, "headers"):
                header_filter = ToolFilter.from_headers(request.headers)
                if header_filter != ToolFilter():
                    return self._static_filter.merge(header_filter)
        except Exception:
            pass
        return self._static_filter

    async def list_tools(self, **kwargs: Any) -> Sequence[FunctionTool]:
        """List tools, filtered by the active configuration."""
        all_tools = await super().list_tools(**kwargs)
        if self._tool_index is not None:
            return all_tools
        tf = self._get_active_filter()
        return [
            t
            for t in all_tools
            if tf.is_tool_allowed(t.name, self._registry.get(t.name, ""))
        ]

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None, **kwargs: Any
    ) -> Any:
        """Call a tool, blocking if it's filtered out."""
        if self._tool_index is not None:
            return await super().call_tool(name, arguments, **kwargs)
        tf = self._get_active_filter()
        toolset = self._registry.get(name, "")
        if not tf.is_tool_allowed(name, toolset):
            raise ToolError(
                f"Tool '{name}' is not available in the current configuration"
            )
        return await super().call_tool(name, arguments, **kwargs)


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
        confirm: bool = False,
    ) -> str:
        """Execute an API tool by name with the given arguments.

        Use search_tools first to find the tool name and its parameter schema.

        tool_name: The exact tool name (e.g. "list_companies", "get_employee").
        arguments: Tool arguments as a JSON string or dict (e.g. '{"company_id": "com_xxx"}'
            or {"company_id": "com_xxx"}).
        confirm: Set to true to confirm execution of a destructive tool (approve,
            delete, simulate, refund, cancel). Required when CHECK_CONFIRM_DESTRUCTIVE
            is enabled and the tool is destructive.
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
                return json.dumps(
                    {"error": "Arguments must be a JSON string or object"}
                )

        if tf.requires_confirmation(tool_name) and not confirm:
            return json.dumps(
                {
                    "confirmation_required": True,
                    "tool_name": tool_name,
                    "arguments": parsed_args,
                    "message": (
                        f"⚠️  '{tool_name}' is a destructive operation that may "
                        f"trigger irreversible effects (money movement, data deletion, "
                        f"etc.). Call run_tool again with confirm=true to proceed."
                    ),
                }
            )

        try:
            result = await index.run(
                name=tool_name,
                arguments=parsed_args,
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


def setup_tools(server: CheckMCP, tool_mode: str = "dynamic") -> None:
    """Register tools, resources, and dynamic mode on a CheckMCP instance.

    This is the public entry point for configuring a CheckMCP server with
    all Check API tools.  The ``mcp-server-check-hosted`` package calls
    this on its own server instance to reuse the tool definitions.
    """
    if tool_mode == "all":
        register_all(server, registry=server._registry)
    else:
        _setup_dynamic_mode(server)
    _register_resources(server)


def _create_server() -> CheckMCP:
    """Create and configure the MCP server based on CHECK_TOOL_MODE."""
    server = CheckMCP(
        "Check Payroll API", instructions=SERVER_INSTRUCTIONS, lifespan=lifespan
    )
    tool_mode = os.environ.get("CHECK_TOOL_MODE", "dynamic").lower()
    setup_tools(server, tool_mode)
    return server


mcp = _create_server()

@mcp.custom_route("/health", methods=["GET"])
async def healthz(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


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
    mcp.run(transport=transport, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))


if __name__ == "__main__":
    main()
