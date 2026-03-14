/** Component tools for the Check API. */

import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import {
  checkApiPost,
  type CheckApiOptions,
} from "../helpers.js";
import type { ToolFilter } from "../tool-filter.js";
import { tool } from "./_register.js";



interface ComponentDef {
  entityType: string;
  entityLabel: string;
  componentName: string;
}

const COMPANY_COMPONENTS = [
  "previous_provider_access",
  "accounting_integration",
  "authorization_documents",
  "business_details",
  "checklist",
  "company_reports",
  "connect_bank_account",
  "details",
  "early_enrollment",
  "employee_setup",
  "filing_authorization",
  "filing_preview",
  "full_service_setup_submission",
  "integrations",
  "integrations_authorize",
  "pay_history",
  "payment_setup",
  "progress_tracker",
  "run_payroll",
  "signatory_agreements",
  "tax_documents",
  "tax_setup",
  "team_setup",
  "terms_of_service",
  "verification_documents",
];

const EMPLOYEE_COMPONENTS = [
  "benefits",
  "payment_setup",
  "paystubs",
  "post_tax_deductions",
  "profile",
  "ssn_setup",
  "tax_documents",
  "tax_setup",
  "withholdings_setup",
];

const CONTRACTOR_COMPONENTS = [
  "tax_documents",
];

function buildComponentDefs(): ComponentDef[] {
  const defs: ComponentDef[] = [];
  for (const name of COMPANY_COMPONENTS) {
    defs.push({ entityType: "companies", entityLabel: "company", componentName: name });
  }
  for (const name of EMPLOYEE_COMPONENTS) {
    defs.push({ entityType: "employees", entityLabel: "employee", componentName: name });
  }
  for (const name of CONTRACTOR_COMPONENTS) {
    defs.push({ entityType: "contractors", entityLabel: "contractor", componentName: name });
  }
  return defs;
}

export function register(
  server: McpServer,
  api: CheckApiOptions,
  filter: ToolFilter,
  toolsetName: string,
) {
  const componentDefs = buildComponentDefs();

  for (const def of componentDefs) {
    const toolName = `create_${def.entityLabel}_${def.componentName}_component`;

    tool(
      server,
      filter,
      toolsetName,
      toolName,
      `Create a ${def.componentName} component for a ${def.entityLabel}.`,
      {
        entity_id: z.string().describe(`The Check ${def.entityLabel} ID.`),
        data: z.record(z.unknown()).optional().describe("Optional component configuration data."),
      },
      async ({ entity_id, data }) => {
        const result = await checkApiPost(
          api,
          `/${def.entityType}/${entity_id}/components/${def.componentName}`,
          data,
        );
        return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
      },
    );
  }
}
