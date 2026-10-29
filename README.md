# mcp-server-check

> **⚠️ Early Access Beta** — This MCP server is currently in beta and available to select partners. APIs, tools, and behavior may change without notice. Please share feedback with your Check point of contact.

> **Terms of Service** — By using this MCP server to access the Check API, you agree to the [MCP Usage Terms](TERMS_OF_SERVICE.md), which are in addition to your existing agreement with Check.

An [MCP](https://modelcontextprotocol.io/) server that wraps the [Check Payroll API](https://docs.checkhq.com/), providing 286 tools for managing companies, employees, contractors, payrolls, tax configuration, embedded components, and more.

## Quickstart

```bash
git clone https://github.com/check-technologies/mcp-server-check.git
cd mcp-server-check
uv sync
CHECK_API_KEY=your-key uv run mcp-server-check
```

## Configuration

| Environment Variable | Required | Default | Description |
|---|---|---|---|
| `CHECK_API_KEY` | Yes | — | Your Check API key (Bearer token) |
| `CHECK_API_BASE_URL` | No | `https://sandbox.checkhq.com` | API base URL |
| `CHECK_TOOL_MODE` | No | `dynamic` | Tool mode: `dynamic` (3 meta-tools) or `all` (all tools individually) |
| `CHECK_CODE_MODE` | No | — | Set to `1`, `true`, or `yes` to replace dynamic mode's three meta-tools with `get_stubs` and `run_code` (see [Code Mode](#code-mode-experimental)); a remote client can opt in per request with the `X-MCP-Code-Mode` header instead |
| `CHECK_CODE_TIMEOUT_SECS` | No | `60` | Code mode: wall-clock budget for one `run_code` program |
| `CHECK_CODE_MAX_CALLS` | No | `200` | Code mode: most tool calls one program may make |
| `CHECK_CODE_CONCURRENCY` | No | `8` | Code mode: most tool calls one program runs at once |
| `CHECK_CODE_MAX_RETRIES` | No | `8` | Code mode: retries of a throttled (HTTP 429) call, or of a read whose connection dropped, before the program sees the error |
| `CHECK_CODE_MAX_PROGRAMS` | No | `4` | Code mode: most programs (each in its own sandbox) one server runs at once; more wait their turn |
| `CHECK_TOOLSETS` | No | — | Comma-separated list of toolsets to enable (e.g. `companies,employees`) |
| `CHECK_TOOLS` | No | — | Comma-separated allowlist of individual tool names |
| `CHECK_EXCLUDE_TOOLS` | No | — | Comma-separated list of tool names to hide |
| `CHECK_READ_ONLY` | No | — | Set to `1`, `true`, or `yes` to disable all write/mutating tools |
| `CHECK_EXCLUDE_MONEY_MOVEMENT` | No | — | Set to `1`, `true`, or `yes` to remove tools that move funds or change funding/payout destinations |
| `CHECK_EXCLUDE_DESTRUCTIVE` | No | — | Set to `1`, `true`, or `yes` to remove irreversible tools (delete, approve, cancel, refund, simulate) |
| `CHECK_PREVIEW_TOOLSETS` | No | — | Comma-separated list of [preview toolsets](#preview-toolsets) to enable |
| `CHECK_TRANSPORT` | No | `stdio` | Transport protocol: `stdio`, `sse`, or `streamable-http` |
| `CHECK_MAX_RESPONSE_BYTES` | No | `6000000` | Largest tool result to return; a bigger one becomes a tool error listing ways to narrow it. `0` disables the check |
| `CHECK_MAX_RESULT_CHARS` | No | `50000` | Most characters of a tool result to hand the model. A longer list result keeps the records that fit, with `results_omitted` and a hint to page; any other longer result becomes a tool error listing ways to narrow it. `0` disables the budget |

### Sandbox vs Production

By default the server connects to the **Check sandbox** (`https://sandbox.checkhq.com`), which is safe for testing and development. The sandbox supports simulation endpoints (e.g. `simulate_start_processing`, `simulate_complete_funding`) that let you advance payrolls through processing states without real money movement.

To point at production, set:

```bash
CHECK_API_BASE_URL=https://api.checkhq.com
```

### Server Configuration

The server supports fine-grained tool filtering, configurable via environment variables (for stdio) or HTTP headers (for SSE / streamable-http). This follows the [GitHub MCP Server configuration pattern](https://github.com/github/github-mcp-server).

| Feature | Environment Variable | HTTP Header |
|---|---|---|
| Toolsets | `CHECK_TOOLSETS` | `X-MCP-Toolsets` |
| Individual tools | `CHECK_TOOLS` | `X-MCP-Tools` |
| Exclude tools | `CHECK_EXCLUDE_TOOLS` | `X-MCP-Exclude-Tools` |
| Read-only | `CHECK_READ_ONLY` | `X-MCP-Readonly` |
| Exclude money movement | `CHECK_EXCLUDE_MONEY_MOVEMENT` | `X-MCP-Exclude-Money-Movement` |
| Exclude destructive | `CHECK_EXCLUDE_DESTRUCTIVE` | `X-MCP-Exclude-Destructive` |
| Preview toolsets | `CHECK_PREVIEW_TOOLSETS` | `X-MCP-Preview-Toolsets` (or the `preview_toolsets` query parameter) |
| Code mode | `CHECK_CODE_MODE` | `X-MCP-Code-Mode` (or the `code_mode` query parameter) |

**Filtering precedence:** `exclude_tools` > category exclusions (money movement, destructive) > `preview_toolsets` > `read_only` > `tools` > `toolsets`. Exclude always wins; category exclusions apply even to tools named in the `tools` allowlist; a preview toolset stays hidden until it is opted into, even if `tools` or `toolsets` names it; if `tools` is set it acts as an allowlist independent of toolsets.

#### Toolsets

There are 21 toolsets, one per API module: `agencies`, `bank_accounts`, `companies`, `compensation`, `components`, `contractor_payments`, `contractors`, `documents`, `employees`, `external_payrolls`, `forms`, `logs`, `payments`, `payroll_items`, `payrolls`, `platform`, `report_runs`, `tax`, `webhooks`, `workflows`, `workplaces`.

Enable only specific toolsets:

```bash
CHECK_TOOLSETS=companies,employees CHECK_API_KEY=your-key uv run mcp-server-check
```

#### Individual Tools

Allow only specific tools by name:

```bash
CHECK_TOOLS=list_companies,get_company,list_employees CHECK_API_KEY=your-key uv run mcp-server-check
```

#### Excluding Tools

Hide specific tools while keeping everything else:

```bash
CHECK_EXCLUDE_TOOLS=create_company,delete_company CHECK_API_KEY=your-key uv run mcp-server-check
```

#### Read-Only Mode

Set `CHECK_READ_ONLY=1` to run the server with only read-only tools (list, get, download, preview, etc.). All create, update, delete, and other mutating tools are excluded. This is useful when you want to allow exploration of your Check data without risk of modifications.

```bash
CHECK_READ_ONLY=1 CHECK_API_KEY=your-key uv run mcp-server-check
```

#### Preview Toolsets

Toolsets for APIs still being piloted with specific partners are hidden unless the client opts in. No toolset is in preview at the moment (corrections left preview when the Corrections API became generally available, so the `X-MCP-Preview-Toolsets: corrections` header is no longer needed and is ignored). When one is, opt in with any of:

```bash
# Local (stdio)
CHECK_PREVIEW_TOOLSETS=<toolset> CHECK_API_KEY=your-key uv run mcp-server-check
```

```
# Remote: HTTP header
X-MCP-Preview-Toolsets: <toolset>

# Remote: query parameter, for clients that can only be configured with a URL
https://<server>/mcp?preview_toolsets=<toolset>
```

Opting in works the same in sandbox and production, and either the server or the client can do it. Once enabled, the toolset behaves like any other: read-only mode, `exclude_tools`, `toolsets`, and category exclusions still apply. Opting in only makes the tools visible — the Check API still decides per partner whether the underlying endpoints are available, so a partner without access gets "not found" or "feature unavailable" errors.

#### Category Exclusions

Two flags remove whole categories of tools from a deployment. Unlike `CHECK_EXCLUDE_TOOLS`, they do not need updating as tools are added.

`CHECK_EXCLUDE_MONEY_MOVEMENT=1` removes the tools that move funds or change where funds are drawn from and sent to: `approve_payroll`, `retry_payment`, `refund_payment`, `cancel_payment`, and `create`/`update`/`delete_bank_account`.

`CHECK_EXCLUDE_DESTRUCTIVE=1` removes tools with irreversible effects — everything matching `delete_`, `bulk_delete_`, `approve_`, `cancel_`, `refund_`, `simulate_`, plus `start_implementation`, `cancel_implementation`, `sync_accounting`, and `reopen_correction`.

```bash
CHECK_EXCLUDE_MONEY_MOVEMENT=1 CHECK_EXCLUDE_DESTRUCTIVE=1 CHECK_API_KEY=your-key uv run mcp-server-check
```

With both set, an agent can still prepare a payroll run (`create_payroll`, `create_payroll_item`, `create_contractor_payment`, `preview_payroll`) but cannot approve or disburse it, and cannot add or repoint a bank account. Excluded tools are hidden from `list_tools` and `search_tools`, and calling one directly returns an error before any API request is made.

#### HTTP Headers (Remote Transport)

When running with `CHECK_TRANSPORT=sse` or `CHECK_TRANSPORT=streamable-http`, clients can pass configuration via HTTP headers:

```
X-MCP-Toolsets: companies,employees
X-MCP-Readonly: true
X-MCP-Exclude-Tools: create_company,delete_company
X-MCP-Exclude-Money-Movement: true
X-MCP-Exclude-Destructive: true
```

Header and environment settings are merged, taking the most restrictive value for each. A client can narrow what the server exposes but never widen it: if the server sets `CHECK_READ_ONLY=1` or a category exclusion, no header can turn it off. Preview toolsets and [code mode](#code-mode-experimental) are the exceptions: either side can opt in.

### Dynamic Tool Mode (Default)

By default, the server runs in dynamic mode (`CHECK_TOOL_MODE=dynamic`), exposing 3 meta-tools instead of all individual tools. This avoids sending every tool schema to the LLM upfront, saving significant context window space.

- **`search_tools(query, toolset?, limit?)`** — Search for tools by keyword with synonym matching. Returns matching tools with their full parameter schemas.
- **`list_toolsets()`** — List all available toolsets with descriptions and example tools.
- **`run_tool(tool_name, arguments?)`** — Execute a tool by name with a dict of arguments.

The LLM workflow becomes: browse toolsets or search for relevant tools → review their parameter schemas → call `run_tool` with the correct arguments. All filtering (`CHECK_TOOLSETS`, `CHECK_READ_ONLY`, etc.) is applied at both the search and execution layers.

Set `CHECK_TOOL_MODE=all` to expose all tools individually (legacy mode):

```bash
CHECK_TOOL_MODE=all CHECK_API_KEY=your-key uv run mcp-server-check
```

### Code Mode (experimental)

Code mode follows the pattern described by [Cloudflare](https://blog.cloudflare.com/code-mode/) and [Rippling](https://www.rippling.com/blog/building-mcp-server): instead of one tool call per API request, the model writes a short Python program that calls many tools and returns only the answer. Intermediate results never pass through the model's context.

Each program runs in an isolated VM, so code mode is available only on a server configured to start one, such as the hosted Check MCP. On a local install, `CHECK_CODE_MODE`, the header, and the query parameter have no effect, and the server keeps the dynamic-mode tools.

A dynamic-mode server can also switch it on per request, which lets a remote deployment roll it out client by client:

```
# Remote: header
X-MCP-Code-Mode: 1

# Remote: query parameter, for clients that can only be configured with a URL
https://<server>/mcp?code_mode=1
```

Without the header, a dynamic-mode server lists only the three meta-tools and refuses calls to `run_code` and `get_stubs`. With it, only `get_stubs` and `run_code` are listed and the three meta-tools are refused, so every API call goes through a program. To refuse the opt-in, set `CHECK_EXCLUDE_TOOLS=run_code,get_stubs` on the server. The code-mode server instructions are only sent when the server itself sets `CHECK_CODE_MODE`; a client enabling it by header relies on the tool descriptions. Code mode is part of dynamic mode, so it has no effect under `CHECK_TOOL_MODE=all`.

Code mode replaces the three dynamic-mode tools with two, so every API call goes through a program:

- **`get_stubs(query?, toolset?, tools?)`** — With no arguments, the catalog: every toolset with its description and tool names, write tools marked with `*`. With a keyword `query`, a `toolset`, or a list of `tools`, typed Python signatures (with docstrings) for the `check` module, one `async def` per tool.
- **`run_code(code, writes?)`** — Run a program. The `check` module is pre-imported and exposes every allowed tool as an async function; the program's last expression is returned along with anything it printed and a trace of every tool call it made (tool, arguments, status, duration).

```python
import asyncio

page = await check.list_employees(company="com_xxx", limit=100)
snapshots = await asyncio.gather(
    *[check.get_employee(employee_id=e["id"]) for e in page["results"]]
)
[e["id"] for e in snapshots if not e.get("bank_accounts")]
```

How it works:

1. **Stubs come from the tool functions.** `code_mode.render_stubs` introspects the same functions `run_tool` runs (signature, defaults, docstring) and renders a `.pyi`-style stub file for the `check` module. There is no second catalog to keep in sync; a new tool gets a stub automatically.
2. **Each program gets a fresh sandbox.** `run_code` starts an isolated VM for the program, sends it the program and the names of the tools it may call, and terminates the VM when the program ends. The program runs in CPython with the standard library, and the `check` module inside the VM sends each call back to the server.
3. **Calls proxy back to the host.** When the program awaits `check.list_employees(...)`, the host runs the tool through `ToolIndex.run`, so validation, the `ToolFilter`, and error conversion apply as they do for `run_tool`. MCP middleware runs once, around `run_code` itself, so failed reports inside a program don't get recovery `alternatives` or `hints`, and the server logs a failed program's call trace without its arguments, output, or source. Only the tool's result crosses back into the sandbox; the API key never does.
4. **The result is the program's last expression** plus captured `print` output and a call trace (tool, arguments, status, duration). A failed API call raises `RuntimeError` inside the sandbox with the usual JSON error payload, so a program can catch it and continue; an uncaught error returns the trace so far.
5. **Every call is visible.** The trace comes back as its own content block, one line per call, and the server instructions tell the model to repeat it when reporting the result. While the program runs, each finished call is also sent as an MCP progress notification (`list_employees(company='com_x') ok 340ms`), which clients that request progress, such as Claude Code, show on the running tool. MCP has no per-call approval inside a program; that is what the `writes` declaration is for.

Guardrails:

- The sandbox never sees the API key; every `check.*` call proxies to the same tool function `run_tool` would run, through the same `ToolFilter`, so `CHECK_READ_ONLY`, toolsets, and category exclusions apply unchanged.
- Write tools are absent from `check` unless the program names them in `run_code`'s `writes` argument, which keeps every write visible in the client's tool-call stream before it runs. A declared write that the filter hides is an error.
- Programs run in CPython with the standard library and no third-party packages. The program's last expression is the answer, serialized by the server, so programs rarely need `json` at all. A program that calls a tool missing from `check` gets a note saying whether the tool doesn't exist, is hidden by the server's configuration, or is a write it didn't declare.
- Each program gets its own sandbox with a time budget, a call budget, and a concurrency cap on API calls, and the server runs at most `CHECK_CODE_MAX_PROGRAMS` of them at once (see the `CHECK_CODE_*` variables in the configuration table). When a program ends with calls still in flight (a timeout, or one call of a `gather` failing), the host cancels them and they show `"status": "pending"` in the trace; a pending write may already have landed. Throttled calls (HTTP 429) are retried by the host with the wait the API asks for, and one throttled call pauses every call of the program for that long, so a `gather` of a hundred calls drains at the rate the API allows instead of each call discovering the limit on its own. A read whose connection dropped is retried the same way; a write is not, since it may have landed. The trace records the retries.

## Usage with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "check": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-server-check", "mcp-server-check"],
      "env": {
        "CHECK_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Usage with Claude Code

```bash
claude mcp add check -- uv run --directory /path/to/mcp-server-check mcp-server-check
```

Then set the `CHECK_API_KEY` environment variable in your shell before running Claude Code.

## Available Tools

286 tools organized across 21 categories. All list tools support `limit` and `cursor` parameters for cursor-based pagination — pass the `cursor` value from a previous response to fetch the next page.

### Companies (26 tools)

| Tool | Method | Description |
|---|---|---|
| `list_companies` | GET | List companies with optional filters |
| `get_company` | GET | Get details for a specific company |
| `create_company` | POST | Create a new company |
| `update_company` | PATCH | Update an existing company |
| `onboard_company` | POST | Onboard a company to active status |
| `get_company_paydays` | GET | Get upcoming paydays for a company |
| `list_company_tax_deposits` | GET | List tax deposits for a company |
| `get_company_benefit_aggregations` | GET | Get benefit aggregations for a company |
| `get_company_report` | GET | Get a company report by `report_type`, as JSON rows or, with `response_format="csv"`, the smaller CSV rendering. A request that times out or is too large to return fails with `alternatives` (such as a [Report Run](#report-runs-4-tools) or the CSV rendering) and `hints` |
| `list_federal_ein_verifications` | GET | List federal EIN verifications |
| `get_federal_ein_verification` | GET | Get a specific EIN verification |
| `list_signatories` | GET | List signatories for a company |
| `create_signatory` | POST | Create a signatory |
| `get_enrollment_profile` | GET | Get enrollment profile |
| `create_enrollment_profile` | PUT | Create enrollment profile |
| `update_enrollment_profile` | PATCH | Update enrollment profile |
| `start_implementation` | POST | Start implementation for a company |
| `cancel_implementation` | POST | Cancel implementation |
| `request_embedded_setup` | POST | Request embedded setup |

### Employees (17 tools)

| Tool | Method | Description |
|---|---|---|
| `list_employees` | GET | List employees with optional filters |
| `get_employee` | GET | Get details for a specific employee |
| `create_employee` | POST | Create a new employee |
| `update_employee` | PATCH | Update an existing employee |
| `onboard_employee` | POST | Onboard an employee to active status |
| `list_employee_paystubs` | GET | List paystubs for an employee |
| `get_employee_paystub` | GET | Get a specific paystub |
| `list_employee_forms` | GET | List forms for an employee |
| `get_employee_form` | GET | Get a specific employee form |
| `submit_employee_form` | POST | Submit an employee form |
| `sign_and_submit_employee_form` | POST | Sign and submit an employee form |
| `get_employee_company_defined_attributes` | GET | Get company-defined attributes |
| `update_employee_company_defined_attributes` | PATCH | Update company-defined attributes |
| `get_employee_reciprocity_elections` | GET | Get reciprocity elections |
| `update_employee_reciprocity_elections` | PATCH | Update reciprocity elections |
| `reveal_employee_ssn` | GET | Reveal employee SSN |
| `authorize_employee_partner` | POST | Authorize a partner for an employee |

### Contractors (10 tools)

| Tool | Method | Description |
|---|---|---|
| `list_contractors` | GET | List contractors with optional filters |
| `get_contractor` | GET | Get details for a specific contractor |
| `create_contractor` | POST | Create a new contractor |
| `update_contractor` | PATCH | Update an existing contractor |
| `onboard_contractor` | POST | Onboard a contractor to active status |
| `list_contractor_payments_for_contractor` | GET | List payments for a contractor |
| `get_contractor_payment_for_payroll` | GET | Get contractor payment for a payroll |
| `list_contractor_forms` | GET | List forms for a contractor |
| `submit_contractor_form` | POST | Submit a contractor form |
| `reveal_contractor_ssn` | GET | Reveal contractor SSN/EIN |

### Workplaces (4 tools)

| Tool | Method | Description |
|---|---|---|
| `list_workplaces` | GET | List workplaces |
| `get_workplace` | GET | Get details for a specific workplace |
| `create_workplace` | POST | Create a new workplace |
| `update_workplace` | PATCH | Update an existing workplace |

### Payrolls (15 tools)

| Tool | Method | Description |
|---|---|---|
| `list_payrolls` | GET | List payrolls with optional filters |
| `get_payroll` | GET | Get details for a specific payroll; items are omitted unless `include_items=true` |
| `create_payroll` | POST | Create a new payroll |
| `update_payroll` | PATCH | Update an existing payroll |
| `delete_payroll` | DELETE | Delete a payroll |
| `preview_payroll` | GET | Preview a payroll before approval; per-item previews are omitted unless `include_items=true` |
| `approve_payroll` | POST | Approve a payroll for processing |
| `reopen_payroll` | POST | Reopen a previously approved payroll |
| `get_payroll_paper_checks` | GET | Get paper checks for a payroll |
| `get_payroll_cash_requirement_report` | GET | Get cash requirement report |
| `get_payroll_paper_checks_report` | GET | Get paper checks report |
| `simulate_start_processing` | POST | Simulate starting processing (sandbox) |
| `simulate_complete_funding` | POST | Simulate completing funding (sandbox) |
| `simulate_fail_funding` | POST | Simulate failing funding (sandbox) |
| `simulate_complete_disbursements` | POST | Simulate completing disbursements (sandbox) |

### Payroll Items (8 tools)

| Tool | Method | Description |
|---|---|---|
| `list_payroll_items` | GET | List payroll items |
| `get_payroll_item` | GET | Get details for a specific payroll item |
| `create_payroll_item` | POST | Create a new payroll item |
| `update_payroll_item` | PATCH | Update an existing payroll item |
| `bulk_update_payroll_items` | PATCH | Bulk update payroll items |
| `delete_payroll_item` | DELETE | Delete a payroll item |
| `bulk_delete_payroll_items` | DELETE | Bulk delete payroll items |
| `get_payroll_item_paper_check` | GET | Get paper check for a payroll item |

### Contractor Payments (6 tools)

| Tool | Method | Description |
|---|---|---|
| `list_contractor_payments` | GET | List contractor payments |
| `get_contractor_payment` | GET | Get details for a specific payment |
| `create_contractor_payment` | POST | Create a new contractor payment |
| `update_contractor_payment` | PATCH | Update a contractor payment |
| `delete_contractor_payment` | DELETE | Delete a contractor payment |
| `get_contractor_payment_paper_check` | GET | Get paper check for a payment |

### External Payrolls (8 tools)

| Tool | Method | Description |
|---|---|---|
| `list_external_payrolls` | GET | List external payrolls; line items are omitted unless `include_items=true` |
| `get_external_payroll` | GET | Get details for a specific external payroll; items are omitted unless `include_items=true` |
| `create_external_payroll` | POST | Create a new external payroll |
| `update_external_payroll` | PATCH | Update an external payroll |
| `delete_external_payroll` | DELETE | Delete an external payroll |
| `approve_external_payroll` | POST | Approve an external payroll |
| `reopen_external_payroll` | POST | Reopen an external payroll |
| `preview_external_payroll` | GET | Preview an external payroll |

### Corrections (18 tools)

Correct a company's past payrolls: create a draft correction, void or add payrolls to it, preview it, then approve. Access is enabled per partner on the Check API; a partner without it gets a "feature unavailable" error.

| Tool | Method | Description |
|---|---|---|
| `list_corrections` | GET | List corrections; filter by company, year, status, or payroll |
| `get_correction` | GET | Get a correction, including its operations, totals, and preview and approval state |
| `get_correction_receipt` | GET | Get the tax rollup for a previewed correction |
| `get_correction_receipt_download` | GET | Get a short-lived presigned URL for the correction receipt PDF |
| `create_correction` | POST | Create a draft correction for a company and tax year |
| `update_correction` | PATCH | Update a draft correction's settlement date, bank account, description, metadata, or simulation mode |
| `delete_correction` | DELETE | Delete a draft correction |
| `void_payroll` | POST | Void a paid payroll, or part of it, as part of a draft correction |
| `add_payroll_to_correction` | POST | Add a new payroll to a draft correction, e.g. to replace a voided one or record a missed one |
| `add_external_payroll` | POST | Add a new external payroll to a draft correction |
| `preview_correction` | POST | Price a draft correction without moving money |
| `create_correction_payroll_journal_run` | POST | Start a payroll journal report run for a previewed correction |
| `create_correction_payroll_summary_run` | POST | Start a payroll summary report run for a previewed correction |
| `approve_correction` | POST | Approve a draft correction, committing its payroll changes and moving money |
| `reopen_correction` | POST | Cancel a pending correction's approval and return it to draft |
| `simulate_correction_start_processing` | POST | Simulate starting correction processing (sandbox only) |
| `simulate_correction_complete_funding` | POST | Simulate completing correction funding (sandbox only) |
| `simulate_correction_fail_funding` | POST | Simulate failing correction funding (sandbox only) |

### Compensation (32 tools)

Pay schedules, benefits, post-tax deductions, company benefits, earning rates, earning codes, and net pay splits.

| Tool | Method | Description |
|---|---|---|
| **Pay Schedules** | | |
| `list_pay_schedules` | GET | List pay schedules |
| `get_pay_schedule` | GET | Get a specific pay schedule |
| `create_pay_schedule` | POST | Create a new pay schedule |
| `update_pay_schedule` | PATCH | Update a pay schedule |
| `delete_pay_schedule` | DELETE | Delete a pay schedule |
| `get_pay_schedule_paydays` | GET | Get paydays for a pay schedule |
| **Benefits** | | |
| `list_benefits` | GET | List employee benefits |
| `get_benefit` | GET | Get a specific benefit |
| `create_benefit` | POST | Create an employee benefit |
| `update_benefit` | PATCH | Update a benefit |
| `delete_benefit` | DELETE | Delete a benefit |
| **Post-Tax Deductions** | | |
| `list_post_tax_deductions` | GET | List post-tax deductions |
| `get_post_tax_deduction` | GET | Get a specific post-tax deduction |
| `create_post_tax_deduction` | POST | Create a post-tax deduction |
| `update_post_tax_deduction` | PATCH | Update a post-tax deduction |
| `delete_post_tax_deduction` | DELETE | Delete a post-tax deduction |
| **Company Benefits** | | |
| `list_company_benefits` | GET | List company-level benefits |
| `get_company_benefit` | GET | Get a specific company benefit |
| `create_company_benefit` | POST | Create a company benefit |
| `update_company_benefit` | PATCH | Update a company benefit |
| `delete_company_benefit` | DELETE | Delete a company benefit |
| **Earning Rates** | | |
| `list_earning_rates` | GET | List earning rates |
| `get_earning_rate` | GET | Get a specific earning rate |
| `create_earning_rate` | POST | Create an earning rate |
| `update_earning_rate` | PATCH | Update an earning rate |
| **Earning Codes** | | |
| `list_earning_codes` | GET | List earning codes |
| `get_earning_code` | GET | Get a specific earning code |
| `create_earning_code` | POST | Create an earning code |
| `update_earning_code` | PATCH | Update an earning code |
| **Net Pay Splits** | | |
| `list_net_pay_splits` | GET | List net pay splits |
| `get_net_pay_split` | GET | Get a specific net pay split |
| `create_net_pay_split` | POST | Create a net pay split |

### Bank Accounts (6 tools)

| Tool | Method | Description |
|---|---|---|
| `list_bank_accounts` | GET | List bank accounts |
| `get_bank_account` | GET | Get a specific bank account |
| `create_bank_account` | POST | Create a new bank account |
| `update_bank_account` | PATCH | Update a bank account |
| `delete_bank_account` | DELETE | Delete a bank account |
| `reveal_bank_account_number` | GET | Reveal full account number |

### Documents (19 tools)

| Tool | Method | Description |
|---|---|---|
| **Company Tax Documents** | | |
| `list_company_tax_documents` | GET | List company tax documents |
| `get_company_tax_document` | GET | Get a specific company tax document |
| `download_company_tax_document` | GET | Download a company tax document as text (PDF text layer or CSV) |
| **Company Authorization Documents** | | |
| `list_company_authorization_documents` | GET | List authorization documents |
| `get_company_authorization_document` | GET | Get an authorization document |
| `download_company_authorization_document` | GET | Download an authorization document as text (PDF text layer or CSV) |
| **Employee Tax Documents** | | |
| `list_employee_tax_documents` | GET | List employee tax documents |
| `get_employee_tax_document` | GET | Get an employee tax document |
| `download_employee_tax_document` | GET | Download an employee tax document as text (PDF text layer or CSV) |
| **Contractor Tax Documents** | | |
| `list_contractor_tax_documents` | GET | List contractor tax documents |
| `get_contractor_tax_document` | GET | Get a contractor tax document |
| `download_contractor_tax_document` | GET | Download a contractor tax document as text (PDF text layer or CSV) |
| **Setup Documents** | | |
| `list_setup_documents` | GET | List setup documents |
| `get_setup_document` | GET | Get a setup document |
| `download_setup_document` | GET | Download a setup document as text (PDF text layer or CSV); `sensitive_*` types are refused |
| **Company Provided Documents** | | |
| `list_company_provided_documents` | GET | List company-provided documents |
| `get_company_provided_document` | GET | Get a company-provided document |
| `create_company_provided_document` | POST | Create a company-provided document |
| `upload_company_provided_document_file` | POST | Upload a file for a document |

### Report Runs (4 tools)

Asynchronous reporting. `create_report_run` returns a `run_` ID, `get_report_run` polls it until the status is `completed` or `failed`, and `download_report_run` returns a link to a ZIP of CSVs. Unlike `get_company_report`, a run is not scoped to one company unless you pass `company`.

| Tool | Method | Description |
|---|---|---|
| `list_report_runs` | GET | List report runs; filter by company, `report_type`, and status |
| `get_report_run` | GET | Get a report run and its current status |
| `download_report_run` | GET | Get a presigned download link, valid for about 60 seconds |
| `create_report_run` | POST | Start a `payroll_journal` or `payroll_summary` run over a payday range |

### Forms (4 tools)

| Tool | Method | Description |
|---|---|---|
| `list_forms` | GET | List forms across all companies; filter by company, state, city, language, and form type |
| `get_form` | GET | Get a specific form |
| `render_form` | GET | Render a form for display |
| `validate_form` | POST | Validate form data before submission |

### Logs (2 tools)

| Tool | Method | Description |
|---|---|---|
| `list_logs` | GET | List API request logs; filter by path, method, status code/class, log ID, idempotency key, and time range |
| `get_log` | GET | Get the full record for a single API request log |

### Payments (6 tools)

| Tool | Method | Description |
|---|---|---|
| `list_payments` | GET | List payments |
| `get_payment` | GET | Get a specific payment |
| `list_payment_attempts` | GET | List payment attempts |
| `retry_payment` | POST | Retry a failed payment |
| `refund_payment` | POST | Refund a payment |
| `cancel_payment` | POST | Cancel a payment |

### Tax (31 tools)

Tax parameters, elections (including tax exemptions), filings, statements, packages, and tax reference data.

| Tool | Method | Description |
|---|---|---|
| **Company Tax Params** | | |
| `get_company_tax_params` | GET | Get tax parameters for a company |
| `update_company_tax_params` | PATCH | Update company tax parameters |
| `list_company_tax_param_settings` | GET | List tax parameter settings |
| `get_company_tax_param_setting` | GET | Get a specific tax param setting |
| **Employee Tax Params** | | |
| `list_employee_tax_params` | GET | List employee tax parameters |
| `get_employee_tax_params` | GET | Get tax parameters for an employee |
| `update_employee_tax_params` | PATCH | Update employee tax parameters |
| `list_employee_tax_param_settings` | GET | List employee tax param settings |
| `get_employee_tax_param_setting` | GET | Get a specific setting |
| `bulk_get_employee_tax_param_settings` | POST | Bulk get tax param settings |
| `bulk_update_employee_tax_param_settings` | POST | Bulk update tax param settings |
| **Company Tax Elections** | | |
| `list_company_tax_elections` | GET | List a company's tax exemptions (tax elections) for employer-paid taxes; `exemptible: false` (e.g. SUI/FUTA) means only Check Support can set it |
| `create_company_tax_elections` | POST | Create company tax elections |
| `update_company_tax_elections` | PATCH | Set or remove a company's exemption from an employer-paid tax |
| **Employee Tax Elections** | | |
| `list_employee_tax_elections` | GET | List an employee's tax exemptions (Social Security, Medicare/FICA, income tax withholding, …); includes the employer halves of FICA |
| `update_employee_tax_elections` | PATCH | Set or remove an employee's tax exemption (e.g. minister/clergy FICA exemption) — no Support request needed when `exemptible` is true |
| **Filings** | | |
| `list_filings` | GET | List tax filings |
| `get_filing` | GET | Get a specific tax filing |
| `add_filing_blockers` | POST | Add blockers to a filing |
| `remove_filing_blockers` | POST | Remove blockers from a filing |
| **Employee Tax Statements** | | |
| `list_employee_tax_statements` | GET | List employee tax statements |
| `get_employee_tax_statement` | GET | Get a specific tax statement |
| **Employee Tax Statement Overrides** | | |
| `list_employee_tax_statement_overrides` | GET | List W-2 supplement overrides (requires company or employee filter) |
| `get_employee_tax_statement_override` | GET | Get a specific override |
| `create_employee_tax_statement_overrides` | POST | Upsert overrides by employee and year |
| `update_employee_tax_statement_override` | PATCH | Update override values |
| `delete_employee_tax_statement_override` | DELETE | Delete an override |
| **Tax Packages** | | |
| `request_tax_package` | POST | Request a tax package |
| `get_tax_package` | GET | Get a specific tax package |
| **Taxes (reference data)** | | |
| `list_taxes` | GET | List tax objects (payroll levies); filter by jurisdiction, payer, supported/remittable, effective status |
| `get_tax` | GET | Get a specific tax object |

### Agencies (2 tools)

The counterparties Check files and remits to (IRS, state revenue departments). Global read-only reference data.

| Tool | Method | Description |
|---|---|---|
| `list_agencies` | GET | List agencies; filter by jurisdiction or label |
| `get_agency` | GET | Get a specific agency |

### Webhooks (7 tools)

| Tool | Method | Description |
|---|---|---|
| `list_webhook_configs` | GET | List webhook configurations |
| `get_webhook_config` | GET | Get a specific webhook configuration |
| `create_webhook_config` | POST | Create a webhook configuration |
| `update_webhook_config` | PATCH | Update a webhook configuration |
| `delete_webhook_config` | DELETE | Delete a webhook configuration |
| `ping_webhook_config` | POST | Send a test ping |
| `list_webhook_deliveries` | GET | List webhook deliveries with status + attempts |
| `get_webhook_delivery` | GET | Get a webhook delivery |
| `retry_webhook_delivery` | POST | Re-enqueue a webhook delivery (sandbox only) |

### Platform (28 tools)

Notifications, communications, usage, integrations, accounting, company groups, addresses, setups, and requirements.

| Tool | Method | Description |
|---|---|---|
| **Notifications** | | |
| `list_notifications` | GET | List notifications |
| `get_notification` | GET | Get a specific notification |
| **Communications** | | |
| `list_communications` | GET | List communications |
| `get_communication` | GET | Get a specific communication |
| `create_communication` | POST | Create a communication |
| **Usage** | | |
| `list_usage_summaries` | GET | List usage summaries |
| `list_usage_records` | GET | List usage records |
| **Integrations** | | |
| `list_integration_partners` | GET | List integration partners |
| `get_integration_partner` | GET | Get a specific integration partner |
| `authorize_integration_partner` | POST | Authorize an integration partner |
| `list_integration_permissions` | GET | List integration permissions |
| `get_integration_permission` | GET | Get a specific permission |
| `list_integration_accesses` | GET | List integration accesses |
| **Accounting** | | |
| `list_accounting_integrations` | GET | List accounting integrations for a company |
| `list_accounting_accounts` | GET | List the QuickBooks chart of accounts |
| `refresh_accounting_accounts` | POST | Re-pull the chart of accounts from QuickBooks |
| `get_accounting_mappings` | GET | Get category mappings |
| `update_accounting_mappings` | PATCH | Update accounting mappings |
| `toggle_accounting_mappings` | POST | Toggle accounting mappings |
| `sync_accounting` | POST | Queue payrolls to sync to QuickBooks |
| `list_accounting_sync_attempts` | GET | List sync attempts with status and failure reason |
| **Company Groups** | | |
| `list_company_groups` | GET | List company groups |
| **Addresses** | | |
| `validate_address` | POST | Validate an address |
| **Setups** | | |
| `list_setups` | GET | List setups |
| `get_setup` | GET | Get a specific setup |
| **Requirements** | | |
| `list_requirements` | GET | List requirements |
| `get_requirement` | GET | Get a specific requirement |
| **Reports** | | |
| `get_applied_for_ids_report` | GET | Get applied-for IDs report |

### Embedded Components (35 tools)

Generate embeddable UI component URLs via `POST /{entity_type}/{entity_id}/components/{component_type}`. All tools accept an `entity_id` and optional `data` configuration.

**Company components (25):**
`create_company_previous_provider_access_component`, `create_company_accounting_integration_component`, `create_company_authorization_documents_component`, `create_company_business_details_component`, `create_company_checklist_component`, `create_company_company_reports_component`, `create_company_connect_bank_account_component`, `create_company_details_component`, `create_company_early_enrollment_component`, `create_company_employee_setup_component`, `create_company_filing_authorization_component`, `create_company_filing_preview_component`, `create_company_full_service_setup_submission_component`, `create_company_integrations_component`, `create_company_integrations_authorize_component`, `create_company_pay_history_component`, `create_company_payment_setup_component`, `create_company_progress_tracker_component`, `create_company_run_payroll_component`, `create_company_signatory_agreements_component`, `create_company_tax_documents_component`, `create_company_tax_setup_component`, `create_company_team_setup_component`, `create_company_terms_of_service_component`, `create_company_verification_documents_component`

**Employee components (9):**
`create_employee_benefits_component`, `create_employee_payment_setup_component`, `create_employee_paystubs_component`, `create_employee_post_tax_deductions_component`, `create_employee_profile_component`, `create_employee_ssn_setup_component`, `create_employee_tax_documents_component`, `create_employee_tax_setup_component`, `create_employee_withholdings_setup_component`

**Contractor components (1):**
`create_contractor_tax_documents_component`

## Development

```bash
git clone https://github.com/check-technologies/mcp-server-check.git
cd mcp-server-check
uv sync --group dev
uv run pytest  # 311 tests
```

### Pre-commit hooks

This repo ships a [pre-commit](https://pre-commit.com/) config that runs `ruff check`
and `ruff format` (the same checks as CI) before each commit. Enable it once after
cloning:

```bash
uv run pre-commit install
```

To run the hooks manually against all files: `uv run pre-commit run --all-files`.
