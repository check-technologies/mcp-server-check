/** Payroll item tools for the Check API. */

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
    "list_payroll_items",
    "List payroll items, optionally filtered by company, employee, or payroll.",
    {
      company: z.string().optional().describe('Filter to payroll items belonging to this Check company ID (e.g. "com_xxxxx").'),
      employee: z.string().optional().describe('Filter to payroll items for this Check employee ID (e.g. "emp_xxxxx").'),
      payroll: z.string().optional().describe('Filter to payroll items for this Check payroll ID (e.g. "prl_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return (default 10, max 100)."),
      ids: z.array(z.string()).optional().describe("Filter to specific payroll item IDs."),
      cursor: z.string().optional().describe("Pagination cursor from a previous response."),
    },
    async ({ company, employee, payroll, limit, ids, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (employee !== undefined) params.employee = employee;
      if (payroll !== undefined) params.payroll = payroll;
      if (limit !== undefined) params.limit = limit;
      if (ids !== undefined) params.ids = ids.join(",");
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/payroll_items", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_payroll_item",
    "Get details for a specific payroll item.",
    {
      payroll_item_id: z.string().describe("The Check payroll item ID."),
    },
    async ({ payroll_item_id }) => {
      const result = await checkApiGet(api, `/payroll_items/${payroll_item_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_payroll_item",
    "Create a new payroll item.",
    {
      payroll: z.string().describe("The Check payroll ID."),
      employee: z.string().describe("The Check employee ID."),
      payment_method: z.string().optional().describe('Payment method — "direct_deposit" or "manual".'),
      earnings: z.array(z.record(z.unknown())).optional().describe('List of earning objects. Each requires "workplace" and may include "type", "earning_code", "description", "earning_rate", "amount", "hours", "piece_units", "metadata".'),
      reimbursements: z.array(z.record(z.unknown())).optional().describe('List of reimbursement objects. Each requires "amount" and may include "description", "code", "metadata".'),
    },
    async ({ payroll, employee, payment_method, earnings, reimbursements }) => {
      const body: Record<string, unknown> = { payroll, employee };
      if (payment_method !== undefined) body.payment_method = payment_method;
      if (earnings !== undefined) body.earnings = earnings;
      if (reimbursements !== undefined) body.reimbursements = reimbursements;
      const result = await checkApiPost(api, "/payroll_items", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_payroll_item",
    "Update an existing payroll item.",
    {
      payroll_item_id: z.string().describe("The Check payroll item ID."),
      payment_method: z.string().optional().describe('Payment method — "direct_deposit" or "manual".'),
      earnings: z.array(z.record(z.unknown())).optional().describe("List of earning objects (see create_payroll_item for shape)."),
      reimbursements: z.array(z.record(z.unknown())).optional().describe("List of reimbursement objects (see create_payroll_item for shape)."),
      benefit_overrides: z.array(z.record(z.unknown())).optional().describe('List of benefit override objects. Each requires "benefit" and may include "employee_contribution_amount", "company_contribution_amount".'),
      post_tax_deduction_overrides: z.array(z.record(z.unknown())).optional().describe('List of post-tax deduction override objects. Each requires "post_tax_deduction" and "amount".'),
      pto_balance_hours: z.number().optional().describe("Employee's remaining PTO hour balance for paystub display."),
      sick_balance_hours: z.number().optional().describe("Employee's remaining sick hour balance for paystub display."),
      supplemental_tax_calc_method: z.string().optional().describe('Tax calculation method — "flat" or "aggregate".'),
      paper_check_number: z.string().optional().describe("Check number for printed checks."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ payroll_item_id, payment_method, earnings, reimbursements, benefit_overrides, post_tax_deduction_overrides, pto_balance_hours, sick_balance_hours, supplemental_tax_calc_method, paper_check_number, metadata }) => {
      const body: Record<string, unknown> = {};
      if (payment_method !== undefined) body.payment_method = payment_method;
      if (earnings !== undefined) body.earnings = earnings;
      if (reimbursements !== undefined) body.reimbursements = reimbursements;
      if (benefit_overrides !== undefined) body.benefit_overrides = benefit_overrides;
      if (post_tax_deduction_overrides !== undefined) body.post_tax_deduction_overrides = post_tax_deduction_overrides;
      if (pto_balance_hours !== undefined) body.pto_balance_hours = pto_balance_hours;
      if (sick_balance_hours !== undefined) body.sick_balance_hours = sick_balance_hours;
      if (supplemental_tax_calc_method !== undefined) body.supplemental_tax_calc_method = supplemental_tax_calc_method;
      if (paper_check_number !== undefined) body.paper_check_number = paper_check_number;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPatch(api, `/payroll_items/${payroll_item_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "bulk_update_payroll_items",
    "Bulk update payroll items. The payload is a complex bulk structure — pass the full request body as a dict.",
    {
      data: z.record(z.unknown()).describe("Bulk update payload with items array."),
    },
    async ({ data }) => {
      const result = await checkApiPatch(api, "/payroll_items", data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "delete_payroll_item",
    "Delete a payroll item.",
    {
      payroll_item_id: z.string().describe("The Check payroll item ID."),
    },
    async ({ payroll_item_id }) => {
      const result = await checkApiDelete(api, `/payroll_items/${payroll_item_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "bulk_delete_payroll_items",
    "Bulk delete payroll items.",
    {
      ids: z.array(z.string()).describe("List of payroll item IDs to delete."),
    },
    async ({ ids }) => {
      const params: Record<string, unknown> = { ids: ids.join(",") };
      const result = await checkApiDelete(api, "/payroll_items", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_payroll_item_paper_check",
    "Get paper check details for a payroll item.",
    {
      payroll_item_id: z.string().describe("The Check payroll item ID."),
    },
    async ({ payroll_item_id }) => {
      const result = await checkApiGet(api, `/payroll_items/${payroll_item_id}/paper_check`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
