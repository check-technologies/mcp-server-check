/** Company tools for the Check API. */

import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import {
  checkApiGet,
  checkApiPost,
  checkApiPatch,
  checkApiPut,
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
    "list_companies",
    "List companies, optionally filtering by active status or specific IDs.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      active: z.boolean().optional().describe("Filter by active status."),
      ids: z.array(z.string()).optional().describe("Filter to specific company IDs."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, active, ids, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (active !== undefined) params.active = String(active);
      if (ids !== undefined) params.ids = ids.join(",");
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/companies", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_company",
    "Get details for a specific company.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiGet(api, `/companies/${company_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_company_paydays",
    "Get paydays for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      start_date: z.string().optional().describe("Start date filter (YYYY-MM-DD)."),
      end_date: z.string().optional().describe("End date filter (YYYY-MM-DD)."),
      pay_schedule: z.string().optional().describe("Filter to a specific pay schedule ID."),
    },
    async ({ company_id, start_date, end_date, pay_schedule }) => {
      const params: Record<string, unknown> = {};
      if (start_date !== undefined) params.start_date = start_date;
      if (end_date !== undefined) params.end_date = end_date;
      if (pay_schedule !== undefined) params.pay_schedule = pay_schedule;
      const result = await checkApiGet(api, `/companies/${company_id}/paydays`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_company_tax_deposits",
    "List tax deposits for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/companies/${company_id}/tax_deposits`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_company_benefit_aggregations",
    "Get benefit aggregations for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      start_date: z.string().optional().describe("Start date filter (YYYY-MM-DD)."),
      end_date: z.string().optional().describe("End date filter (YYYY-MM-DD)."),
    },
    async ({ company_id, start_date, end_date }) => {
      const params: Record<string, unknown> = {};
      if (start_date !== undefined) params.start_date = start_date;
      if (end_date !== undefined) params.end_date = end_date;
      const result = await checkApiGet(api, `/companies/${company_id}/benefit_aggregations`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_payroll_journal_report",
    "Get the payroll journal report for a company within a date range.",
    {
      company_id: z.string().describe("The Check company ID."),
      start_date: z.string().describe("Report start date (YYYY-MM-DD)."),
      end_date: z.string().describe("Report end date (YYYY-MM-DD)."),
    },
    async ({ company_id, start_date, end_date }) => {
      const params: Record<string, unknown> = { start_date, end_date };
      const result = await checkApiGet(api, `/companies/${company_id}/reports/payroll_journal`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_payroll_summary_report",
    "Get the payroll summary report for a company within a date range.",
    {
      company_id: z.string().describe("The Check company ID."),
      start_date: z.string().describe("Report start date (YYYY-MM-DD)."),
      end_date: z.string().describe("Report end date (YYYY-MM-DD)."),
    },
    async ({ company_id, start_date, end_date }) => {
      const params: Record<string, unknown> = { start_date, end_date };
      const result = await checkApiGet(api, `/companies/${company_id}/reports/payroll_summary`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_tax_liabilities_report",
    "Get the tax liabilities report for a company within a date range.",
    {
      company_id: z.string().describe("The Check company ID."),
      start_date: z.string().describe("Report start date (YYYY-MM-DD)."),
      end_date: z.string().describe("Report end date (YYYY-MM-DD)."),
    },
    async ({ company_id, start_date, end_date }) => {
      const params: Record<string, unknown> = { start_date, end_date };
      const result = await checkApiGet(api, `/companies/${company_id}/reports/tax_liabilities`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_contractor_payments_report",
    "Get the contractor payments report for a company within a date range.",
    {
      company_id: z.string().describe("The Check company ID."),
      start_date: z.string().describe("Report start date (YYYY-MM-DD)."),
      end_date: z.string().describe("Report end date (YYYY-MM-DD)."),
    },
    async ({ company_id, start_date, end_date }) => {
      const params: Record<string, unknown> = { start_date, end_date };
      const result = await checkApiGet(api, `/companies/${company_id}/reports/contractor_payments`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_child_support_payments_report",
    "Get the child support payments report for a company within a date range.",
    {
      company_id: z.string().describe("The Check company ID."),
      start_date: z.string().describe("Report start date (YYYY-MM-DD)."),
      end_date: z.string().describe("Report end date (YYYY-MM-DD)."),
    },
    async ({ company_id, start_date, end_date }) => {
      const params: Record<string, unknown> = { start_date, end_date };
      const result = await checkApiGet(api, `/companies/${company_id}/reports/child_support_payments`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_w4_exemption_status_report",
    "Get the W-4 exemption status report for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiGet(api, `/companies/${company_id}/reports/w4_exemption_status`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_applied_for_ids_detailed_report",
    "Get the detailed applied-for IDs report for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiGet(api, `/companies/${company_id}/reports/applied_for_ids_detailed`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_w2_preview_report",
    "Get the W-2 preview report for a company for a specific year.",
    {
      company_id: z.string().describe("The Check company ID."),
      year: z.string().describe("Tax year (e.g. 2024)."),
    },
    async ({ company_id, year }) => {
      const params: Record<string, unknown> = { year };
      const result = await checkApiGet(api, `/companies/${company_id}/reports/w2_preview`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_federal_ein_verifications",
    "List federal EIN verifications for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/companies/${company_id}/federal_ein_verifications`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_federal_ein_verification",
    "Get details for a specific federal EIN verification.",
    {
      company_id: z.string().describe("The Check company ID."),
      verification_id: z.string().describe("The federal EIN verification ID."),
    },
    async ({ company_id, verification_id }) => {
      const result = await checkApiGet(api, `/companies/${company_id}/federal_ein_verifications/${verification_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "list_signatories",
    "List signatories for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company_id, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, `/companies/${company_id}/signatories`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_enrollment_profile",
    "Get the enrollment profile for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiGet(api, `/companies/${company_id}/enrollment_profile`);
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
    "create_company",
    "Create a new company.",
    {
      legal_name: z.string().describe("The company's legal name."),
      trade_name: z.string().optional().describe("The company's trade name / DBA."),
      other_business_name: z.string().optional().describe("Any other business name."),
      business_type: z.string().optional().describe('Business entity type (e.g. "llc", "s_corp", "c_corp").'),
      industry_type: z.string().optional().describe("Industry type / NAICS code."),
      website: z.string().optional().describe("Company website URL."),
      email: z.string().optional().describe("Company email address."),
      phone: z.string().optional().describe("Company phone number."),
      address: z.record(z.unknown()).optional().describe("Company address dict with keys: line1, line2, city, state, postal_code, country."),
      pay_frequency: z.string().optional().describe('Default pay frequency (e.g. "weekly", "biweekly", "semimonthly", "monthly").'),
      start_date: z.string().optional().describe("Company start date (YYYY-MM-DD)."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ legal_name, trade_name, other_business_name, business_type, industry_type, website, email, phone, address, pay_frequency, start_date, metadata }) => {
      const body: Record<string, unknown> = { legal_name };
      if (trade_name !== undefined) body.trade_name = trade_name;
      if (other_business_name !== undefined) body.other_business_name = other_business_name;
      if (business_type !== undefined) body.business_type = business_type;
      if (industry_type !== undefined) body.industry_type = industry_type;
      if (website !== undefined) body.website = website;
      if (email !== undefined) body.email = email;
      if (phone !== undefined) body.phone = phone;
      if (address !== undefined) body.address = address;
      if (pay_frequency !== undefined) body.pay_frequency = pay_frequency;
      if (start_date !== undefined) body.start_date = start_date;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPost(api, "/companies", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_company",
    "Update an existing company.",
    {
      company_id: z.string().describe("The Check company ID."),
      legal_name: z.string().optional().describe("The company's legal name."),
      trade_name: z.string().optional().describe("The company's trade name / DBA."),
      other_business_name: z.string().optional().describe("Any other business name."),
      business_type: z.string().optional().describe('Business entity type (e.g. "llc", "s_corp", "c_corp").'),
      industry_type: z.string().optional().describe("Industry type / NAICS code."),
      website: z.string().optional().describe("Company website URL."),
      email: z.string().optional().describe("Company email address."),
      phone: z.string().optional().describe("Company phone number."),
      address: z.record(z.unknown()).optional().describe("Company address dict with keys: line1, line2, city, state, postal_code, country."),
      principal_place_of_business: z.record(z.unknown()).optional().describe("Principal place of business address."),
      pay_frequency: z.string().optional().describe('Default pay frequency (e.g. "weekly", "biweekly", "semimonthly", "monthly").'),
      processing_period: z.string().optional().describe('Processing period setting (e.g. "two_day", "four_day").'),
      start_date: z.string().optional().describe("Company start date (YYYY-MM-DD)."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
      default_bank_account: z.string().optional().describe("Default bank account ID."),
    },
    async ({ company_id, legal_name, trade_name, other_business_name, business_type, industry_type, website, email, phone, address, principal_place_of_business, pay_frequency, processing_period, start_date, metadata, default_bank_account }) => {
      const body: Record<string, unknown> = {};
      if (legal_name !== undefined) body.legal_name = legal_name;
      if (trade_name !== undefined) body.trade_name = trade_name;
      if (other_business_name !== undefined) body.other_business_name = other_business_name;
      if (business_type !== undefined) body.business_type = business_type;
      if (industry_type !== undefined) body.industry_type = industry_type;
      if (website !== undefined) body.website = website;
      if (email !== undefined) body.email = email;
      if (phone !== undefined) body.phone = phone;
      if (address !== undefined) body.address = address;
      if (principal_place_of_business !== undefined) body.principal_place_of_business = principal_place_of_business;
      if (pay_frequency !== undefined) body.pay_frequency = pay_frequency;
      if (processing_period !== undefined) body.processing_period = processing_period;
      if (start_date !== undefined) body.start_date = start_date;
      if (metadata !== undefined) body.metadata = metadata;
      if (default_bank_account !== undefined) body.default_bank_account = default_bank_account;
      const result = await checkApiPatch(api, `/companies/${company_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "onboard_company",
    "Onboard a company, transitioning it from setup to active.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiPost(api, `/companies/${company_id}/onboard`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_signatory",
    "Create a new signatory for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
      first_name: z.string().describe("Signatory's first name."),
      last_name: z.string().describe("Signatory's last name."),
      title: z.string().describe("Signatory's title."),
      email: z.string().describe("Signatory's email address."),
      middle_name: z.string().optional().describe("Signatory's middle name."),
    },
    async ({ company_id, first_name, last_name, title, email, middle_name }) => {
      const body: Record<string, unknown> = { first_name, last_name, title, email };
      if (middle_name !== undefined) body.middle_name = middle_name;
      const result = await checkApiPost(api, `/companies/${company_id}/signatories`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_enrollment_profile",
    "Create an enrollment profile for a company. Pass all fields as a data dict since there are 20+ optional fields.",
    {
      company_id: z.string().describe("The Check company ID."),
      data: z.record(z.unknown()).describe("Enrollment profile data with fields such as employee_count, contractor_count, pay_period_amount, previous_payroll_provider, first_payroll, first_payroll_of_year, user_since, expected_first_payday, approved_for_payment_processing, etc."),
    },
    async ({ company_id, data }) => {
      const result = await checkApiPut(api, `/companies/${company_id}/enrollment_profile`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_enrollment_profile",
    "Update the enrollment profile for a company. Pass all fields as a data dict since there are 20+ optional fields.",
    {
      company_id: z.string().describe("The Check company ID."),
      data: z.record(z.unknown()).describe("Enrollment profile update data with fields such as employee_count, contractor_count, pay_period_amount, previous_payroll_provider, first_payroll, first_payroll_of_year, user_since, expected_first_payday, approved_for_payment_processing, etc."),
    },
    async ({ company_id, data }) => {
      const result = await checkApiPatch(api, `/companies/${company_id}/enrollment_profile`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "start_implementation",
    "Start implementation for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiPost(api, `/companies/${company_id}/start_implementation`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "cancel_implementation",
    "Cancel implementation for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiPost(api, `/companies/${company_id}/cancel_implementation`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "request_embedded_setup",
    "Request embedded setup for a company.",
    {
      company_id: z.string().describe("The Check company ID."),
    },
    async ({ company_id }) => {
      const result = await checkApiPost(api, `/companies/${company_id}/request_embedded_setup`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
