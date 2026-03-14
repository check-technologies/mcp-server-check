/** Webhook tools for the Check API. */

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
    "list_webhook_configs",
    "List webhook configurations, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to webhook configs belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/webhook_configs", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_webhook_config",
    "Get details for a specific webhook configuration.",
    {
      webhook_config_id: z.string().describe("The Check webhook config ID."),
    },
    async ({ webhook_config_id }) => {
      const result = await checkApiGet(api, `/webhook_configs/${webhook_config_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_webhook_config",
    "Create a new webhook configuration.",
    {
      url: z.string().describe("The webhook endpoint URL."),
    },
    async ({ url }) => {
      const body: Record<string, unknown> = { url };
      const result = await checkApiPost(api, "/webhook_configs", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_webhook_config",
    "Update a webhook configuration.",
    {
      webhook_config_id: z.string().describe("The Check webhook config ID."),
      url: z.string().optional().describe("The webhook endpoint URL."),
      active: z.boolean().optional().describe("Whether the webhook config is active."),
    },
    async ({ webhook_config_id, url, active }) => {
      const body: Record<string, unknown> = {};
      if (url !== undefined) body.url = url;
      if (active !== undefined) body.active = active;
      const result = await checkApiPatch(api, `/webhook_configs/${webhook_config_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "delete_webhook_config",
    "Delete a webhook configuration.",
    {
      webhook_config_id: z.string().describe("The Check webhook config ID."),
    },
    async ({ webhook_config_id }) => {
      const result = await checkApiDelete(api, `/webhook_configs/${webhook_config_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "ping_webhook_config",
    "Send a test ping to a webhook configuration.",
    {
      webhook_config_id: z.string().describe("The Check webhook config ID."),
    },
    async ({ webhook_config_id }) => {
      const result = await checkApiPost(api, `/webhook_configs/${webhook_config_id}/ping`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "retry_webhook_events",
    "Retry failed webhook events. The payload structure varies -- pass the full request body as a dict with event IDs or filters.",
    {
      data: z.record(z.unknown()).describe("Retry configuration (event IDs or filters)."),
    },
    async ({ data }) => {
      const result = await checkApiPost(api, "/webhook_events/retry", data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
