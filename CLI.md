# Check CLI

A command-line interface for the [Check Payroll API](https://docs.checkhq.com/). The CLI exposes the same 263 endpoints as the MCP server, organized as resource-oriented commands similar to the [Stripe CLI](https://docs.stripe.com/cli).

## Installation

```bash
git clone https://github.com/check-technologies/mcp-server-check.git
cd mcp-server-check
uv sync
```

The `check` binary is installed in the project virtualenv. Run it with `uv run`:

```bash
uv run check --help
```

To install globally (no `uv run` prefix needed):

```bash
uv tool install -e .
check --help
```

## Authentication

Set your Check API key via environment variable or flag:

```bash
# Environment variable (recommended)
export CHECK_API_KEY=sk_test_...

# Or pass directly
uv run check --api-key sk_test_... companies list
```

## Quick Start

```bash
# List companies
check companies list

# Get a specific company
check companies get com_xxxxx

# Create a company
check companies create --legal-name "Acme Corp"

# List employees for a company
check employees list --company com_xxxxx

# Approve a payroll
check payrolls approve prl_xxxxx

# Get help for any command
check companies create --help
```

## Command Structure

Commands follow a `check <resource> <action>` pattern:

```
check <group> <command> [ARGS] [OPTIONS]
```

There are 17 resource groups, each with multiple commands:

| Group | Examples |
|---|---|
| `companies` | `list`, `get`, `create`, `update`, `onboard`, `get-paydays` |
| `employees` | `list`, `get`, `create`, `update`, `onboard`, `list-paystubs` |
| `payrolls` | `list`, `get`, `create`, `approve`, `preview`, `simulate-start-processing` |
| `contractors` | `list`, `get`, `create`, `update`, `onboard` |
| `bank-accounts` | `list`, `get`, `create`, `delete`, `reveal-number` |
| `compensation` | `list-pay-schedules`, `create-benefit`, `list-earning-codes` |
| `tax` | `get-company-params`, `list-employee-elections`, `list-filings` |
| `payments` | `list`, `get`, `retry`, `refund`, `cancel` |
| `payroll-items` | `list`, `get`, `create`, `update`, `delete` |
| `contractor-payments` | `list`, `get`, `create`, `delete` |
| `external-payrolls` | `list`, `get`, `create`, `approve` |
| `webhooks` | `list-configs`, `create-config`, `ping-config`, `retry-events` |
| `documents` | `list-company-tax-documents`, `download-employee-tax-document` |
| `components` | `create-company-run-payroll-component`, `create-employee-profile-component` |
| `forms` | `list`, `get`, `render`, `validate` |
| `platform` | `list-notifications`, `validate-address`, `sync-accounting` |
| `workplaces` | `list`, `get`, `create`, `update` |

Use `check <group> --help` to see all commands in a group.

## Global Options

```
--api-key TEXT              Check API key (or CHECK_API_KEY env var)
--env [sandbox|production]  API environment (default: sandbox; or CHECK_ENV)
--format [json|table]       Output format (default: json)
--read-only                 Block write operations (or CHECK_READ_ONLY)
--verbose                   Print request details to stderr
--version                   Show version
--help                      Show help
```

## Output Formats

**JSON (default)** — compact, pipe-friendly:

```bash
check companies get com_xxxxx
# {"id":"com_xxxxx","legal_name":"Acme Corp","status":"active",...}
```

**Table** — human-readable columns:

```bash
check companies list --format table
# ID         LEGAL_NAME   STATUS
# ---------  -----------  ------
# com_001    Acme Corp    active
# com_002    Beta Inc     pending
```

## Piping and Composability

The default JSON output is designed for piping:

```bash
# Extract employee IDs
check employees list --company com_xxxxx | jq '.results[].id'

# Count active companies
check companies list --active | jq '.results | length'

# Get details for each employee
check employees list --company com_xxxxx | jq -r '.results[].id' | \
  xargs -I{} check employees get {}
```

## Parameter Types

| Type | Syntax | Example |
|---|---|---|
| ID (positional) | `<value>` | `check companies get com_xxxxx` |
| String | `--option value` | `--legal-name "Acme Corp"` |
| Integer | `--option N` | `--limit 10` |
| Boolean flag | `--flag / --no-flag` | `--active` or `--no-active` |
| JSON object | `--option '{...}'` | `--address '{"line1":"123 Main"}'` |
| JSON from file | `--option @file.json` | `--address @addr.json` |
| JSON from stdin | `--option @-` | `echo '{}' \| check ... --data @-` |
| CSV list | `--option a,b,c` | `--ids com_001,com_002` |

## Environment Switching

By default the CLI connects to the Check **sandbox** (`https://sandbox.checkhq.com`). The sandbox supports simulation endpoints for advancing payrolls through processing states without real money movement.

```bash
# Sandbox (default)
check payrolls list

# Production
check --env production payrolls list

# Or via environment variable
export CHECK_ENV=production
check payrolls list

# Custom base URL
export CHECK_API_BASE_URL=https://api.checkhq.com
check payrolls list
```

## Filtering

The CLI supports the same filtering as the MCP server, via environment variables or flags.

### Read-Only Mode

Block all write/mutating commands:

```bash
# Via flag
check --read-only companies list          # works
check --read-only companies create ...    # command not found

# Via environment variable
export CHECK_READ_ONLY=1
check companies create ...                # command not found
```

In read-only mode, write commands are hidden from `--help` output.

### Toolset Filtering

Restrict the CLI to specific resource groups:

```bash
export CHECK_TOOLSETS=companies,employees
check companies list                      # works
check payrolls list                       # "No such command"
```

### Tool-Level Filtering

Allow or exclude individual commands by their tool function name:

```bash
# Allow only specific tools
export CHECK_TOOLS=list_companies,get_company

# Exclude specific tools
export CHECK_EXCLUDE_TOOLS=delete_company,delete_employee
```

**Filtering precedence:** `CHECK_EXCLUDE_TOOLS` > `CHECK_READ_ONLY` > `CHECK_TOOLS` > `CHECK_TOOLSETS`.

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | API error (4xx/5xx response) |
| 2 | Usage error (missing argument, unknown command) |
| 3 | Authentication error (no API key) |

Error details are printed to stderr, data to stdout, so pipes work correctly even on errors.

## Examples

### Payroll Workflow

```bash
# Create a payroll
check payrolls create \
  --company com_xxxxx \
  --period-start 2026-01-01 \
  --period-end 2026-01-15 \
  --payday 2026-01-20

# Add a payroll item
check payroll-items create \
  --payroll prl_xxxxx \
  --employee emp_xxxxx \
  --earnings '[{"amount":"5000.00","earning_code":"ec_xxxxx"}]'

# Preview the payroll
check payrolls preview prl_xxxxx

# Approve it
check payrolls approve prl_xxxxx

# Simulate processing (sandbox only)
check payrolls simulate-start-processing prl_xxxxx
check payrolls simulate-complete-funding prl_xxxxx
check payrolls simulate-complete-disbursements prl_xxxxx
```

### Employee Onboarding

```bash
# Create an employee
check employees create \
  --company com_xxxxx \
  --first-name Jane \
  --last-name Doe \
  --email jane@example.com \
  --start-date 2026-02-01

# Onboard them
check employees onboard emp_xxxxx

# Check their forms
check employees list-forms emp_xxxxx
```

### Reports

```bash
# Payroll journal
check companies get-payroll-journal-report com_xxxxx \
  --start-date 2026-01-01 --end-date 2026-03-31

# Tax liabilities
check companies get-tax-liabilities-report com_xxxxx \
  --start-date 2026-01-01 --end-date 2026-03-31

# W-2 preview
check companies get-w2-preview-report com_xxxxx --year 2025
```

### Webhooks

```bash
# List webhook configs
check webhooks list-configs

# Create a webhook
check webhooks create-config \
  --url https://example.com/webhooks \
  --environment sandbox

# Test it
check webhooks ping-config whc_xxxxx
```

## Comparison with MCP Server

The CLI and MCP server share the same tool functions — adding a new API endpoint updates both interfaces in one change.

| | MCP Server | CLI |
|---|---|---|
| **Interface** | MCP protocol (JSON-RPC) | Shell commands |
| **Best for** | AI assistants (Claude, Cursor) | Scripts, CI/CD, debugging |
| **Output** | Structured tool results | JSON or table to stdout |
| **Auth** | Environment variable | Flag, env var, or config |
| **Filtering** | Env vars + HTTP headers | Env vars + `--read-only` flag |
| **Entry point** | `mcp-server-check` | `check` |
