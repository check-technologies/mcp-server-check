/** Contractor payment tools for the Check API. */

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
    "list_contractor_payments",
    "List contractor payments, optionally filtered by company or contractor.",
    {
      company: z.string().optional().describe('Filter to contractor payments belonging to this Check company ID (e.g. "com_xxxxx").'),
      contractor: z.string().optional().describe('Filter to payments for this Check contractor ID (e.g. "ctr_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return (default 10, max 100)."),
      ids: z.array(z.string()).optional().describe("Filter to specific contractor payment IDs."),
      cursor: z.string().optional().describe("Pagination cursor from a previous response."),
    },
    async ({ company, contractor, limit, ids, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (contractor !== undefined) params.contractor = contractor;
      if (limit !== undefined) params.limit = limit;
      if (ids !== undefined) params.ids = ids.join(",");
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/contractor_payments", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_contractor_payment",
    "Get details for a specific contractor payment.",
    {
      contractor_payment_id: z.string().describe("The Check contractor payment ID."),
    },
    async ({ contractor_payment_id }) => {
      const result = await checkApiGet(api, `/contractor_payments/${contractor_payment_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_contractor_payment",
    "Create a new contractor payment.",
    {
      contractor: z.string().describe("The Check contractor ID."),
      payroll: z.string().describe("The Check payroll ID."),
      payment_method: z.string().optional().describe('How the contractor will be paid -- "direct_deposit" or "manual". Default: "direct_deposit".'),
      amount: z.string().optional().describe('The amount to pay the contractor (e.g. "1500.00"). Default: "0.00".'),
      reimbursement_amount: z.string().optional().describe('Reimbursement amount (e.g. "50.00"). Default: "0.00".'),
      workplace: z.string().optional().describe("Workplace ID associated with this payment."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
      paper_check_number: z.string().optional().describe("Check number for accounting on printed checks."),
    },
    async ({ contractor, payroll, payment_method, amount, reimbursement_amount, workplace, metadata, paper_check_number }) => {
      const body: Record<string, unknown> = { contractor, payroll };
      if (payment_method !== undefined) body.payment_method = payment_method;
      if (amount !== undefined) body.amount = amount;
      if (reimbursement_amount !== undefined) body.reimbursement_amount = reimbursement_amount;
      if (workplace !== undefined) body.workplace = workplace;
      if (metadata !== undefined) body.metadata = metadata;
      if (paper_check_number !== undefined) body.paper_check_number = paper_check_number;
      const result = await checkApiPost(api, "/contractor_payments", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_contractor_payment",
    "Update an existing contractor payment.",
    {
      contractor_payment_id: z.string().describe("The Check contractor payment ID."),
      contractor: z.string().optional().describe("The Check contractor ID."),
      payment_method: z.string().optional().describe('How the contractor will be paid -- "direct_deposit" or "manual".'),
      amount: z.string().optional().describe('The amount to pay the contractor (e.g. "1500.00").'),
      reimbursement_amount: z.string().optional().describe('Reimbursement amount (e.g. "50.00").'),
      workplace: z.string().optional().describe("Workplace ID associated with this payment."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
      paper_check_number: z.string().optional().describe("Check number for accounting on printed checks."),
    },
    async ({ contractor_payment_id, contractor, payment_method, amount, reimbursement_amount, workplace, metadata, paper_check_number }) => {
      const body: Record<string, unknown> = {};
      if (contractor !== undefined) body.contractor = contractor;
      if (payment_method !== undefined) body.payment_method = payment_method;
      if (amount !== undefined) body.amount = amount;
      if (reimbursement_amount !== undefined) body.reimbursement_amount = reimbursement_amount;
      if (workplace !== undefined) body.workplace = workplace;
      if (metadata !== undefined) body.metadata = metadata;
      if (paper_check_number !== undefined) body.paper_check_number = paper_check_number;
      const result = await checkApiPatch(api, `/contractor_payments/${contractor_payment_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "delete_contractor_payment",
    "Delete a contractor payment.",
    {
      contractor_payment_id: z.string().describe("The Check contractor payment ID."),
    },
    async ({ contractor_payment_id }) => {
      const result = await checkApiDelete(api, `/contractor_payments/${contractor_payment_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_contractor_payment_paper_check",
    "Get paper check details for a contractor payment.",
    {
      contractor_payment_id: z.string().describe("The Check contractor payment ID."),
    },
    async ({ contractor_payment_id }) => {
      const result = await checkApiGet(api, `/contractor_payments/${contractor_payment_id}/paper_check`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
