"""``check setup`` command — configures AI coding agents with Check API context."""

from __future__ import annotations

import json
import os
import shutil

import click

# Sentinel used to detect whether a file already has Check CLI instructions.
CHECK_SENTINEL = "<!-- check-cli -->"

# Permission entry written to .claude/settings.json.
BASH_CHECK_PERMISSION = "Bash(check *)"

# Paths (relative to project root) where Claude settings may live.
_SETTINGS_PATHS = [
    os.path.join(".claude", "settings.json"),
    os.path.join(".claude", "settings.local.json"),
]

# Target name → default filename
_TARGET_FILES: dict[str, str] = {
    "claude-code": "CLAUDE.md",
    "cursor": ".cursorrules",
    "agents-md": "AGENTS.md",
}

INSTRUCTIONS_TEMPLATE = """\
# Check Payroll API

{sentinel}

This project integrates with the [Check Payroll API](https://docs.checkhq.com/), \
a payroll infrastructure platform for managing companies, employees, contractors, \
payrolls, tax filings, and payments programmatically.

## Entity Model

- **Company** → has Workplaces, Employees, Contractors, Pay Schedules, Bank Accounts
- **Employee** (W-2) → has Earning Rates, Benefits, Post-Tax Deductions, Tax Parameters, Forms
- **Contractor** (1099) → has Contractor Payments
- **Payroll** → has Payroll Items (one per employee) and Contractor Payments
- **Payroll Item** → has Earnings, Reimbursements, Benefit/Deduction overrides
- **Payment** → tracks actual money movement (ACH/wire), has Payment Attempts

## Key Workflows

### Creating a payroll

1. Ensure the company has at least one Workplace and one Bank Account
2. Create the Payroll with period_start, period_end, and payday dates
3. Add Payroll Items (one per employee being paid), each with earnings
4. Add Contractor Payments for any 1099 contractors
5. Preview the payroll to see calculated taxes and net pay
6. Approve the payroll to submit for processing

### Onboarding a new company

1. Create the company with legal_name and address
2. Create a workplace for each work location
3. Create employees and/or contractors for each worker
4. Set up bank accounts for funding
5. Configure tax parameters and benefits
6. Call the onboard endpoint when setup is complete

## ID Prefixes

All Check API resources use prefixed IDs:

| Prefix | Resource |
|--------|----------|
| `com_` | Company |
| `emp_` | Employee |
| `ctr_` | Contractor |
| `prl_` | Payroll |
| `pit_` | Payroll Item |
| `pmt_` | Payment |
| `wrk_` | Workplace |
| `bnk_` | Bank Account |
| `ern_` | Earning Rate |
| `erc_` | Earning Code |
| `ben_` | Benefit |
| `ptd_` | Post-Tax Deduction |
| `spa_` | Tax Parameter Setting |

## Important Concepts

- **Payroll** is the batch container; **Payroll Item** is a single employee's \
pay stub within it.
- **Earning Rate** defines an employee's pay rate; **Earning Code** defines the \
type of earning (regular, overtime, bonus, etc.).
- **Benefits** are pre-tax deductions (401k, health insurance); **Post-Tax \
Deductions** are after-tax (garnishments, Roth 401k).
- **Tax Parameters** control withholding (W-4 info, state elections); they use \
`spa_*` IDs.
- Payrolls must be **approved** before they process — approval triggers real \
money movement.

## Common Gotchas

- You need a Workplace before you can add earnings to a payroll item.
- Payroll period dates must not overlap with existing payrolls.
- Bank accounts require verification before they can fund payrolls.
- Employee SSNs are write-once; after setting, only the last 4 digits are readable.
- Tax parameter updates require the `spa_*` setting ID, not the parameter name.

## CLI Quick Reference

```bash
# List companies
{cmd_prefix}check companies list

# Get a specific company
{cmd_prefix}check companies get --company com_abc123

# List employees for a company
{cmd_prefix}check employees list --company com_abc123

# Preview a payroll
{cmd_prefix}check payrolls preview --payroll prl_abc123

# Approve a payroll
{cmd_prefix}check payrolls approve --payroll prl_abc123
```

## MCP Server Setup

To give AI agents direct access to the Check API, add the MCP server:

```bash
claude mcp add check -- uvx mcp-server-check
```

Set your API key:

```bash
export CHECK_API_KEY=sk_test_...
```

## API Documentation

Full API reference: https://docs.checkhq.com/
"""


def _check_is_on_path() -> bool:
    """Return True if ``check`` is available as a command on PATH."""
    return shutil.which("check") is not None


def _render_content() -> str:
    """Render the instructions template with the correct command prefix."""
    cmd_prefix = "" if _check_is_on_path() else "uv run "
    return INSTRUCTIONS_TEMPLATE.format(sentinel=CHECK_SENTINEL, cmd_prefix=cmd_prefix)


def _file_has_check_instructions(path: str) -> bool:
    """Return True if *path* already contains Check CLI instructions."""
    try:
        with open(path) as f:
            return CHECK_SENTINEL in f.read()
    except OSError:
        return False


def _has_bash_check_permission(directory: str) -> bool:
    """Return True if any Claude settings file allows ``Bash(check *)``."""
    for rel in _SETTINGS_PATHS:
        settings_path = os.path.join(directory, rel)
        try:
            with open(settings_path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        allow_list = data.get("permissions", {}).get("allow", [])
        for entry in allow_list:
            # Match exact "Bash(check *)" or legacy "Bash(check:*)" or broader
            # patterns like "Bash(uv run check *)" / "Bash(uv run check:*)".
            if entry.startswith("Bash(") and "check" in entry:
                return True
    return False


def _ensure_bash_check_permission(directory: str) -> bool:
    """Add ``Bash(check *)`` to ``.claude/settings.json`` if not already present.

    Returns True if the permission was added, False if it was already present.
    """
    if _has_bash_check_permission(directory):
        return False

    settings_path = os.path.join(directory, ".claude", "settings.json")
    data: dict = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}

    permissions = data.setdefault("permissions", {})
    allow_list = permissions.setdefault("allow", [])
    allow_list.append(BASH_CHECK_PERMISSION)

    os.makedirs(os.path.join(directory, ".claude"), exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    return True


def _append_or_create(path: str, content: str) -> str:
    """Append *content* to *path*, creating it if it doesn't exist.

    Returns ``"Appended to"`` or ``"Created"`` for use in the output message.
    """
    if os.path.exists(path):
        with open(path, "a") as f:
            f.write("\n" + content)
        return "Appended to"
    else:
        with open(path, "w") as f:
            f.write(content)
        return "Created"


@click.command("setup")
@click.argument(
    "target",
    type=click.Choice(sorted(_TARGET_FILES.keys())),
)
@click.option(
    "--directory",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Target directory (default: current working directory).",
)
def setup_command(target: str, directory: str | None) -> None:
    """Generate AI agent config for Check API.

    \b
    Targets:
      claude-code   Append to CLAUDE.md + add Bash(check *) to .claude/settings.json
      cursor        Append to .cursorrules
      agents-md     Append to AGENTS.md
    """
    target_dir = directory or os.getcwd()
    filename = _TARGET_FILES[target]
    path = os.path.join(target_dir, filename)

    # Early exit if the file already contains Check instructions.
    if _file_has_check_instructions(path):
        click.echo(f"{filename} already has Check CLI instructions — skipping.")
        return

    content = _render_content()
    verb = _append_or_create(path, content)
    click.echo(f"{verb} {path}")

    # For claude-code, also ensure the Bash permission is set.
    if target == "claude-code":
        if _ensure_bash_check_permission(target_dir):
            settings_path = os.path.join(target_dir, ".claude", "settings.json")
            click.echo(f"Added {BASH_CHECK_PERMISSION} to {settings_path}")
