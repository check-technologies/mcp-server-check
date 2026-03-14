/** Form tools for the Check API. */

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
    "list_forms",
    "List forms, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to forms belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/forms", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_form",
    "Get details for a specific form.",
    {
      form_id: z.string().describe("The Check form ID."),
    },
    async ({ form_id }) => {
      const result = await checkApiGet(api, `/forms/${form_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "render_form",
    "Render a form for display.",
    {
      form_id: z.string().describe("The Check form ID."),
    },
    async ({ form_id }) => {
      const result = await checkApiGet(api, `/forms/${form_id}/render`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "validate_form",
    "Validate form data before submission.",
    {
      form_id: z.string().describe("The Check form ID."),
      parameters: z.array(z.object({
        name: z.string().describe("Form field name."),
        value: z.string().describe("Form field value."),
      })).describe('List of name/value dicts representing form fields. Example: [{"name": "field_name", "value": "field_value"}].'),
    },
    async ({ form_id, parameters }) => {
      const body: Record<string, unknown> = { parameters };
      const result = await checkApiPost(api, `/forms/${form_id}/validate`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
