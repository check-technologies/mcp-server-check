# mcp-server-check

> **⚠️ Early Access Beta** — This MCP server is currently in beta and available to select partners. APIs, tools, and behavior may change without notice. Please share feedback with your Check point of contact.

An [MCP](https://modelcontextprotocol.io/) server that wraps the [Check Payroll API](https://docs.checkhq.com/), providing 263 tools for managing companies, employees, contractors, payrolls, tax configuration, embedded components, and more.

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
| `CHECK_TOOLSETS` | No | — | Comma-separated list of toolsets to enable (e.g. `companies,employees`) |
| `CHECK_TOOLS` | No | — | Comma-separated allowlist of individual tool names |
| `CHECK_EXCLUDE_TOOLS` | No | — | Comma-separated list of tool names to hide |
| `CHECK_READ_ONLY` | No | — | Set to `1`, `true`, or `yes` to disable all write/mutating tools |
| `CHECK_TRANSPORT` | No | `stdio` | Transport protocol: `stdio`, `sse`, or `streamable-http` |

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

**Filtering precedence:** `exclude_tools` > `read_only` > `tools` > `toolsets`. Exclude always wins; if `tools` is set it acts as an allowlist independent of toolsets.

#### Toolsets

There are 17 toolsets, one per API module: `bank_accounts`, `companies`, `compensation`, `components`, `contractor_payments`, `contractors`, `documents`, `employees`, `external_payrolls`, `forms`, `payments`, `payroll_items`, `payrolls`, `platform`, `tax`, `webhooks`, `workplaces`.

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

#### HTTP Headers (Remote Transport)

When running with `CHECK_TRANSPORT=sse` or `CHECK_TRANSPORT=streamable-http`, clients can pass configuration via HTTP headers:

```
X-MCP-Toolsets: companies,employees
X-MCP-Readonly: true
X-MCP-Exclude-Tools: create_company,delete_company
```

Header-based configuration takes precedence over environment variables when headers provide any filter settings.

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

263 tools organized across 17 categories. All list tools support `limit` and `cursor` parameters for cursor-based pagination — pass the `cursor` value from a previous response to fetch the next page.

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
| `get_payroll_journal_report` | GET | Get payroll journal report |
| `get_payroll_summary_report` | GET | Get payroll summary report |
| `get_tax_liabilities_report` | GET | Get tax liabilities report |
| `get_contractor_payments_report` | GET | Get contractor payments report |
| `get_child_support_payments_report` | GET | Get child support payments report |
| `get_w4_exemption_status_report` | GET | Get W-4 exemption status report |
| `get_applied_for_ids_detailed_report` | GET | Get applied-for IDs detailed report |
| `get_w2_preview_report` | GET | Get W-2 preview report |
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
| `get_payroll` | GET | Get details for a specific payroll |
| `create_payroll` | POST | Create a new payroll |
| `update_payroll` | PATCH | Update an existing payroll |
| `delete_payroll` | DELETE | Delete a payroll |
| `preview_payroll` | GET | Preview a payroll before approval |
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
| `list_external_payrolls` | GET | List external payrolls |
| `get_external_payroll` | GET | Get details for a specific external payroll |
| `create_external_payroll` | POST | Create a new external payroll |
| `update_external_payroll` | PATCH | Update an external payroll |
| `delete_external_payroll` | DELETE | Delete an external payroll |
| `approve_external_payroll` | POST | Approve an external payroll |
| `reopen_external_payroll` | POST | Reopen an external payroll |
| `preview_external_payroll` | GET | Preview an external payroll |

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
| `download_company_tax_document` | GET | Download a company tax document |
| **Company Authorization Documents** | | |
| `list_company_authorization_documents` | GET | List authorization documents |
| `get_company_authorization_document` | GET | Get an authorization document |
| `download_company_authorization_document` | GET | Download an authorization document |
| **Employee Tax Documents** | | |
| `list_employee_tax_documents` | GET | List employee tax documents |
| `get_employee_tax_document` | GET | Get an employee tax document |
| `download_employee_tax_document` | GET | Download an employee tax document |
| **Contractor Tax Documents** | | |
| `list_contractor_tax_documents` | GET | List contractor tax documents |
| `get_contractor_tax_document` | GET | Get a contractor tax document |
| `download_contractor_tax_document` | GET | Download a contractor tax document |
| **Setup Documents** | | |
| `list_setup_documents` | GET | List setup documents |
| `get_setup_document` | GET | Get a setup document |
| `download_setup_document` | GET | Download a setup document |
| **Company Provided Documents** | | |
| `list_company_provided_documents` | GET | List company-provided documents |
| `get_company_provided_document` | GET | Get a company-provided document |
| `create_company_provided_document` | POST | Create a company-provided document |
| `upload_company_provided_document_file` | POST | Upload a file for a document |

### Forms (4 tools)

| Tool | Method | Description |
|---|---|---|
| `list_forms` | GET | List forms across all companies |
| `get_form` | GET | Get a specific form |
| `render_form` | GET | Render a form for display |
| `validate_form` | POST | Validate form data before submission |

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

Tax parameters, elections, filings, exempt status, exemptible taxes, statements, and packages.

| Tool | Method | Description |
|---|---|---|
| **Company Tax Params** | | |
| `get_company_tax_params` | GET | Get tax parameters for a company |
| `update_company_tax_params` | PATCH | Update company tax parameters |
| `list_company_tax_param_settings` | GET | List tax parameter settings |
| `get_company_tax_param_setting` | GET | Get a specific tax param setting |
| `list_company_jurisdictions` | GET | List tax jurisdictions for a company |
| **Employee Tax Params** | | |
| `list_employee_tax_params` | GET | List employee tax parameters |
| `get_employee_tax_params` | GET | Get tax parameters for an employee |
| `update_employee_tax_params` | PATCH | Update employee tax parameters |
| `list_employee_tax_param_settings` | GET | List employee tax param settings |
| `get_employee_tax_param_setting` | GET | Get a specific setting |
| `list_employee_jurisdictions` | GET | List tax jurisdictions for an employee |
| `bulk_get_employee_tax_param_settings` | POST | Bulk get tax param settings |
| `bulk_update_employee_tax_param_settings` | POST | Bulk update tax param settings |
| **Company Tax Elections** | | |
| `list_company_tax_elections` | GET | List tax elections for a company |
| `create_company_tax_elections` | POST | Create company tax elections |
| `update_company_tax_elections` | PATCH | Update company tax elections |
| **Employee Tax Elections** | | |
| `list_employee_tax_elections` | GET | List tax elections for an employee |
| `update_employee_tax_elections` | PATCH | Update employee tax elections |
| **Tax Filings** | | |
| `list_tax_filings` | GET | List tax filings |
| `get_tax_filing` | GET | Get a specific tax filing |
| `request_tax_filing_refile` | POST | Request a refile |
| **Tax Filing Events** | | |
| `get_tax_filing_event` | GET | Get a specific tax filing event |
| **Exempt Status** | | |
| `get_exempt_status` | GET | Get exempt status for an employee |
| `update_exempt_status` | PATCH | Update exempt status |
| **Exemptible Taxes** | | |
| `list_exemptible_taxes` | GET | List exemptible taxes |
| `update_exemptible_tax` | PATCH | Update an exemptible tax |
| `bulk_update_exemptible_taxes` | PATCH | Bulk update exemptible taxes |
| **Employee Tax Statements** | | |
| `list_employee_tax_statements` | GET | List employee tax statements |
| `get_employee_tax_statement` | GET | Get a specific tax statement |
| **Tax Packages** | | |
| `request_tax_package` | POST | Request a tax package |
| `get_tax_package` | GET | Get a specific tax package |

### Webhooks (7 tools)

| Tool | Method | Description |
|---|---|---|
| `list_webhook_configs` | GET | List webhook configurations |
| `get_webhook_config` | GET | Get a specific webhook configuration |
| `create_webhook_config` | POST | Create a webhook configuration |
| `update_webhook_config` | PATCH | Update a webhook configuration |
| `delete_webhook_config` | DELETE | Delete a webhook configuration |
| `ping_webhook_config` | POST | Send a test ping |
| `retry_webhook_events` | POST | Retry failed webhook events |

### Platform (29 tools)

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
| `list_accounting_accounts` | GET | List accounting accounts for a company |
| `refresh_accounting_accounts` | POST | Refresh accounting accounts |
| `get_accounting_mappings` | GET | Get accounting mappings |
| `update_accounting_mappings` | PATCH | Update accounting mappings |
| `toggle_accounting_mappings` | POST | Toggle accounting mappings |
| `sync_accounting` | POST | Trigger an accounting sync |
| `list_accounting_sync_attempts` | GET | List accounting sync attempts |
| **Company Groups** | | |
| `list_company_groups` | GET | List company groups |
| `create_company_group` | POST | Create a company group |
| `update_company_group` | PATCH | Update a company group |
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
