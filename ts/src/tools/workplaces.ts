/** Workplace tools for the Check API. */

import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import {
  checkApiGet,
  checkApiPost,
  checkApiPatch,
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
    "list_workplaces",
    "List workplaces, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to workplaces belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return (default 10, max 100)."),
      cursor: z.string().optional().describe("Pagination cursor from a previous response."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/workplaces", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_workplace",
    "Get details for a specific workplace.",
    {
      workplace_id: z.string().describe('The Check workplace ID (e.g. "wrk_xxxxx").'),
    },
    async ({ workplace_id }) => {
      const result = await checkApiGet(api, `/workplaces/${workplace_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_workplace",
    "Create a new workplace.",
    {
      company: z.string().describe("The Check company ID."),
      address: z.record(z.unknown()).describe("Workplace address dict with keys: line1 (required), line2, city (required), state (required), postal_code (required), country."),
      name: z.string().optional().describe("Human-readable name for the workplace."),
      active: z.boolean().optional().describe("Whether the workplace can be associated with employees. Default: true."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ company, address, name, active, metadata }) => {
      const body: Record<string, unknown> = { company, address };
      if (name !== undefined) body.name = name;
      if (active !== undefined) body.active = active;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPost(api, "/workplaces", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_workplace",
    "Update an existing workplace.",
    {
      workplace_id: z.string().describe("The Check workplace ID."),
      company: z.string().optional().describe("The Check company ID."),
      name: z.string().optional().describe("Human-readable name for the workplace."),
      address: z.record(z.unknown()).optional().describe("Address dict with keys: line1, line2, city, state, postal_code, country."),
      active: z.boolean().optional().describe("Whether the workplace can be associated with employees."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ workplace_id, company, name, address, active, metadata }) => {
      const body: Record<string, unknown> = {};
      if (company !== undefined) body.company = company;
      if (name !== undefined) body.name = name;
      if (address !== undefined) body.address = address;
      if (active !== undefined) body.active = active;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPatch(api, `/workplaces/${workplace_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
