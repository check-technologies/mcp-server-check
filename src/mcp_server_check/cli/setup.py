"""``check setup`` command — generates a CLAUDE.md file for AI coding agents."""

from __future__ import annotations

import os

import click

CLAUDE_MD_CONTENT = """\
# Check Payroll API

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
check companies list

# Get a specific company
check companies get --company com_abc123

# List employees for a company
check employees list --company com_abc123

# Preview a payroll
check payrolls preview --payroll prl_abc123

# Approve a payroll
check payrolls approve --payroll prl_abc123
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


@click.command("setup")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite the file without prompting.",
)
@click.option(
    "--file",
    "filename",
    default="CLAUDE.md",
    show_default=True,
    help="Output filename (e.g. AGENTS.md).",
)
@click.option(
    "--directory",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Target directory (default: current working directory).",
)
def setup_command(force: bool, filename: str, directory: str | None) -> None:
    """Generate a CLAUDE.md file with Check API context for AI coding agents."""
    target_dir = directory or os.getcwd()
    path = os.path.join(target_dir, filename)

    if os.path.exists(path) and not force:
        click.confirm(
            f"{filename} already exists in {target_dir}. Overwrite?", abort=True
        )

    with open(path, "w") as f:
        f.write(CLAUDE_MD_CONTENT)

    click.echo(f"Created {path}")
