"""MCP server for the Check Payroll API."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError, ValidationError
from fastmcp.tools import FunctionTool, ToolResult
from mcp.types import TextContent

from mcp_server_check.code_mode import (
    SANDBOX_MODULES,
    CallRecord,
    CodeRunner,
    render_catalog,
    render_stubs,
    render_trace,
)
from mcp_server_check.errors import CheckToolError
from mcp_server_check.helpers import CheckContext
from mcp_server_check.middleware import (
    RecoveryMiddleware,
    ResponseSizeLimitMiddleware,
    ToolCall,
    ToolErrorLogMiddleware,
)
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
- **Tax Elections** (`txe_*`) are exemptions from a specific tax (e.g. a minister exempt from Social Security/Medicare, a company exempt from SUI): check them with list_employee_tax_elections / list_company_tax_elections before escalating; if `exemptible` is true the partner can set it with the matching update tool, if false only Check Support can
- **Taxes** (`tax_`) and **Agencies** (`agc_`) are global read-only reference data — the levies themselves and the authorities Check files/remits to; look them up with list_taxes/list_agencies
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
- Report runs (`run_`) are asynchronous: create one, poll it until "completed" or "failed", then download — the download link expires in about a minute
- A report that times out or is too large to return fails with "alternatives" (complete calls that can still get it, such as response_format="csv" or a report run) and "hints" (advice that needs input only you have)
"""

CODE_MODE_INSTRUCTIONS = f"""\

## Code Mode
This server runs in code mode: every Check API call happens inside a Python \
program you write and run with run_code. A single call is a one-line program.
- The `check` module is already imported. It has one async function per \
Check tool, named as get_stubs lists them. Call them with keyword arguments \
and `await` them; use asyncio.gather for independent calls.
- Only the program's last expression, what it prints, and a trace of the tool \
calls it made come back. Filter, join, and aggregate inside the program and \
return a small result.
- A run_code result has two parts: the JSON result, then the list of tool \
calls the program made. When you report the result, tell the user which calls \
ran (tool, key arguments, and any failures), always for writes, so they can \
see what touched their account.
- Look up signatures first: get_stubs() with no arguments lists every toolset \
and its tool names; get_stubs(tools=[...]), get_stubs(toolset=...), or \
get_stubs(query="...") return signatures with docstrings. A program is \
type-checked against them before it runs, so a wrong name or argument fails \
before any API call is made; a doubt about an argument's type comes back as a \
warning with the result instead.
- Paginate with next_cursor until it is null. List results are summaries (key \
fields only); call the get_* tool for a full record.
- A failed API call raises RuntimeError whose message is a JSON object with \
status_code and detail; catch it to continue. Throttled calls, and reads whose \
connection dropped, are retried for you.
- Make the answer the program's last expression and let the server serialize \
it; do not json.dumps or print it. The sandbox is a Python subset: its only \
modules are {", ".join(SANDBOX_MODULES)} (json.dumps takes indent and \
sort_keys, not default); generator expressions evaluate eagerly to lists (use \
`next(iter(...))`); there are no third-party packages.
- Its asyncio has only gather(*coros) and sleep(): no Semaphore, wait_for, \
create_task, async with, or gather keyword arguments. Do not throttle or time \
out calls yourself; the server caps concurrent calls and retries throttled \
ones. There is also no async for, yield, class inheritance (so no custom \
exceptions, TypedDict, or NamedTuple), or del. When a program hits one of \
these limits, the error carries a hint; fix the program and rerun it.
- Write tools (create_*, update_*, approve_*, ...) are absent from `check` \
unless named in run_code's writes argument. Confirm with the user before \
running a program that declares writes, and keep reads and writes in separate \
programs where you can.
"""


# Dynamic mode registers both sets and shows one of them per request: the
# dynamic tools, or, when the active filter has code_mode set (CHECK_CODE_MODE=1
# for every request, the X-MCP-Code-Mode header or code_mode query parameter
# for one), only the code-mode tools, so every API call goes through run_code.
# CHECK_EXCLUDE_TOOLS still hides the code-mode tools, so a server can refuse
# the opt-in.
CODE_MODE_TOOLS: frozenset[str] = frozenset({"get_stubs", "run_code"})
DYNAMIC_TOOLS: frozenset[str] = frozenset({"search_tools", "list_toolsets", "run_tool"})


def _code_mode_tool_allowed(tf: ToolFilter, name: str) -> bool:
    return tf.code_mode and name not in tf.exclude_tools


def _code_mode_active(tf: ToolFilter) -> bool:
    """Whether this request runs in code mode, hiding the dynamic tools.

    A server that excludes the code-mode tools has refused the opt-in, so
    the dynamic tools stay available rather than leaving nothing to call.
    """
    return all(_code_mode_tool_allowed(tf, name) for name in CODE_MODE_TOOLS)


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
        self._code_runner: CodeRunner | None = None
        self.add_middleware(RecoveryMiddleware(self.is_tool_available))
        self.add_middleware(ToolErrorLogMiddleware())
        response_size_limit = ResponseSizeLimitMiddleware.from_env()
        if response_size_limit is not None:
            self.add_middleware(response_size_limit)

    def active_tool_filter(self) -> ToolFilter:
        """Return the filter for the current request.

        For HTTP transports, merges request-header and query-parameter
        overrides with the static (env-based) filter, taking the most
        restrictive value for each field.  The env filter acts as a
        policy floor that clients cannot relax.  For stdio, returns
        the static filter.
        """
        try:
            request = self._mcp_server.request_context.request
            if request is not None:
                result = self._static_filter
                if hasattr(request, "headers"):
                    header_filter = ToolFilter.from_headers(request.headers)
                    if header_filter != ToolFilter():
                        result = result.merge(header_filter)
                if hasattr(request, "query_params"):
                    qp_filter = ToolFilter.from_query_params(request.query_params)
                    if qp_filter != ToolFilter():
                        result = result.merge(qp_filter)
                return result
        except Exception:
            pass
        return self._static_filter

    def is_tool_available(self, name: str) -> bool:
        """Return whether the current request can call the Check tool name."""
        if self._tool_index is not None:
            entry = self._tool_index.get_entry(name)
            toolset = entry.toolset if entry is not None else None
        else:
            toolset = self._registry.get(name)
        return toolset is not None and self.active_tool_filter().is_tool_allowed(
            name, toolset
        )

    async def list_tools(self, **kwargs: Any) -> Sequence[FunctionTool]:
        """List tools, filtered by the active configuration."""
        all_tools = await super().list_tools(**kwargs)
        tf = self.active_tool_filter()
        if self._tool_index is not None:
            return [
                t
                for t in all_tools
                if (
                    _code_mode_tool_allowed(tf, t.name)
                    if t.name in CODE_MODE_TOOLS
                    else not (t.name in DYNAMIC_TOOLS and _code_mode_active(tf))
                )
            ]
        return [
            t
            for t in all_tools
            if tf.is_tool_allowed(t.name, self._registry.get(t.name, ""))
        ]

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None, **kwargs: Any
    ) -> Any:
        """Call a tool, blocking if it's filtered out."""
        tf = self.active_tool_filter()
        if self._tool_index is not None:
            if name in CODE_MODE_TOOLS and not tf.code_mode:
                raise ToolError(
                    f"Tool '{name}' is not available in the current configuration: "
                    "code mode is off. Enable it with CHECK_CODE_MODE=1, the "
                    "X-MCP-Code-Mode: 1 header, or the code_mode=1 query parameter."
                )
            if name in CODE_MODE_TOOLS and not _code_mode_tool_allowed(tf, name):
                raise ToolError(
                    f"Tool '{name}' is not available in the current configuration"
                )
            if name in DYNAMIC_TOOLS and _code_mode_active(tf):
                raise ToolError(
                    f"Tool '{name}' is not available in code mode. Use get_stubs to "
                    "find tools and run_code to call them."
                )
            return await super().call_tool(name, arguments, **kwargs)
        toolset = self._registry.get(name, "")
        if not tf.is_tool_allowed(name, toolset):
            raise ToolError(
                f"Tool '{name}' is not available in the current configuration"
            )
        return await super().call_tool(name, arguments, **kwargs)


def _setup_dynamic_mode(server: CheckMCP) -> None:
    """Configure the server with meta-tools instead of individual tools.

    Registers search_tools, list_toolsets, and run_tool, plus get_stubs and
    run_code. CheckMCP shows one set per request: the code-mode pair when the
    request's filter has code_mode on, the dynamic trio otherwise.
    """
    index = ToolIndex()
    index.build()
    server._tool_index = index
    runner = CodeRunner(index)
    server._code_runner = runner

    @server.tool(
        title="Search Tools",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
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
        tf = server.active_tool_filter()
        results = index.search(query, tool_filter=tf, toolset=toolset, limit=limit)
        return json.dumps(results, indent=2)

    @server.tool(
        title="List Toolsets",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    def list_toolsets() -> str:
        """List all available API toolsets with descriptions.

        Returns a summary of each toolset including its name, description,
        tool count, and example tools. Use this to understand what's available
        before searching for specific tools.
        """
        tf = server.active_tool_filter()
        results = index.search("", tool_filter=tf)
        return json.dumps(results, indent=2)

    @server.tool(
        name=ToolCall.RUN_TOOL,
        title="Run Tool",
        # Without a schema the result goes out once, as text, not also as
        # structuredContent.
        output_schema=None,
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "openWorldHint": False,
        },
    )
    async def run_tool(
        ctx: Context,
        tool_name: str,
        arguments: str | dict | None = None,
    ) -> ToolResult:
        """Execute an API tool by name with the given arguments.

        Use search_tools first to find the tool name and its parameter schema.
        A failed call returns a tool error whose message is a JSON object with
        "error" and, for Check API failures, "status_code" and "detail". A report
        that times out or is too large also lists "alternatives" to call instead
        and "hints".

        tool_name: The exact tool name (e.g. "list_companies", "get_employee").
        arguments: Tool arguments as a JSON string or dict (e.g. '{"company_id": "com_xxx"}'
            or {"company_id": "com_xxx"}).
        """
        tf = server.active_tool_filter()
        call = ToolCall.from_run_tool(tool_name, arguments)

        try:
            result = await index.run(
                name=tool_name,
                arguments=call.arguments,
                tool_filter=tf,
            )
        except (ValueError, ValidationError) as e:
            raise CheckToolError({"error": str(e)}) from e

        return ToolResult(content=result.content)

    @server.tool(
        title="Get Stubs",
        annotations={
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    def get_stubs(
        query: str | None = None,
        toolset: str | None = None,
        tools: list[str] | None = None,
        limit: int = 20,
    ) -> str:
        """Find the `check` module's tools and their typed Python signatures.

        With no arguments, returns the catalog: every toolset with its
        description and tool names (write tools marked with `*`). With any
        argument, returns a stub file: one `async def` per matching tool with
        its docstring. Start from the catalog, then fetch signatures for the
        tools you need; a whole toolset at a time is fine, the full set is not.
        Tools marked as write tools must be named in run_code's writes argument.

        query: Search keywords with synonym matching (e.g. "pay employees").
        toolset: Restrict to one toolset (e.g. "employees").
        tools: Restrict to specific tool names.
        limit: Most tools a query returns (default 20).
        """
        from mcp_server_check.tool_index import _TOOLSET_DESCRIPTIONS

        tf = server.active_tool_filter()
        if query is None and toolset is None and tools is None:
            return render_catalog(runner.visible_entries(tf), _TOOLSET_DESCRIPTIONS)
        if query:
            found = index.search(query, tool_filter=tf, toolset=toolset, limit=limit)
            names = [r["name"] for r in found if "name" in r]
            if tools:
                names = [n for n in names if n in set(tools)]
            if not names:
                return (
                    f"# No tools match {query!r}. Call get_stubs() for the catalog.\n"
                )
            tools = names
        return render_stubs(
            runner.visible_entries(tf, toolset=toolset, tools=tools), mark_writes=True
        )

    @server.tool(
        title="Run Code",
        output_schema=None,
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "openWorldHint": False,
        },
    )
    async def run_code(
        ctx: Context, code: str, writes: list[str] | None = None
    ) -> ToolResult:
        """Run a Python program against the Check API in a sandbox.

        Write ordinary async Python. The `check` module is already imported
        and has one async function per Check tool, named as get_stubs lists
        them; call them with keyword arguments and `await` them, and
        use asyncio.gather for independent calls. Top-level `await` is
        allowed. The value of the program's last expression is
        returned along with anything it printed and a trace of every tool call
        it made. Only what you return or print reaches the conversation, so
        filter and aggregate in the program, and make the answer the last
        expression rather than json.dumps-ing or printing it; the server
        serializes it.

        The result has two content blocks: the JSON result (result, logs,
        calls, duration_ms) and a readable list of the tool calls the program
        made. Each call is also sent as a progress notification as it
        finishes. Tell the user which calls ran when you report the result.

        Check the signatures first with get_stubs: the program
        is type-checked against them before it runs, so a wrong name or
        argument fails fast without touching the API, and a doubt about an
        argument's type is returned as a warning. A failed Check API call
        raises RuntimeError whose message is a JSON object with status_code
        and detail; catch it to continue. Throttled calls and reads whose
        connection dropped are retried. There is no network or filesystem
        access; only `check.*` calls leave the sandbox.

        code: The Python source to run.
        writes: Names of write tools (create_*, update_*, approve_*, ...) the
            program may call. Write tools not listed here are absent from
            `check`. Read tools never need listing.
        """
        tf = server.active_tool_filter()

        async def report(record: CallRecord, finished: int) -> None:
            await ctx.report_progress(progress=finished, message=record.summary())

        result = await runner.run(code, tf, writes or [], on_call=report)
        trace = render_trace(
            [CallRecord.from_dict(c) for c in result["calls"]], result["duration_ms"]
        )
        return ToolResult(
            content=[
                TextContent(
                    type="text", text=json.dumps(result, indent=2, default=str)
                ),
                TextContent(type="text", text=trace),
            ]
        )


def _register_resources(server: CheckMCP) -> None:
    """Register MCP resources for enum values and reference data."""
    from mcp_server_check.tool_index import _TOOLSET_DESCRIPTIONS
    from mcp_server_check.reports import ReportType
    from mcp_server_check.tools.compensation import BENEFIT_TYPES
    from mcp_server_check.tools.components import (
        COMPANY_COMPONENTS,
        CONTRACTOR_COMPONENTS,
        EMPLOYEE_COMPONENTS,
    )
    from mcp_server_check.tools.report_runs import REPORT_RUN_TYPES

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
        "benefit_type": {
            "description": "Valid values for the benefit field on benefits and company benefits.",
            "values": BENEFIT_TYPES,
        },
        "report_type": {
            "description": "Valid report_type values for get_company_report.",
            "values": [report_type.value for report_type in ReportType],
        },
        "report_run_type": {
            "description": (
                "Valid report values for create_report_run, and for the "
                "report_type filter on list_report_runs."
            ),
            "values": REPORT_RUN_TYPES,
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
        tf = server.active_tool_filter()
        return json.dumps(
            {
                name: description
                for name, description in _TOOLSET_DESCRIPTIONS.items()
                if tf.is_preview_enabled(name)
            },
            indent=2,
        )


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
    """Create and configure the MCP server from CHECK_TOOL_MODE and CHECK_CODE_MODE."""
    tool_mode = os.environ.get("CHECK_TOOL_MODE", "dynamic").lower()
    instructions = SERVER_INSTRUCTIONS
    if tool_mode != "all" and ToolFilter.from_env().code_mode:
        instructions += CODE_MODE_INSTRUCTIONS
    server = CheckMCP("Check Payroll API", instructions=instructions, lifespan=lifespan)
    setup_tools(server, tool_mode)
    return server


mcp = _create_server()


def main():
    if not os.environ.get("CHECK_API_KEY"):
        print("Error: CHECK_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    tool_mode = os.environ.get("CHECK_TOOL_MODE", "dynamic").lower()
    if tool_mode == "all":
        print("Running in all-tools mode (legacy)", file=sys.stderr)
        if mcp._static_filter.code_mode:
            print(
                "CHECK_CODE_MODE is ignored in all-tools mode (run_code needs "
                "CHECK_TOOL_MODE=dynamic)",
                file=sys.stderr,
            )
    elif mcp._static_filter.code_mode:
        print(
            "Running in code mode (get_stubs + run_code)",
            file=sys.stderr,
        )
    else:
        print(
            "Running in dynamic tool mode (3 meta-tools; CHECK_CODE_MODE=1 or the "
            "X-MCP-Code-Mode header switches to get_stubs + run_code)",
            file=sys.stderr,
        )
    if mcp._static_filter.read_only:
        print("Running in read-only mode (CHECK_READ_ONLY is set)", file=sys.stderr)
    if mcp._static_filter.toolsets:
        print(
            f"Active toolsets: {', '.join(sorted(mcp._static_filter.toolsets))}",
            file=sys.stderr,
        )
    if mcp._static_filter.preview_toolsets:
        print(
            "Preview toolsets enabled: "
            f"{', '.join(sorted(mcp._static_filter.preview_toolsets))}",
            file=sys.stderr,
        )
    transport = os.environ.get("CHECK_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
