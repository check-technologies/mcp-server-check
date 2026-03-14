/** Document tools for the Check API. */

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
  // --- Company Tax Documents ---

  tool(
    server,
    filter,
    toolsetName,
    "list_company_tax_documents",
    "List company tax documents.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/company_tax_documents", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_company_tax_document",
    "Get a specific company tax document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/company_tax_documents/${document_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "download_company_tax_document",
    "Download a company tax document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/company_tax_documents/${document_id}/download`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Company Authorization Documents ---

  tool(
    server,
    filter,
    toolsetName,
    "list_company_authorization_documents",
    "List company authorization documents.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/company_authorization_documents", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_company_authorization_document",
    "Get a specific company authorization document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/company_authorization_documents/${document_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "download_company_authorization_document",
    "Download a company authorization document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/company_authorization_documents/${document_id}/download`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Employee Tax Documents ---

  tool(
    server,
    filter,
    toolsetName,
    "list_employee_tax_documents",
    "List employee tax documents.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/employee_tax_documents", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_employee_tax_document",
    "Get a specific employee tax document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/employee_tax_documents/${document_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "download_employee_tax_document",
    "Download an employee tax document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/employee_tax_documents/${document_id}/download`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Contractor Tax Documents ---

  tool(
    server,
    filter,
    toolsetName,
    "list_contractor_tax_documents",
    "List contractor tax documents.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/contractor_tax_documents", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_contractor_tax_document",
    "Get a specific contractor tax document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/contractor_tax_documents/${document_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "download_contractor_tax_document",
    "Download a contractor tax document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/contractor_tax_documents/${document_id}/download`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Setup Documents ---

  tool(
    server,
    filter,
    toolsetName,
    "list_setup_documents",
    "List setup documents.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/setup_documents", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_setup_document",
    "Get a specific setup document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/setup_documents/${document_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "download_setup_document",
    "Download a setup document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/setup_documents/${document_id}/download`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  // --- Company Provided Documents ---

  tool(
    server,
    filter,
    toolsetName,
    "list_company_provided_documents",
    "List company-provided documents.",
    {
      limit: z.number().optional().describe("Maximum number of results to return."),
      cursor: z.string().optional().describe("Pagination cursor."),
    },
    async ({ limit, cursor }) => {
      const params: Record<string, unknown> = {};
      if (limit !== undefined) params.limit = limit;
      if (cursor !== undefined) params.cursor = cursor;
      const result = await checkApiList(api, "/company_provided_documents", params);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "get_company_provided_document",
    "Get a specific company-provided document.",
    {
      document_id: z.string().describe("The document ID."),
    },
    async ({ document_id }) => {
      const result = await checkApiGet(api, `/company_provided_documents/${document_id}`);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "create_company_provided_document",
    "Create a company-provided document.",
    {
      company: z.string().describe("The Check company ID."),
      document_type: z.string().optional().describe('Type of document — one of "940", "941", "943", "944", "945", "cp_575", "147_c", "signatory_photo_id", "voided_check", "bank_statement", "ss4", "bank_account_owner_id", "bank_letter", "profit_and_loss", "cash_flow_statement", "balance_sheet", "articles_of_incorporation", "articles_of_incorporation_signatory_amendment", "state_registration".'),
    },
    async ({ company, document_type }) => {
      const body: Record<string, unknown> = { company };
      if (document_type !== undefined) body.document_type = document_type;
      const result = await checkApiPost(api, "/company_provided_documents", body);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );

  tool(
    server,
    filter,
    toolsetName,
    "upload_company_provided_document_file",
    "Upload a file for a company-provided document.",
    {
      document_id: z.string().describe("The document ID."),
      data: z.record(z.unknown()).optional().describe("Upload metadata."),
    },
    async ({ document_id, data }) => {
      const result = await checkApiPost(api, `/company_provided_documents/${document_id}/upload`, data);
      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    },
  );
}
