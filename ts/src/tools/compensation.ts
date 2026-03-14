/** Compensation tools for the Check API. */

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
  // ---------------------------------------------------------------------------
  // Pay Schedules
  // ---------------------------------------------------------------------------

  tool(
    server,
    filter,
    toolsetName,
    "list_pay_schedules",
    "List pay schedules, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to pay schedules belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/pay_schedules", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_pay_schedule",
    "Get details for a specific pay schedule.",
    {
      pay_schedule_id: z.string().describe("The Check pay schedule ID."),
    },
    async ({ pay_schedule_id }) => {
      const result = await checkApiGet(api, `/pay_schedules/${pay_schedule_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_pay_schedule",
    "Create a new pay schedule.",
    {
      company: z.string().describe("The Check company ID."),
      pay_frequency: z.string().describe('Pay frequency (e.g. "weekly", "biweekly", "semimonthly", "monthly").'),
      first_payday: z.string().describe("First payday date (YYYY-MM-DD)."),
      first_period_end: z.string().describe("First period end date (YYYY-MM-DD)."),
      second_payday: z.string().optional().describe("Second payday date for semimonthly schedules (YYYY-MM-DD)."),
      name: z.string().optional().describe("Human-readable name for the pay schedule."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ company, pay_frequency, first_payday, first_period_end, second_payday, name, metadata }) => {
      const body: Record<string, unknown> = { company, pay_frequency, first_payday, first_period_end };
      if (second_payday !== undefined) body.second_payday = second_payday;
      if (name !== undefined) body.name = name;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPost(api, "/pay_schedules", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_pay_schedule",
    "Update an existing pay schedule.",
    {
      pay_schedule_id: z.string().describe("The Check pay schedule ID."),
      pay_frequency: z.string().optional().describe('Pay frequency (e.g. "weekly", "biweekly", "semimonthly", "monthly").'),
      first_payday: z.string().optional().describe("First payday date (YYYY-MM-DD)."),
      first_period_end: z.string().optional().describe("First period end date (YYYY-MM-DD)."),
      second_payday: z.string().optional().describe("Second payday date for semimonthly schedules (YYYY-MM-DD)."),
      name: z.string().optional().describe("Human-readable name for the pay schedule."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ pay_schedule_id, pay_frequency, first_payday, first_period_end, second_payday, name, metadata }) => {
      const body: Record<string, unknown> = {};
      if (pay_frequency !== undefined) body.pay_frequency = pay_frequency;
      if (first_payday !== undefined) body.first_payday = first_payday;
      if (first_period_end !== undefined) body.first_period_end = first_period_end;
      if (second_payday !== undefined) body.second_payday = second_payday;
      if (name !== undefined) body.name = name;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPatch(api, `/pay_schedules/${pay_schedule_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "delete_pay_schedule",
    "Delete a pay schedule.",
    {
      pay_schedule_id: z.string().describe("The Check pay schedule ID."),
    },
    async ({ pay_schedule_id }) => {
      const result = await checkApiDelete(api, `/pay_schedules/${pay_schedule_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_pay_schedule_paydays",
    "Get paydays for a pay schedule.",
    {
      pay_schedule_id: z.string().describe("The Check pay schedule ID."),
      start_date: z.string().optional().describe("Start date filter (YYYY-MM-DD)."),
      end_date: z.string().optional().describe("End date filter (YYYY-MM-DD)."),
    },
    async ({ pay_schedule_id, start_date, end_date }) => {
      const params: Record<string, unknown> = {};
      if (start_date !== undefined) params.start_date = start_date;
      if (end_date !== undefined) params.end_date = end_date;
      const result = await checkApiGet(api, `/pay_schedules/${pay_schedule_id}/paydays`, params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // ---------------------------------------------------------------------------
  // Benefits
  // ---------------------------------------------------------------------------

  tool(
    server,
    filter,
    toolsetName,
    "list_benefits",
    "List benefits, optionally filtered by company or employee.",
    {
      company: z.string().optional().describe('Filter to benefits belonging to this Check company ID (e.g. "com_xxxxx").'),
      employee: z.string().optional().describe('Filter to benefits for this Check employee ID (e.g. "emp_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, employee, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (employee !== undefined) params.employee = employee;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/benefits", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_benefit",
    "Get details for a specific benefit.",
    {
      benefit_id: z.string().describe("The Check benefit ID."),
    },
    async ({ benefit_id }) => {
      const result = await checkApiGet(api, `/benefits/${benefit_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_benefit",
    "Create a new employee benefit.",
    {
      employee: z.string().describe("The Check employee ID."),
      company_benefit: z.string().describe("The Check company benefit ID."),
      benefit: z.string().optional().describe("Benefit type identifier."),
      period: z.string().optional().describe('Deduction period (e.g. "per_paycheck").'),
      description: z.string().optional().describe("Benefit description."),
      company_contribution_amount: z.string().optional().describe("Company contribution amount per period."),
      company_contribution_percent: z.number().optional().describe("Company contribution percentage."),
      company_period_amount: z.string().optional().describe("Company contribution period cap."),
      employee_contribution_amount: z.string().optional().describe("Employee contribution amount per period."),
      employee_contribution_percent: z.number().optional().describe("Employee contribution percentage."),
      employee_period_amount: z.string().optional().describe("Employee contribution period cap."),
      effective_start: z.string().optional().describe("Effective start date (YYYY-MM-DD)."),
      effective_end: z.string().optional().describe("Effective end date (YYYY-MM-DD)."),
      hsa_contribution_limit: z.string().optional().describe("HSA contribution limit type."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ employee, company_benefit, benefit, period, description, company_contribution_amount, company_contribution_percent, company_period_amount, employee_contribution_amount, employee_contribution_percent, employee_period_amount, effective_start, effective_end, hsa_contribution_limit, metadata }) => {
      const body: Record<string, unknown> = { employee, company_benefit };
      if (benefit !== undefined) body.benefit = benefit;
      if (period !== undefined) body.period = period;
      if (description !== undefined) body.description = description;
      if (company_contribution_amount !== undefined) body.company_contribution_amount = company_contribution_amount;
      if (company_contribution_percent !== undefined) body.company_contribution_percent = company_contribution_percent;
      if (company_period_amount !== undefined) body.company_period_amount = company_period_amount;
      if (employee_contribution_amount !== undefined) body.employee_contribution_amount = employee_contribution_amount;
      if (employee_contribution_percent !== undefined) body.employee_contribution_percent = employee_contribution_percent;
      if (employee_period_amount !== undefined) body.employee_period_amount = employee_period_amount;
      if (effective_start !== undefined) body.effective_start = effective_start;
      if (effective_end !== undefined) body.effective_end = effective_end;
      if (hsa_contribution_limit !== undefined) body.hsa_contribution_limit = hsa_contribution_limit;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPost(api, "/benefits", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_benefit",
    "Update an existing employee benefit.",
    {
      benefit_id: z.string().describe("The Check benefit ID."),
      benefit: z.string().optional().describe("Benefit type identifier."),
      period: z.string().optional().describe('Deduction period (e.g. "per_paycheck").'),
      description: z.string().optional().describe("Benefit description."),
      company_contribution_amount: z.string().optional().describe("Company contribution amount per period."),
      company_contribution_percent: z.number().optional().describe("Company contribution percentage."),
      company_period_amount: z.string().optional().describe("Company contribution period cap."),
      employee_contribution_amount: z.string().optional().describe("Employee contribution amount per period."),
      employee_contribution_percent: z.number().optional().describe("Employee contribution percentage."),
      employee_period_amount: z.string().optional().describe("Employee contribution period cap."),
      effective_start: z.string().optional().describe("Effective start date (YYYY-MM-DD)."),
      effective_end: z.string().optional().describe("Effective end date (YYYY-MM-DD)."),
      hsa_contribution_limit: z.string().optional().describe("HSA contribution limit type."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ benefit_id, benefit, period, description, company_contribution_amount, company_contribution_percent, company_period_amount, employee_contribution_amount, employee_contribution_percent, employee_period_amount, effective_start, effective_end, hsa_contribution_limit, metadata }) => {
      const body: Record<string, unknown> = {};
      if (benefit !== undefined) body.benefit = benefit;
      if (period !== undefined) body.period = period;
      if (description !== undefined) body.description = description;
      if (company_contribution_amount !== undefined) body.company_contribution_amount = company_contribution_amount;
      if (company_contribution_percent !== undefined) body.company_contribution_percent = company_contribution_percent;
      if (company_period_amount !== undefined) body.company_period_amount = company_period_amount;
      if (employee_contribution_amount !== undefined) body.employee_contribution_amount = employee_contribution_amount;
      if (employee_contribution_percent !== undefined) body.employee_contribution_percent = employee_contribution_percent;
      if (employee_period_amount !== undefined) body.employee_period_amount = employee_period_amount;
      if (effective_start !== undefined) body.effective_start = effective_start;
      if (effective_end !== undefined) body.effective_end = effective_end;
      if (hsa_contribution_limit !== undefined) body.hsa_contribution_limit = hsa_contribution_limit;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPatch(api, `/benefits/${benefit_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "delete_benefit",
    "Delete a benefit.",
    {
      benefit_id: z.string().describe("The Check benefit ID."),
    },
    async ({ benefit_id }) => {
      const result = await checkApiDelete(api, `/benefits/${benefit_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // ---------------------------------------------------------------------------
  // Post-Tax Deductions
  // ---------------------------------------------------------------------------

  tool(
    server,
    filter,
    toolsetName,
    "list_post_tax_deductions",
    "List post-tax deductions, optionally filtered by company or employee.",
    {
      company: z.string().optional().describe('Filter to post-tax deductions belonging to this Check company ID (e.g. "com_xxxxx").'),
      employee: z.string().optional().describe('Filter to post-tax deductions for this Check employee ID (e.g. "emp_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, employee, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (employee !== undefined) params.employee = employee;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/post_tax_deductions", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_post_tax_deduction",
    "Get details for a specific post-tax deduction.",
    {
      deduction_id: z.string().describe("The Check post-tax deduction ID."),
    },
    async ({ deduction_id }) => {
      const result = await checkApiGet(api, `/post_tax_deductions/${deduction_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_post_tax_deduction",
    "Create a new post-tax deduction.",
    {
      employee: z.string().describe("The Check employee ID."),
      type: z.string().describe('Deduction type (e.g. "miscellaneous", "child_support", "miscellaneous_garnishment").'),
      description: z.string().describe("Deduction description."),
      effective_start: z.string().describe("Effective start date (YYYY-MM-DD)."),
      effective_end: z.string().optional().describe("Effective end date (YYYY-MM-DD)."),
      miscellaneous: z.record(z.unknown()).optional().describe("Miscellaneous deduction configuration."),
      child_support: z.record(z.unknown()).optional().describe("Child support deduction configuration."),
      miscellaneous_garnishment: z.record(z.unknown()).optional().describe("Miscellaneous garnishment configuration."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
      managed: z.boolean().optional().describe("Whether the deduction is managed."),
    },
    async ({ employee, type, description, effective_start, effective_end, miscellaneous, child_support, miscellaneous_garnishment, metadata, managed }) => {
      const body: Record<string, unknown> = { employee, type, description, effective_start };
      if (effective_end !== undefined) body.effective_end = effective_end;
      if (miscellaneous !== undefined) body.miscellaneous = miscellaneous;
      if (child_support !== undefined) body.child_support = child_support;
      if (miscellaneous_garnishment !== undefined) body.miscellaneous_garnishment = miscellaneous_garnishment;
      if (metadata !== undefined) body.metadata = metadata;
      if (managed !== undefined) body.managed = managed;
      const result = await checkApiPost(api, "/post_tax_deductions", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_post_tax_deduction",
    "Update an existing post-tax deduction.",
    {
      deduction_id: z.string().describe("The Check post-tax deduction ID."),
      description: z.string().optional().describe("Deduction description."),
      effective_start: z.string().optional().describe("Effective start date (YYYY-MM-DD)."),
      effective_end: z.string().optional().describe("Effective end date (YYYY-MM-DD)."),
      miscellaneous: z.record(z.unknown()).optional().describe("Miscellaneous deduction configuration."),
      child_support: z.record(z.unknown()).optional().describe("Child support deduction configuration."),
      miscellaneous_garnishment: z.record(z.unknown()).optional().describe("Miscellaneous garnishment configuration."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
      managed: z.boolean().optional().describe("Whether the deduction is managed."),
    },
    async ({ deduction_id, description, effective_start, effective_end, miscellaneous, child_support, miscellaneous_garnishment, metadata, managed }) => {
      const body: Record<string, unknown> = {};
      if (description !== undefined) body.description = description;
      if (effective_start !== undefined) body.effective_start = effective_start;
      if (effective_end !== undefined) body.effective_end = effective_end;
      if (miscellaneous !== undefined) body.miscellaneous = miscellaneous;
      if (child_support !== undefined) body.child_support = child_support;
      if (miscellaneous_garnishment !== undefined) body.miscellaneous_garnishment = miscellaneous_garnishment;
      if (metadata !== undefined) body.metadata = metadata;
      if (managed !== undefined) body.managed = managed;
      const result = await checkApiPatch(api, `/post_tax_deductions/${deduction_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "delete_post_tax_deduction",
    "Delete a post-tax deduction.",
    {
      deduction_id: z.string().describe("The Check post-tax deduction ID."),
    },
    async ({ deduction_id }) => {
      const result = await checkApiDelete(api, `/post_tax_deductions/${deduction_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // ---------------------------------------------------------------------------
  // Company Benefits
  // ---------------------------------------------------------------------------

  tool(
    server,
    filter,
    toolsetName,
    "list_company_benefits",
    "List company benefits, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to company benefits belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/company_benefits", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_company_benefit",
    "Get details for a specific company benefit.",
    {
      company_benefit_id: z.string().describe("The Check company benefit ID."),
    },
    async ({ company_benefit_id }) => {
      const result = await checkApiGet(api, `/company_benefits/${company_benefit_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_company_benefit",
    "Create a new company benefit.",
    {
      company: z.string().describe("The Check company ID."),
      benefit: z.string().describe("Benefit type identifier."),
      description: z.string().describe("Company benefit description."),
      period: z.string().optional().describe('Deduction period (e.g. "per_paycheck").'),
      company_contribution_amount: z.string().optional().describe("Company contribution amount per period."),
      company_contribution_percent: z.number().optional().describe("Company contribution percentage."),
      company_period_amount: z.string().optional().describe("Company contribution period cap."),
      employee_contribution_amount: z.string().optional().describe("Employee contribution amount per period."),
      employee_contribution_percent: z.number().optional().describe("Employee contribution percentage."),
      employee_period_amount: z.string().optional().describe("Employee contribution period cap."),
      effective_start: z.string().optional().describe("Effective start date (YYYY-MM-DD)."),
      effective_end: z.string().optional().describe("Effective end date (YYYY-MM-DD)."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ company, benefit, description, period, company_contribution_amount, company_contribution_percent, company_period_amount, employee_contribution_amount, employee_contribution_percent, employee_period_amount, effective_start, effective_end, metadata }) => {
      const body: Record<string, unknown> = { company, benefit, description };
      if (period !== undefined) body.period = period;
      if (company_contribution_amount !== undefined) body.company_contribution_amount = company_contribution_amount;
      if (company_contribution_percent !== undefined) body.company_contribution_percent = company_contribution_percent;
      if (company_period_amount !== undefined) body.company_period_amount = company_period_amount;
      if (employee_contribution_amount !== undefined) body.employee_contribution_amount = employee_contribution_amount;
      if (employee_contribution_percent !== undefined) body.employee_contribution_percent = employee_contribution_percent;
      if (employee_period_amount !== undefined) body.employee_period_amount = employee_period_amount;
      if (effective_start !== undefined) body.effective_start = effective_start;
      if (effective_end !== undefined) body.effective_end = effective_end;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPost(api, "/company_benefits", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_company_benefit",
    "Update an existing company benefit.",
    {
      company_benefit_id: z.string().describe("The Check company benefit ID."),
      description: z.string().optional().describe("Company benefit description."),
      period: z.string().optional().describe('Deduction period (e.g. "per_paycheck").'),
      company_contribution_amount: z.string().optional().describe("Company contribution amount per period."),
      company_contribution_percent: z.number().optional().describe("Company contribution percentage."),
      company_period_amount: z.string().optional().describe("Company contribution period cap."),
      employee_contribution_amount: z.string().optional().describe("Employee contribution amount per period."),
      employee_contribution_percent: z.number().optional().describe("Employee contribution percentage."),
      employee_period_amount: z.string().optional().describe("Employee contribution period cap."),
      effective_start: z.string().optional().describe("Effective start date (YYYY-MM-DD)."),
      effective_end: z.string().optional().describe("Effective end date (YYYY-MM-DD)."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ company_benefit_id, description, period, company_contribution_amount, company_contribution_percent, company_period_amount, employee_contribution_amount, employee_contribution_percent, employee_period_amount, effective_start, effective_end, metadata }) => {
      const body: Record<string, unknown> = {};
      if (description !== undefined) body.description = description;
      if (period !== undefined) body.period = period;
      if (company_contribution_amount !== undefined) body.company_contribution_amount = company_contribution_amount;
      if (company_contribution_percent !== undefined) body.company_contribution_percent = company_contribution_percent;
      if (company_period_amount !== undefined) body.company_period_amount = company_period_amount;
      if (employee_contribution_amount !== undefined) body.employee_contribution_amount = employee_contribution_amount;
      if (employee_contribution_percent !== undefined) body.employee_contribution_percent = employee_contribution_percent;
      if (employee_period_amount !== undefined) body.employee_period_amount = employee_period_amount;
      if (effective_start !== undefined) body.effective_start = effective_start;
      if (effective_end !== undefined) body.effective_end = effective_end;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPatch(api, `/company_benefits/${company_benefit_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "delete_company_benefit",
    "Delete a company benefit.",
    {
      company_benefit_id: z.string().describe("The Check company benefit ID."),
    },
    async ({ company_benefit_id }) => {
      const result = await checkApiDelete(api, `/company_benefits/${company_benefit_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // ---------------------------------------------------------------------------
  // Earning Rates
  // ---------------------------------------------------------------------------

  tool(
    server,
    filter,
    toolsetName,
    "list_earning_rates",
    "List earning rates, optionally filtered by company or employee.",
    {
      company: z.string().optional().describe('Filter to earning rates belonging to this Check company ID (e.g. "com_xxxxx").'),
      employee: z.string().optional().describe('Filter to earning rates for this Check employee ID (e.g. "emp_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, employee, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (employee !== undefined) params.employee = employee;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/earning_rates", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_earning_rate",
    "Get details for a specific earning rate.",
    {
      earning_rate_id: z.string().describe("The Check earning rate ID."),
    },
    async ({ earning_rate_id }) => {
      const result = await checkApiGet(api, `/earning_rates/${earning_rate_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_earning_rate",
    "Create a new earning rate.",
    {
      employee: z.string().describe("The Check employee ID."),
      amount: z.string().describe("Earning rate amount."),
      period: z.string().describe('Earning rate period (e.g. "hour", "year").'),
      name: z.string().optional().describe("Human-readable name for the earning rate."),
      workweek_hours: z.number().optional().describe("Number of hours in a standard workweek."),
    },
    async ({ employee, amount, period, name, workweek_hours }) => {
      const body: Record<string, unknown> = { employee, amount, period };
      if (name !== undefined) body.name = name;
      if (workweek_hours !== undefined) body.workweek_hours = workweek_hours;
      const result = await checkApiPost(api, "/earning_rates", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_earning_rate",
    "Update an existing earning rate.",
    {
      earning_rate_id: z.string().describe("The Check earning rate ID."),
      name: z.string().optional().describe("Human-readable name for the earning rate."),
      active: z.boolean().optional().describe("Whether the earning rate is active."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ earning_rate_id, name, active, metadata }) => {
      const body: Record<string, unknown> = {};
      if (name !== undefined) body.name = name;
      if (active !== undefined) body.active = active;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPatch(api, `/earning_rates/${earning_rate_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // ---------------------------------------------------------------------------
  // Earning Codes
  // ---------------------------------------------------------------------------

  tool(
    server,
    filter,
    toolsetName,
    "list_earning_codes",
    "List earning codes, optionally filtered by company.",
    {
      company: z.string().optional().describe('Filter to earning codes belonging to this Check company ID (e.g. "com_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/earning_codes", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_earning_code",
    "Get details for a specific earning code.",
    {
      earning_code_id: z.string().describe("The Check earning code ID."),
    },
    async ({ earning_code_id }) => {
      const result = await checkApiGet(api, `/earning_codes/${earning_code_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_earning_code",
    "Create a new earning code.",
    {
      company: z.string().describe("The Check company ID."),
      name: z.string().describe("Earning code name."),
      type: z.string().describe("Earning code type."),
      active: z.boolean().optional().describe("Whether the earning code is active."),
      calculation_overrides: z.record(z.unknown()).optional().describe("Calculation override configuration."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ company, name, type, active, calculation_overrides, metadata }) => {
      const body: Record<string, unknown> = { company, name, type };
      if (active !== undefined) body.active = active;
      if (calculation_overrides !== undefined) body.calculation_overrides = calculation_overrides;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPost(api, "/earning_codes", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "update_earning_code",
    "Update an existing earning code.",
    {
      earning_code_id: z.string().describe("The Check earning code ID."),
      active: z.boolean().optional().describe("Whether the earning code is active."),
      metadata: z.string().optional().describe("Additional JSON metadata string."),
    },
    async ({ earning_code_id, active, metadata }) => {
      const body: Record<string, unknown> = {};
      if (active !== undefined) body.active = active;
      if (metadata !== undefined) body.metadata = metadata;
      const result = await checkApiPatch(api, `/earning_codes/${earning_code_id}`, body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // ---------------------------------------------------------------------------
  // Net Pay Splits
  // ---------------------------------------------------------------------------

  tool(
    server,
    filter,
    toolsetName,
    "list_net_pay_splits",
    "List net pay splits, optionally filtered by company or employee.",
    {
      company: z.string().optional().describe('Filter to net pay splits belonging to this Check company ID (e.g. "com_xxxxx").'),
      employee: z.string().optional().describe('Filter to net pay splits for this Check employee ID (e.g. "emp_xxxxx").'),
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ company, employee, limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (company !== undefined) params.company = company;
      if (employee !== undefined) params.employee = employee;
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/net_pay_splits", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_net_pay_split",
    "Get details for a specific net pay split.",
    {
      net_pay_split_id: z.string().describe("The Check net pay split ID."),
    },
    async ({ net_pay_split_id }) => {
      const result = await checkApiGet(api, `/net_pay_splits/${net_pay_split_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_net_pay_split",
    "Create a new net pay split configuration.",
    {
      splits: z.array(z.record(z.unknown())).describe("Array of split objects defining how net pay is distributed."),
      employee: z.string().optional().describe("The Check employee ID."),
      contractor: z.string().optional().describe("The Check contractor ID."),
      is_default: z.boolean().optional().describe("Whether this is the default net pay split."),
    },
    async ({ splits, employee, contractor, is_default }) => {
      const body: Record<string, unknown> = { splits };
      if (employee !== undefined) body.employee = employee;
      if (contractor !== undefined) body.contractor = contractor;
      if (is_default !== undefined) body.is_default = is_default;
      const result = await checkApiPost(api, "/net_pay_splits", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
