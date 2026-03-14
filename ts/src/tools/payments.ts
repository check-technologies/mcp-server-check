/** Payment tools for the Check API. */

import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import {
  checkApiGet,
  checkApiPost,
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
    "list_payments",
    "List payments, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to payments belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/payments", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_payment",
    "Get details for a specific payment.",
    {
      payment_id: z.string().describe("The Check payment ID."),
    },
    async ({ payment_id }) => {
      const result = await checkApiGet(api, `/payments/${payment_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_payment_attempts",
    "List payment attempts for a payment.",
    {
      payment_id: z.string().describe("The Check payment ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ payment_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/payments/${payment_id}/payment_attempts`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "retry_payment",
    "Retry a failed payment.",
    {
      payment_id: z.string().describe("The Check payment ID."),
    },
    async ({ payment_id }) => {
      const result = await checkApiPost(api, `/payments/${payment_id}/retry`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "refund_payment",
    "Refund a payment.",
    {
      payment_id: z.string().describe("The Check payment ID."),
    },
    async ({ payment_id }) => {
      const result = await checkApiPost(api, `/payments/${payment_id}/refund`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "cancel_payment",
    "Cancel a payment.",
    {
      payment_id: z.string().describe("The Check payment ID."),
    },
    async ({ payment_id }) => {
      const result = await checkApiPost(api, `/payments/${payment_id}/cancel`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
