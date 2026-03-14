/** Tool registration orchestrator — imports all 17 modules. */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { CheckApiOptions } from "../helpers.js";
import type { ToolFilter } from "../tool-filter.js";

import { register as bankAccounts } from "./bank-accounts.js";
import { register as companies } from "./companies.js";
import { register as compensation } from "./compensation.js";
import { register as components } from "./components.js";
import { register as contractorPayments } from "./contractor-payments.js";
import { register as contractors } from "./contractors.js";
import { register as documents } from "./documents.js";
import { register as employees } from "./employees.js";
import { register as externalPayrolls } from "./external-payrolls.js";
import { register as forms } from "./forms.js";
import { register as payments } from "./payments.js";
import { register as payrollItems } from "./payroll-items.js";
import { register as payrolls } from "./payrolls.js";
import { register as platform } from "./platform.js";
import { register as tax } from "./tax.js";
import { register as webhooks } from "./webhooks.js";
import { register as workplaces } from "./workplaces.js";

const TOOLSETS: Record<string, typeof webhooks> = {
  bank_accounts: bankAccounts,
  companies,
  compensation,
  components,
  contractor_payments: contractorPayments,
  contractors,
  documents,
  employees,
  external_payrolls: externalPayrolls,
  forms,
  payments,
  payroll_items: payrollItems,
  payrolls,
  platform,
  tax,
  webhooks,
  workplaces,
};

export function registerAll(
  server: McpServer,
  api: CheckApiOptions,
  filter: ToolFilter,
): void {
  for (const [toolsetName, mod] of Object.entries(TOOLSETS)) {
    mod(server, api, filter, toolsetName);
  }
}
