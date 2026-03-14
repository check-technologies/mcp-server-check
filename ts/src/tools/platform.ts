/** Platform tools for the Check API. */

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
  // ---------------------------------------------------------------------------
  // Read tools
  // ---------------------------------------------------------------------------

  tool(
    server,
    filter,
    toolsetName,
    "list_notifications",
    "List notifications, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to notifications belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/notifications", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_notification",
    "Get details for a specific notification.",
    {
      notification_id: z.string().describe("The Check notification ID."),
    },
    async ({ notification_id }) => {
      const result = await checkApiGet(api, `/notifications/${notification_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_communications",
    "List communications, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to communications belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/communications", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_communication",
    "Get details for a specific communication.",
    {
      communication_id: z.string().describe("The Check communication ID."),
    },
    async ({ communication_id }) => {
      const result = await checkApiGet(api, `/communications/${communication_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_usage_summaries",
    "List usage summaries.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/usage_summaries", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_usage_records",
    "List usage records.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/usage_records", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_integration_partners",
    "List integration partners.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/integration_partners", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_integration_partner",
    "Get details for a specific integration partner.",
    {
      partner_id: z.string().describe("The Check integration partner ID."),
    },
    async ({ partner_id }) => {
      const result = await checkApiGet(api, `/integration_partners/${partner_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_integration_permissions",
    "List integration permissions.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/integration_permissions", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_integration_permission",
    "Get details for a specific integration permission.",
    {
      permission_id: z.string().describe("The Check integration permission ID."),
    },
    async ({ permission_id }) => {
      const result = await checkApiGet(api, `/integration_permissions/${permission_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_integration_accesses",
    "List integration accesses.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/integration_accesses", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_accounting_accounts",
    "List accounting accounts for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/companies/${company_id}/accounting_accounts`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_accounting_mappings",
    "Get accounting mappings for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiGet(api, `/companies/${company_id}/accounting_mappings`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_accounting_sync_attempts",
    "List accounting sync attempts for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/companies/${company_id}/accounting_sync_attempts`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_company_groups",
    "List company groups.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/company_groups", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "validate_address",
    "Validate a US address. Returns the validated/standardized address or validation errors.",
    {
      line1: z.string().describe("Street address line 1."),
      city: z.string().describe("City name."),
      state: z.string().describe("Two-letter state code."),
      postal_code: z.string().describe("ZIP or postal code."),
      line2: z.string().optional().describe("Street address line 2."),
      country: z.string().optional().describe("Country code (default: US)."),
    },
    async ({ line1, city, state, postal_code, line2, country }) => {
      const body: Record<string, unknown> = { line1, city, state, postal_code };
      if (line2 !== undefined) body.line2 = line2;
      if (country !== undefined) body.country = country;
      const result = await checkApiPost(api, "/addresses/validate", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_setups",
    "List setups, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to setups belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/setups", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_setup",
    "Get details for a specific setup.",
    {
      setup_id: z.string().describe("The Check setup ID."),
    },
    async ({ setup_id }) => {
      const result = await checkApiGet(api, `/setups/${setup_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_requirements",
    "List requirements, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to requirements belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/requirements", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_requirement",
    "Get details for a specific requirement.",
    {
      requirement_id: z.string().describe("The Check requirement ID."),
    },
    async ({ requirement_id }) => {
      const result = await checkApiGet(api, `/requirements/${requirement_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_applied_for_ids_report",
    "Get the applied-for IDs report across all companies.",
    {},
    async () => {
      const result = await checkApiGet(api, "/reports/applied_for_ids");
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // ---------------------------------------------------------------------------
  // Write tools
  // ---------------------------------------------------------------------------

  tool(
    server,
    filter,
    toolsetName,
    "create_communication",
    "Create a new communication.",
    {
      company: z.string().describe("The Check company ID."),
      type: z.string().optional().describe("Communication type."),
      email: z.record(z.unknown()).optional().describe("Email configuration object."),
    },
    async ({ company, type, email }) => {
      const body: Record<string, unknown> = { company };
      if (type !== undefined) body.type = type;
      if (email !== undefined) body.email = email;
      const result = await checkApiPost(api, "/communications", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "authorize_integration_partner",
    "Authorize an integration partner.",
    {
      partner_id: z.string().describe("The Check integration partner ID."),
      data: z.record(z.unknown()).optional().describe("Authorization data."),
    },
    async ({ partner_id, data }) => {
      const result = await checkApiPost(api, `/integration_partners/${partner_id}/authorize`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "refresh_accounting_accounts",
    "Refresh accounting accounts for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiPost(api, `/companies/${company_id}/accounting_accounts/refresh`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_accounting_mappings",
    "Update accounting mappings for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      data: z.record(z.unknown()).describe("Accounting mappings data."),
    },
    async ({ company_id, data }) => {
      const result = await checkApiPatch(api, `/companies/${company_id}/accounting_mappings`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "toggle_accounting_mappings",
    "Toggle accounting mappings for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      data: z.record(z.unknown()).describe("Toggle configuration data."),
    },
    async ({ company_id, data }) => {
      const result = await checkApiPost(api, `/companies/${company_id}/accounting_mappings/toggle`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "sync_accounting",
    "Trigger an accounting sync for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      data: z.record(z.unknown()).optional().describe("Sync configuration data."),
    },
    async ({ company_id, data }) => {
      const result = await checkApiPost(api, `/companies/${company_id}/accounting_sync`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_company_group",
    "Create a new company group.",
    {
      name: z.string().optional().describe("Name of the company group."),
      companies: z.array(z.record(z.unknown())).optional().describe("List of company objects to include in the group."),
    },
    async ({ name, companies }) => {
      const body: Record<string, unknown> = {};
      if (name !== undefined) body.name = name;
      if (companies !== undefined) body.companies = companies;
      const result = await checkApiPost(api, "/company_groups", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_company_group",
    "Update an existing company group.",
    {
      group_id: z.string().describe("The Check company group ID."),
      name: z.string().optional().describe("Name of the company group."),
      companies: z.array(z.record(z.unknown())).optional().describe("List of company objects to include in the group."),
    },
    async ({ group_id, name, companies }) => {
      const body: Record<string, unknown> = {};
      if (name !== undefined) body.name = name;
      if (companies !== undefined) body.companies = companies;
      const result = await checkApiPatch(api, `/company_groups/${group_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
