/** Bank account tools for the Check API. */

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
    "list_bank_accounts",
    "List bank accounts, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to bank accounts belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/bank_accounts", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_bank_account",
    "Get details for a specific bank account.",
    {
      bank_account_id: z.string().describe("The Check bank account ID."),
    },
    async ({ bank_account_id }) => {
      const result = await checkApiGet(api, `/bank_accounts/${bank_account_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_bank_account",
    "Create a new bank account. Provide either raw_bank_account or plaid_bank_account, plus exactly one of employee, company, or contractor to indicate who owns the account.",
    {
      raw_bank_account: z.record(z.unknown()).optional().describe('Bank account details dict with keys: account_number (required), routing_number (required), subtype (required -- "checking" or "savings"), institution_name (optional).'),
      plaid_bank_account: z.record(z.unknown()).optional().describe("Plaid token dict with key: plaid_processor_token (required)."),
      employee: z.string().optional().describe("ID of the employee who owns this account."),
      company: z.string().optional().describe("ID of the company who owns this account."),
      contractor: z.string().optional().describe("ID of the contractor who owns this account."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ raw_bank_account, plaid_bank_account, employee, company, contractor, metadata }) => {
      const body: Record<string, unknown> = {};
      if (raw_bank_account !== undefined) body.raw_bank_account = raw_bank_account;
      if (plaid_bank_account !== undefined) body.plaid_bank_account = plaid_bank_account;
      if (employee !== undefined) body.employee = employee;
      if (company !== undefined) body.company = company;
      if (contractor !== undefined) body.contractor = contractor;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPost(api, "/bank_accounts", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_bank_account",
    "Update a bank account.",
    {
      bank_account_id: z.string().describe("The Check bank account ID."),
      raw_bank_account: z.record(z.unknown()).optional().describe('Bank account details dict with keys: account_number, routing_number, subtype ("checking" or "savings"), institution_name.'),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ bank_account_id, raw_bank_account, metadata }) => {
      const body: Record<string, unknown> = {};
      if (raw_bank_account !== undefined) body.raw_bank_account = raw_bank_account;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPatch(api, `/bank_accounts/${bank_account_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "delete_bank_account",
    "Delete a bank account.",
    {
      bank_account_id: z.string().describe("The Check bank account ID."),
    },
    async ({ bank_account_id }) => {
      const result = await checkApiDelete(api, `/bank_accounts/${bank_account_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "reveal_bank_account_number",
    "Reveal the full account number for a bank account.",
    {
      bank_account_id: z.string().describe("The Check bank account ID."),
    },
    async ({ bank_account_id }) => {
      const result = await checkApiGet(api, `/bank_accounts/${bank_account_id}/reveal`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
