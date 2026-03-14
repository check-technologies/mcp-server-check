/** Employee tools for the Check API. */

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
    "list_employees",
    "List employees, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to employees belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return (default 10, max 100)."),
      ids: z.array(z.string()).optional().describe("Filter to specific employee IDs."),
      cursor: z.string().optional().describe("Pagination cursor from a previous response."),
    },
    async ({ company, limit, ids, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (ids !== undefined) params.ids = ids.join(",");
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/employees", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_employee",
    "Get details for a specific employee.",
    {
      employee_id: z.string().describe('The Check employee ID (e.g. "emp_xxxxx").'),
    },
    async ({ employee_id }) => {
      const result = await checkApiGet(api, `/employees/${employee_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_employee",
    "Create a new employee.",
    {
      company: z.string().describe("The Check company ID the employee belongs to."),
      first_name: z.string().describe("Employee's first name."),
      last_name: z.string().describe("Employee's last name."),
      middle_name: z.string().optional().describe("Employee's middle name."),
      email: z.string().optional().describe("Employee's email address."),
      dob: z.string().optional().describe("Date of birth (YYYY-MM-DD)."),
      start_date: z.string().optional().describe("Most recent start date of employment (YYYY-MM-DD)."),
      termination_date: z.string().optional().describe("Most recent termination date (YYYY-MM-DD)."),
      residence: z.record(z.unknown()).optional().describe("Residence address object with keys: line1, line2, city, state, postal_code, country."),
      workplaces: z.array(z.string()).optional().describe("List of workplace IDs where the employee works."),
      primary_workplace: z.string().optional().describe("Workplace ID of the employee's primary workplace."),
      ssn: z.string().optional().describe("Employee's Social Security Number. Only last four digits available after set."),
      payment_method_preference: z.string().optional().describe('"direct_deposit" or "manual".'),
      default_net_pay_split: z.string().optional().describe("ID of employee's default net pay split."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ company, first_name, last_name, middle_name, email, dob, start_date, termination_date, residence, workplaces, primary_workplace, ssn, payment_method_preference, default_net_pay_split, metadata }) => {
      const body: Record<string, unknown> = { company, first_name, last_name };
      if (middle_name !== undefined) body.middle_name = middle_name;
      if (email !== undefined) body.email = email;
      if (dob !== undefined) body.dob = dob;
      if (start_date !== undefined) body.start_date = start_date;
      if (termination_date !== undefined) body.termination_date = termination_date;
      if (residence !== undefined) body.residence = residence;
      if (workplaces !== undefined) body.workplaces = workplaces;
      if (primary_workplace !== undefined) body.primary_workplace = primary_workplace;
      if (ssn !== undefined) body.ssn = ssn;
      if (payment_method_preference !== undefined) body.payment_method_preference = payment_method_preference;
      if (default_net_pay_split !== undefined) body.default_net_pay_split = default_net_pay_split;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPost(api, "/employees", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_employee",
    "Update an existing employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      first_name: z.string().optional().describe("Employee's first name."),
      middle_name: z.string().optional().describe("Employee's middle name."),
      last_name: z.string().optional().describe("Employee's last name."),
      email: z.string().optional().describe("Employee's email address."),
      dob: z.string().optional().describe("Date of birth (YYYY-MM-DD)."),
      start_date: z.string().optional().describe("Most recent start date of employment (YYYY-MM-DD)."),
      termination_date: z.string().optional().describe("Most recent termination date (YYYY-MM-DD)."),
      residence: z.record(z.unknown()).optional().describe("Residence address object with keys: line1, line2, city, state, postal_code, country."),
      workplaces: z.array(z.string()).optional().describe("List of workplace IDs where the employee works."),
      primary_workplace: z.string().optional().describe("Workplace ID of the employee's primary workplace."),
      ssn: z.string().optional().describe("Employee's Social Security Number."),
      payment_method_preference: z.string().optional().describe('"direct_deposit" or "manual".'),
      default_net_pay_split: z.string().optional().describe("ID of employee's default net pay split."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ employee_id, first_name, middle_name, last_name, email, dob, start_date, termination_date, residence, workplaces, primary_workplace, ssn, payment_method_preference, default_net_pay_split, metadata }) => {
      const body: Record<string, unknown> = {};
      if (first_name !== undefined) body.first_name = first_name;
      if (middle_name !== undefined) body.middle_name = middle_name;
      if (last_name !== undefined) body.last_name = last_name;
      if (email !== undefined) body.email = email;
      if (dob !== undefined) body.dob = dob;
      if (start_date !== undefined) body.start_date = start_date;
      if (termination_date !== undefined) body.termination_date = termination_date;
      if (residence !== undefined) body.residence = residence;
      if (workplaces !== undefined) body.workplaces = workplaces;
      if (primary_workplace !== undefined) body.primary_workplace = primary_workplace;
      if (ssn !== undefined) body.ssn = ssn;
      if (payment_method_preference !== undefined) body.payment_method_preference = payment_method_preference;
      if (default_net_pay_split !== undefined) body.default_net_pay_split = default_net_pay_split;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPatch(api, `/employees/${employee_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "onboard_employee",
    "Onboard an employee, transitioning them to active status.",
    {
      employee_id: z.string().describe("The Check employee ID."),
    },
    async ({ employee_id }) => {
      const result = await checkApiPost(api, `/employees/${employee_id}/onboard`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Paystubs ---

  tool(
    server,
    filter,
    toolsetName,
    "list_employee_paystubs",
    "List paystubs for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ employee_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/employees/${employee_id}/paystubs`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_employee_paystub",
    "Get a specific paystub for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      payroll_id: z.string().describe("The Check payroll ID."),
    },
    async ({ employee_id, payroll_id }) => {
      const result = await checkApiGet(api, `/employees/${employee_id}/paystubs/${payroll_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Forms ---

  tool(
    server,
    filter,
    toolsetName,
    "list_employee_forms",
    "List forms for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ employee_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/employees/${employee_id}/forms`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_employee_form",
    "Get a specific form for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      form_id: z.string().describe("The form ID."),
    },
    async ({ employee_id, form_id }) => {
      const result = await checkApiGet(api, `/employees/${employee_id}/forms/${form_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "submit_employee_form",
    "Submit an employee form.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      form_id: z.string().describe("The form ID."),
      parameters: z.array(z.record(z.unknown())).optional().describe('List of name/value objects representing form fields. Example: [{"name": "field_name", "value": "field_value"}].'),
    },
    async ({ employee_id, form_id, parameters }) => {
      const body: Record<string, unknown> | undefined = parameters !== undefined ? { parameters } : undefined;
      const result = await checkApiPost(api, `/employees/${employee_id}/forms/${form_id}/submit`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "sign_and_submit_employee_form",
    "Sign and submit an employee form.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      form_id: z.string().describe("The form ID."),
      parameters: z.array(z.record(z.unknown())).optional().describe('List of name/value objects representing form fields. Example: [{"name": "field_name", "value": "field_value"}].'),
    },
    async ({ employee_id, form_id, parameters }) => {
      const body: Record<string, unknown> | undefined = parameters !== undefined ? { parameters } : undefined;
      const result = await checkApiPost(api, `/employees/${employee_id}/forms/${form_id}/sign_and_submit`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Company Defined Attributes ---

  tool(
    server,
    filter,
    toolsetName,
    "get_employee_company_defined_attributes",
    "Get company-defined attributes for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
    },
    async ({ employee_id }) => {
      const result = await checkApiGet(api, `/employees/${employee_id}/company_defined_attributes`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_employee_company_defined_attributes",
    "Update company-defined attributes for an employee. The schema is dynamic and defined per-company, so attributes are passed as a free-form object.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      data: z.record(z.unknown()).describe("Attributes to update (schema varies by company configuration)."),
    },
    async ({ employee_id, data }) => {
      const result = await checkApiPatch(api, `/employees/${employee_id}/company_defined_attributes`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Reciprocity Elections ---

  tool(
    server,
    filter,
    toolsetName,
    "get_employee_reciprocity_elections",
    "Get reciprocity elections for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
    },
    async ({ employee_id }) => {
      const result = await checkApiGet(api, `/employees/${employee_id}/reciprocity_elections`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_employee_reciprocity_elections",
    "Update reciprocity elections for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      data: z.record(z.unknown()).describe("Reciprocity election data (complex nested structure)."),
    },
    async ({ employee_id, data }) => {
      const result = await checkApiPatch(api, `/employees/${employee_id}/reciprocity_elections`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Other ---

  tool(
    server,
    filter,
    toolsetName,
    "reveal_employee_ssn",
    "Reveal the SSN for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
    },
    async ({ employee_id }) => {
      const result = await checkApiGet(api, `/employees/${employee_id}/reveal`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "authorize_employee_partner",
    "Authorize a partner for an employee.",
    {
      employee_id: z.string().describe("The Check employee ID."),
      data: z.record(z.unknown()).optional().describe("Partner authorization details."),
    },
    async ({ employee_id, data }) => {
      const result = await checkApiPost(api, `/employees/${employee_id}/authorize_partner`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
