/** Contractor tools for the Check API. */

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
    "list_contractors",
    "List contractors, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to contractors belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return (default 10, max 100)."),
      ids: z.array(z.string()).optional().describe("Filter to specific contractor IDs."),
      cursor: z.string().optional().describe("Pagination cursor from a previous response."),
    },
    async ({ company, limit, ids, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (ids !== undefined) params.ids = ids.join(",");
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/contractors", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_contractor",
    "Get details for a specific contractor.",
    {
      contractor_id: z.string().describe('The Check contractor ID (e.g. "ctr_xxxxx").'),
    },
    async ({ contractor_id }) => {
      const result = await checkApiGet(api, `/contractors/${contractor_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_contractor",
    "Create a new contractor.",
    {
      company: z.string().describe("The Check company ID."),
      type: z.string().optional().describe('Contractor type — "individual" or "business".'),
      first_name: z.string().optional().describe("Contractor's first name (or business primary contact's first name)."),
      middle_name: z.string().optional().describe("Contractor's middle name."),
      last_name: z.string().optional().describe("Contractor's last name (or business primary contact's last name)."),
      business_name: z.string().optional().describe("Business name (for business-type contractors)."),
      dob: z.string().optional().describe("Date of birth (YYYY-MM-DD)."),
      start_date: z.string().optional().describe("Most recent start date of contract (YYYY-MM-DD)."),
      termination_date: z.string().optional().describe("Most recent termination date (YYYY-MM-DD)."),
      workplaces: z.array(z.string()).optional().describe("List of workplace IDs where the contractor works."),
      primary_workplace: z.string().optional().describe("Workplace ID of the contractor's primary workplace."),
      email: z.string().optional().describe("Contractor's email address."),
      ssn: z.string().optional().describe("Contractor's Social Security Number."),
      ein: z.string().optional().describe("Contractor's Employer Identification Number (for businesses)."),
      default_net_pay_split: z.string().optional().describe("ID of contractor's default net pay split."),
      payment_method_preference: z.string().optional().describe('"direct_deposit" or "manual".'),
      address: z.record(z.unknown()).optional().describe("Address object with keys: line1, line2, city, state, postal_code, country."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ company, type, first_name, middle_name, last_name, business_name, dob, start_date, termination_date, workplaces, primary_workplace, email, ssn, ein, default_net_pay_split, payment_method_preference, address, metadata }) => {
      const body: Record<string, unknown> = { company };
      if (type !== undefined) body.type = type;
      if (first_name !== undefined) body.first_name = first_name;
      if (middle_name !== undefined) body.middle_name = middle_name;
      if (last_name !== undefined) body.last_name = last_name;
      if (business_name !== undefined) body.business_name = business_name;
      if (dob !== undefined) body.dob = dob;
      if (start_date !== undefined) body.start_date = start_date;
      if (termination_date !== undefined) body.termination_date = termination_date;
      if (workplaces !== undefined) body.workplaces = workplaces;
      if (primary_workplace !== undefined) body.primary_workplace = primary_workplace;
      if (email !== undefined) body.email = email;
      if (ssn !== undefined) body.ssn = ssn;
      if (ein !== undefined) body.ein = ein;
      if (default_net_pay_split !== undefined) body.default_net_pay_split = default_net_pay_split;
      if (payment_method_preference !== undefined) body.payment_method_preference = payment_method_preference;
      if (address !== undefined) body.address = address;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPost(api, "/contractors", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_contractor",
    "Update an existing contractor.",
    {
      contractor_id: z.string().describe("The Check contractor ID."),
      type: z.string().optional().describe('Contractor type — "individual" or "business".'),
      first_name: z.string().optional().describe("Contractor's first name."),
      middle_name: z.string().optional().describe("Contractor's middle name."),
      last_name: z.string().optional().describe("Contractor's last name."),
      business_name: z.string().optional().describe("Business name (for business-type contractors)."),
      dob: z.string().optional().describe("Date of birth (YYYY-MM-DD)."),
      start_date: z.string().optional().describe("Most recent start date of contract (YYYY-MM-DD)."),
      termination_date: z.string().optional().describe("Most recent termination date (YYYY-MM-DD)."),
      workplaces: z.array(z.string()).optional().describe("List of workplace IDs where the contractor works."),
      primary_workplace: z.string().optional().describe("Workplace ID of the contractor's primary workplace."),
      email: z.string().optional().describe("Contractor's email address."),
      ssn: z.string().optional().describe("Contractor's Social Security Number."),
      ein: z.string().optional().describe("Contractor's Employer Identification Number (for businesses)."),
      default_net_pay_split: z.string().optional().describe("ID of contractor's default net pay split."),
      payment_method_preference: z.string().optional().describe('"direct_deposit" or "manual".'),
      address: z.record(z.unknown()).optional().describe("Address object with keys: line1, line2, city, state, postal_code, country."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ contractor_id, type, first_name, middle_name, last_name, business_name, dob, start_date, termination_date, workplaces, primary_workplace, email, ssn, ein, default_net_pay_split, payment_method_preference, address, metadata }) => {
      const body: Record<string, unknown> = {};
      if (type !== undefined) body.type = type;
      if (first_name !== undefined) body.first_name = first_name;
      if (middle_name !== undefined) body.middle_name = middle_name;
      if (last_name !== undefined) body.last_name = last_name;
      if (business_name !== undefined) body.business_name = business_name;
      if (dob !== undefined) body.dob = dob;
      if (start_date !== undefined) body.start_date = start_date;
      if (termination_date !== undefined) body.termination_date = termination_date;
      if (workplaces !== undefined) body.workplaces = workplaces;
      if (primary_workplace !== undefined) body.primary_workplace = primary_workplace;
      if (email !== undefined) body.email = email;
      if (ssn !== undefined) body.ssn = ssn;
      if (ein !== undefined) body.ein = ein;
      if (default_net_pay_split !== undefined) body.default_net_pay_split = default_net_pay_split;
      if (payment_method_preference !== undefined) body.payment_method_preference = payment_method_preference;
      if (address !== undefined) body.address = address;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPatch(api, `/contractors/${contractor_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "onboard_contractor",
    "Onboard a contractor, transitioning them to active status.",
    {
      contractor_id: z.string().describe("The Check contractor ID."),
    },
    async ({ contractor_id }) => {
      const result = await checkApiPost(api, `/contractors/${contractor_id}/onboard`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_contractor_payments_for_contractor",
    "List payments for a specific contractor.",
    {
      contractor_id: z.string().describe("The Check contractor ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ contractor_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/contractors/${contractor_id}/payments`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_contractor_payment_for_payroll",
    "Get a contractor payment for a specific payroll.",
    {
      contractor_id: z.string().describe("The Check contractor ID."),
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ contractor_id, payroll_id }) => {
      const result = await checkApiGet(api, `/contractors/${contractor_id}/payments/${payroll_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_contractor_forms",
    "List forms for a contractor.",
    {
      contractor_id: z.string().describe("The Check contractor ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ contractor_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/contractors/${contractor_id}/forms`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "submit_contractor_form",
    "Submit a contractor form.",
    {
      contractor_id: z.string().describe("The Check contractor ID."),
      form_id: z.string().describe("The form ID."),
      parameters: z.array(z.record(z.unknown())).optional().describe('List of name/value objects representing form fields. Example: [{"name": "field_name", "value": "field_value"}].'),
    },
    async ({ contractor_id, form_id, parameters }) => {
      const body: Record<string, unknown> | undefined = parameters !== undefined ? { parameters } : undefined;
      const result = await checkApiPost(api, `/contractors/${contractor_id}/forms/${form_id}/submit`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "reveal_contractor_ssn",
    "Reveal the SSN/EIN for a contractor.",
    {
      contractor_id: z.string().describe("The Check contractor ID."),
    },
    async ({ contractor_id }) => {
      const result = await checkApiGet(api, `/contractors/${contractor_id}/reveal`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
