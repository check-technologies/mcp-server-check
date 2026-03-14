/** Payroll tools for the Check API. */

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
    "list_payrolls",
    "List payrolls, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to payrolls belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return (default 10, max 100)."),
      ids: z.array(z.string()).optional().describe("Filter to specific payroll IDs."),
      cursor: z.string().optional().describe("Pagination cursor from a previous response."),
    },
    async ({ company, limit, ids, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (ids !== undefined) params.ids = ids.join(",");
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/payrolls", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_payroll",
    "Get details for a specific payroll.",
    {
      payroll_id: z.string().describe('The Check payroll ID (e.g. "prl_xxxxx").'),
    },
    async ({ payroll_id }) => {
      const result = await checkApiGet(api, `/payrolls/${payroll_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_payroll",
    "Create a new payroll.",
    {
      company: z.string().describe("The Check company ID."),
      period_start: z.string().describe("Pay period start date (YYYY-MM-DD)."),
      period_end: z.string().describe("Pay period end date (YYYY-MM-DD)."),
      payday: z.string().describe("Payday date (YYYY-MM-DD)."),
      type: z.string().optional().describe('Payroll type — "regular", "off_cycle", or "amendment". Default: "regular".'),
      processing_period: z.string().optional().describe('Processing period — "three_day", "two_day", or "one_day".'),
      pay_frequency: z.string().optional().describe('Pay frequency — "weekly", "biweekly", "semimonthly", "monthly", "quarterly", or "annually". Default: "biweekly".'),
      funding_payment_method: z.string().optional().describe('Funding method — "ach" or "wire". Default: "ach".'),
      pay_schedule: z.string().optional().describe("ID of the pay schedule this payroll relates to."),
      off_cycle_options: z.record(z.unknown()).optional().describe("Off-cycle config object with keys: force_supplemental_withholding (bool), apply_benefits (bool), apply_post_tax_deductions (bool)."),
      items: z.array(z.record(z.unknown())).optional().describe('List of payroll item objects. Each requires "employee" and may include "payment_method", "earnings" (list), "reimbursements" (list), "benefit_overrides" (list), "post_tax_deduction_overrides" (list), "pto_balance_hours", "sick_balance_hours", "metadata".'),
      contractor_payments: z.array(z.record(z.unknown())).optional().describe('List of contractor payment objects. Each requires "contractor" and may include "payment_method", "amount", "reimbursement_amount", "workplace", "paper_check_number".'),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
      bank_account: z.string().optional().describe("ID of the bank account to fund the payroll."),
    },
    async ({ company, period_start, period_end, payday, type, processing_period, pay_frequency, funding_payment_method, pay_schedule, off_cycle_options, items, contractor_payments, metadata, bank_account }) => {
      const body: Record<string, unknown> = { company, period_start, period_end, payday };
      if (type !== undefined) body.type = type;
      if (processing_period !== undefined) body.processing_period = processing_period;
      if (pay_frequency !== undefined) body.pay_frequency = pay_frequency;
      if (funding_payment_method !== undefined) body.funding_payment_method = funding_payment_method;
      if (pay_schedule !== undefined) body.pay_schedule = pay_schedule;
      if (off_cycle_options !== undefined) body.off_cycle_options = off_cycle_options;
      if (items !== undefined) body.items = items;
      if (contractor_payments !== undefined) body.contractor_payments = contractor_payments;
      if (metadata !== undefined) body.metadata = metadata;
      if (bank_account !== undefined) body.bank_account = bank_account;
      const result = await checkApiPost(api, "/payrolls", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_payroll",
    "Update an existing payroll.",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
      period_start: z.string().optional().describe("Pay period start date (YYYY-MM-DD)."),
      period_end: z.string().optional().describe("Pay period end date (YYYY-MM-DD)."),
      payday: z.string().optional().describe("Payday date (YYYY-MM-DD)."),
      type: z.string().optional().describe('Payroll type — "regular", "off_cycle", or "amendment".'),
      processing_period: z.string().optional().describe('Processing period — "three_day", "two_day", or "one_day".'),
      pay_frequency: z.string().optional().describe('Pay frequency — "weekly", "biweekly", "semimonthly", "monthly", "quarterly", or "annually".'),
      funding_payment_method: z.string().optional().describe('Funding method — "ach" or "wire".'),
      pay_schedule: z.string().optional().describe("ID of the pay schedule this payroll relates to."),
      off_cycle_options: z.record(z.unknown()).optional().describe("Off-cycle config object with keys: force_supplemental_withholding (bool), apply_benefits (bool), apply_post_tax_deductions (bool)."),
      items: z.array(z.record(z.unknown())).optional().describe("List of payroll item objects (see create_payroll for shape)."),
      contractor_payments: z.array(z.record(z.unknown())).optional().describe("List of contractor payment objects (see create_payroll for shape)."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
      bank_account: z.string().optional().describe("ID of the bank account to fund the payroll."),
    },
    async ({ payroll_id, period_start, period_end, payday, type, processing_period, pay_frequency, funding_payment_method, pay_schedule, off_cycle_options, items, contractor_payments, metadata, bank_account }) => {
      const body: Record<string, unknown> = {};
      if (period_start !== undefined) body.period_start = period_start;
      if (period_end !== undefined) body.period_end = period_end;
      if (payday !== undefined) body.payday = payday;
      if (type !== undefined) body.type = type;
      if (processing_period !== undefined) body.processing_period = processing_period;
      if (pay_frequency !== undefined) body.pay_frequency = pay_frequency;
      if (funding_payment_method !== undefined) body.funding_payment_method = funding_payment_method;
      if (pay_schedule !== undefined) body.pay_schedule = pay_schedule;
      if (off_cycle_options !== undefined) body.off_cycle_options = off_cycle_options;
      if (items !== undefined) body.items = items;
      if (contractor_payments !== undefined) body.contractor_payments = contractor_payments;
      if (metadata !== undefined) body.metadata = metadata;
      if (bank_account !== undefined) body.bank_account = bank_account;
      const result = await checkApiPatch(api, `/payrolls/${payroll_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "delete_payroll",
    "Delete a payroll.",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiDelete(api, `/payrolls/${payroll_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "preview_payroll",
    "Preview a payroll before approval.",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiGet(api, `/payrolls/${payroll_id}/preview`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "approve_payroll",
    "Approve a payroll for processing.",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiPost(api, `/payrolls/${payroll_id}/approve`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "reopen_payroll",
    "Reopen a previously approved payroll.",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiPost(api, `/payrolls/${payroll_id}/reopen`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_payroll_paper_checks",
    "Get paper checks for a payroll.",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiGet(api, `/payrolls/${payroll_id}/paper_checks`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_payroll_cash_requirement_report",
    "Get a cash requirement report for a payroll.",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiGet(api, `/payrolls/${payroll_id}/reports/cash_requirement`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_payroll_paper_checks_report",
    "Get a paper checks report for a payroll.",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiGet(api, `/payrolls/${payroll_id}/reports/paper_checks`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Simulation ---

  tool(
    server,
    filter,
    toolsetName,
    "simulate_start_processing",
    "Simulate starting payroll processing (sandbox only).",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiPost(api, `/payrolls/${payroll_id}/simulate/start_processing`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "simulate_complete_funding",
    "Simulate completing payroll funding (sandbox only).",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiPost(api, `/payrolls/${payroll_id}/simulate/complete_funding`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "simulate_fail_funding",
    "Simulate failing payroll funding (sandbox only).",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiPost(api, `/payrolls/${payroll_id}/simulate/fail_funding`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "simulate_complete_disbursements",
    "Simulate completing payroll disbursements (sandbox only).",
    {
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ payroll_id }) => {
      const result = await checkApiPost(api, `/payrolls/${payroll_id}/simulate/complete_disbursements`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
