/** Tax tools for the Check API. */

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
    "get_company_tax_params",
    "Get tax parameters for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiGet(api, `/company_tax_params/${company_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_company_tax_param_settings",
    "List tax parameter settings for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/company_tax_params/${company_id}/settings`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_company_tax_param_setting",
    "Get a specific tax parameter setting for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      setting_id: z.string().describe("The tax parameter setting ID."),
    },
    async ({ company_id, setting_id }) => {
      const result = await checkApiGet(api, `/company_tax_params/${company_id}/settings/${setting_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_company_jurisdictions",
    "List tax jurisdictions for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/company_tax_params/${company_id}/jurisdictions`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_employee_tax_params",
    "List employee tax parameters, optionally filtered by employee.",
    {
      employee: z.string().optional().describe('Filter to tax params for this Check employee ID (e.g. "emp_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ employee, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (employee !== undefined) params.employee = employee;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/employee_tax_params", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_employee_tax_params",
    "Get tax parameters for a specific employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
    },
    async ({ employee_id }) => {
      const result = await checkApiGet(api, `/employee_tax_params/${employee_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_employee_tax_param_settings",
    "List tax parameter settings for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ employee_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/employee_tax_params/${employee_id}/settings`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_employee_tax_param_setting",
    "Get a specific tax parameter setting for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      setting_id: z.string().describe("The tax parameter setting ID."),
    },
    async ({ employee_id, setting_id }) => {
      const result = await checkApiGet(api, `/employee_tax_params/${employee_id}/settings/${setting_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_employee_jurisdictions",
    "List tax jurisdictions for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ employee_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/employee_tax_params/${employee_id}/jurisdictions`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "bulk_get_employee_tax_param_settings",
    "Bulk get employee tax parameter settings. Pass the full request body as a dict.",
    {
      data: z.record(z.unknown()).describe("Bulk get payload with employee IDs and filters."),
    },
    async ({ data }) => {
      const result = await checkApiPost(api, "/employee_tax_param_settings/bulk_get", data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_company_tax_elections",
    "List tax elections for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/companies/${company_id}/tax_elections`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_employee_tax_elections",
    "List tax elections for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ employee_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/employees/${employee_id}/tax_elections`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_tax_filings",
    "List tax filings, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to tax filings belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/tax_filings", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_tax_filing",
    "Get details for a specific tax filing.",
    {
      tax_filing_id: z.string().describe("The Check tax filing ID."),
    },
    async ({ tax_filing_id }) => {
      const result = await checkApiGet(api, `/tax_filings/${tax_filing_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_tax_filing_event",
    "Get details for a specific tax filing event.",
    {
      event_id: z.string().describe("The Check tax filing event ID."),
    },
    async ({ event_id }) => {
      const result = await checkApiGet(api, `/tax_filing_events/${event_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_exempt_status",
    "Get exempt status for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
    },
    async ({ employee_id }) => {
      const result = await checkApiGet(api, `/employees/${employee_id}/exempt_status`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_exemptible_taxes",
    "List exemptible taxes, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to exemptible taxes belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/exemptible_taxes", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_employee_tax_statements",
    "List employee tax statements, optionally filtered by employee.",
    {
      employee: z.string().optional().describe('Filter to tax statements for this Check employee ID (e.g. "emp_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ employee, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (employee !== undefined) params.employee = employee;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/employee_tax_statements", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_employee_tax_statement",
    "Get details for a specific employee tax statement.",
    {
      statement_id: z.string().describe("The Check employee tax statement ID."),
    },
    async ({ statement_id }) => {
      const result = await checkApiGet(api, `/employee_tax_statements/${statement_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_tax_package",
    "Get details for a specific tax package.",
    {
      tax_package_id: z.string().describe("The Check tax package ID."),
    },
    async ({ tax_package_id }) => {
      const result = await checkApiGet(api, `/tax_packages/${tax_package_id}`);
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
    "update_company_tax_params",
    "Update tax parameters for a company. Pass the full array of tax param updates.",
    {
      company_id: z.string().describe("The Check company ID."),
      data: z.array(z.record(z.unknown())).describe("Array of tax parameter update objects."),
    },
    async ({ company_id, data }) => {
      const result = await checkApiPatch(api, `/company_tax_params/${company_id}`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_employee_tax_params",
    "Update tax parameters for an employee. Pass the full array of tax param updates.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      data: z.array(z.record(z.unknown())).describe("Array of tax parameter update objects."),
    },
    async ({ employee_id, data }) => {
      const result = await checkApiPatch(api, `/employee_tax_params/${employee_id}`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "bulk_update_employee_tax_param_settings",
    "Bulk update employee tax parameter settings. Pass the full request body as a dict.",
    {
      data: z.record(z.unknown()).describe("Bulk update payload with settings data."),
    },
    async ({ data }) => {
      const result = await checkApiPost(api, "/employee_tax_param_settings/bulk_update", data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_company_tax_elections",
    "Create tax elections for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      data: z.record(z.unknown()).describe("Tax election creation data."),
    },
    async ({ company_id, data }) => {
      const result = await checkApiPost(api, `/companies/${company_id}/tax_elections`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_company_tax_elections",
    "Update tax elections for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      data: z.record(z.unknown()).describe("Tax election update data."),
    },
    async ({ company_id, data }) => {
      const result = await checkApiPatch(api, `/companies/${company_id}/tax_elections`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_employee_tax_elections",
    "Update tax elections for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      data: z.record(z.unknown()).describe("Tax election update data."),
    },
    async ({ employee_id, data }) => {
      const result = await checkApiPatch(api, `/employees/${employee_id}/tax_elections`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "request_tax_filing_refile",
    "Request a refile for a tax filing.",
    {
      tax_filing_id: z.string().describe("The Check tax filing ID."),
    },
    async ({ tax_filing_id }) => {
      const result = await checkApiPost(api, `/tax_filings/${tax_filing_id}/request_refile`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_exempt_status",
    "Update exempt status for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      data: z.record(z.unknown()).describe("Exempt status update data."),
    },
    async ({ employee_id, data }) => {
      const result = await checkApiPatch(api, `/employees/${employee_id}/exempt_status`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_exemptible_tax",
    "Update a specific exemptible tax.",
    {
      tax_id: z.string().describe("The Check exemptible tax ID."),
      data: z.record(z.unknown()).describe("Exemptible tax update data."),
    },
    async ({ tax_id, data }) => {
      const result = await checkApiPatch(api, `/exemptible_taxes/${tax_id}`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "bulk_update_exemptible_taxes",
    "Bulk update exemptible taxes. Pass the full request body as a dict.",
    {
      data: z.record(z.unknown()).describe("Bulk update payload with exemptible tax data."),
    },
    async ({ data }) => {
      const result = await checkApiPatch(api, "/exemptible_taxes", data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "request_tax_package",
    "Request a tax package for a company.",
    {
      company: z.string().describe("The Check company ID."),
      contents: z.record(z.unknown()).optional().describe("Tax package contents configuration."),
    },
    async ({ company, contents }) => {
      const body: Record<string, unknown> = { company };
      if (contents !== undefined) body.contents = contents;
      const result = await checkApiPost(api, "/tax_packages", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
