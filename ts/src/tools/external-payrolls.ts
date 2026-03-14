/** External payroll tools for the Check API. */

import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import {
  checkApiGet,
  checkApiPost,
  checkApiPatch,
  checkApiDelete,
  checkApiList,
  type CheckApiOptions,
} from "../helpers.js";
import type { ToolFilter } from "../tool-filter.js";
import { tool } from "./_register.js";



export function register(
  server: McpServer,
  api: CheckApiOptions,
  filter: ToolFilter,
  toolsetName: string,
) {
  tool(
    server,
    filter,
    toolsetName,
    "list_external_payrolls",
    "List external payrolls, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to external payrolls belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return (default 10, max 100)."),
      ids: z.array(z.string()).optional().describe("Filter to specific external payroll IDs."),
      cursor: z.string().optional().describe("Pagination cursor from a previous response."),
    },
    async ({ company, limit, ids, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (ids !== undefined) params.ids = ids.join(",");
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/external_payrolls", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_external_payroll",
    "Get details for a specific external payroll.",
    {
      payroll_id: z.string().describe("The Check external payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiGet(api, `/external_payrolls/${payroll_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_external_payroll",
    "Create a new external payroll.",
    {
      company: z.string().describe("The Check company ID."),
      period_start: z.string().describe("Pay period start date (YYYY-MM-DD)."),
      period_end: z.string().describe("Pay period end date (YYYY-MM-DD)."),
      payday: z.string().describe("Payday date (YYYY-MM-DD)."),
      pay_frequency: z.string().optional().describe("Frequency at which the external payroll was paid."),
      items: z.array(z.record(z.unknown())).optional().describe('List of external payroll item objects. Each may include "employee", "earnings" (list), "reimbursements" (list), "taxes" (list), "benefits" (list), "post_tax_deductions" (list).'),
      contractor_payments: z.array(z.record(z.unknown())).optional().describe('List of contractor payment objects. Each may include "contractor", "amount", "reimbursement_amount".'),
    },
    async ({ company, period_start, period_end, payday, pay_frequency, items, contractor_payments }) => {
      const body: Record<string, unknown> = { company, period_start, period_end, payday };
      if (pay_frequency !== undefined) body.pay_frequency = pay_frequency;
      if (items !== undefined) body.items = items;
      if (contractor_payments !== undefined) body.contractor_payments = contractor_payments;
      const result = await checkApiPost(api, "/external_payrolls", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_external_payroll",
    "Update an existing external payroll.",
    {
      payroll_id: z.string().describe("The Check external payroll ID."),
      period_start: z.string().optional().describe("Pay period start date (YYYY-MM-DD)."),
      period_end: z.string().optional().describe("Pay period end date (YYYY-MM-DD)."),
      payday: z.string().optional().describe("Payday date (YYYY-MM-DD)."),
      pay_frequency: z.string().optional().describe("Frequency at which the external payroll was paid."),
      items: z.array(z.record(z.unknown())).optional().describe("List of external payroll item objects (see create_external_payroll)."),
      contractor_payments: z.array(z.record(z.unknown())).optional().describe("List of contractor payment objects (see create_external_payroll)."),
    },
    async ({ payroll_id, period_start, period_end, payday, pay_frequency, items, contractor_payments }) => {
      const body: Record<string, unknown> = {};
      if (period_start !== undefined) body.period_start = period_start;
      if (period_end !== undefined) body.period_end = period_end;
      if (payday !== undefined) body.payday = payday;
      if (pay_frequency !== undefined) body.pay_frequency = pay_frequency;
      if (items !== undefined) body.items = items;
      if (contractor_payments !== undefined) body.contractor_payments = contractor_payments;
      const result = await checkApiPatch(api, `/external_payrolls/${payroll_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "delete_external_payroll",
    "Delete an external payroll.",
    {
      payroll_id: z.string().describe("The Check external payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiDelete(api, `/external_payrolls/${payroll_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "approve_external_payroll",
    "Approve an external payroll.",
    {
      payroll_id: z.string().describe("The Check external payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiPost(api, `/external_payrolls/${payroll_id}/approve`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "reopen_external_payroll",
    "Reopen an external payroll.",
    {
      payroll_id: z.string().describe("The Check external payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiPost(api, `/external_payrolls/${payroll_id}/reopen`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "preview_external_payroll",
    "Preview an external payroll.",
    {
      external_payroll_id: z.string().describe("The Check external payroll ID."),
    },
    async ({ external_payroll_id }) => {
      const result = await checkApiGet(api, `/external_payrolls/${external_payroll_id}/preview`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
