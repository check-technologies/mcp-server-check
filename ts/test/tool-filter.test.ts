/** Tests for ToolFilter — port of test_tool_filter.py. */

import { describe, it, expect } from "vitest";
import { TOOLSETS, ToolFilter, isWriteTool } from "../src/tool-filter.js";

// --- isWriteTool ---

describe("isWriteTool", () => {
  it.each([
    "create_company",
    "update_employee",
    "delete_payroll",
    "bulk_update_payroll_items",
    "bulk_delete_payroll_items",
    "approve_payroll",
    "reopen_payroll",
    "onboard_company",
    "submit_employee_form",
    "sign_and_submit_employee_form",
    "authorize_integration_partner",
    "simulate_start_processing",
    "retry_payment",
    "refund_payment",
    "cancel_payment",
    "start_implementation",
    "cancel_implementation",
    "request_embedded_setup",
    "ping_webhook_config",
    "refresh_accounting_accounts",
    "toggle_accounting_mappings",
    "sync_accounting",
    "upload_company_provided_document_file",
    "request_tax_filing_refile",
  ])("detects %s as write tool", (name) => {
    expect(isWriteTool(name)).toBe(true);
  });

  it.each([
    "list_companies",
    "get_company",
    "get_employee",
    "list_payrolls",
    "preview_payroll",
    "download_company_tax_document",
    "validate_address",
    "list_webhook_configs",
    "reveal_employee_ssn",
    "get_enrollment_profile",
  ])("does not flag %s as write tool", (name) => {
    expect(isWriteTool(name)).toBe(false);
  });
});

// --- ToolFilter.fromEnv ---

describe("ToolFilter.fromEnv", () => {
  it("returns defaults with no env vars", () => {
    const tf = ToolFilter.fromEnv({
      CHECK_API_KEY: "key",
    });
    expect(tf.toolsets).toBeNull();
    expect(tf.tools).toBeNull();
    expect(tf.excludeTools.size).toBe(0);
    expect(tf.readOnly).toBe(false);
  });

  it("parses toolsets", () => {
    const tf = ToolFilter.fromEnv({
      CHECK_API_KEY: "key",
      CHECK_TOOLSETS: "companies, employees",
    });
    expect(tf.toolsets).toEqual(new Set(["companies", "employees"]));
  });

  it("parses tools", () => {
    const tf = ToolFilter.fromEnv({
      CHECK_API_KEY: "key",
      CHECK_TOOLS: "list_companies,get_company",
    });
    expect(tf.tools).toEqual(new Set(["list_companies", "get_company"]));
  });

  it("parses exclude_tools", () => {
    const tf = ToolFilter.fromEnv({
      CHECK_API_KEY: "key",
      CHECK_EXCLUDE_TOOLS: "create_company,delete_company",
    });
    expect(tf.excludeTools).toEqual(new Set(["create_company", "delete_company"]));
  });

  it("parses read_only true", () => {
    for (const val of ["1", "true", "yes", "True", "YES"]) {
      const tf = ToolFilter.fromEnv({ CHECK_API_KEY: "key", CHECK_READ_ONLY: val });
      expect(tf.readOnly).toBe(true);
    }
  });

  it("parses read_only false", () => {
    for (const val of ["0", "false", "no", ""]) {
      const tf = ToolFilter.fromEnv({ CHECK_API_KEY: "key", CHECK_READ_ONLY: val });
      expect(tf.readOnly).toBe(false);
    }
  });

  it("treats empty strings as null", () => {
    const tf = ToolFilter.fromEnv({
      CHECK_API_KEY: "key",
      CHECK_TOOLSETS: "",
      CHECK_TOOLS: "",
    });
    expect(tf.toolsets).toBeNull();
    expect(tf.tools).toBeNull();
  });
});

// --- ToolFilter.fromHeaders ---

describe("ToolFilter.fromHeaders", () => {
  it("parses all headers", () => {
    const headers = new Headers({
      "x-mcp-toolsets": "companies,employees",
      "x-mcp-tools": "list_companies",
      "x-mcp-exclude-tools": "create_company",
      "x-mcp-readonly": "true",
    });
    const tf = ToolFilter.fromHeaders(headers);
    expect(tf.toolsets).toEqual(new Set(["companies", "employees"]));
    expect(tf.tools).toEqual(new Set(["list_companies"]));
    expect(tf.excludeTools).toEqual(new Set(["create_company"]));
    expect(tf.readOnly).toBe(true);
  });

  it("returns defaults for empty headers", () => {
    const tf = ToolFilter.fromHeaders(new Headers());
    expect(tf.isDefault()).toBe(true);
  });
});

// --- isToolAllowed precedence ---

describe("isToolAllowed", () => {
  it("allows everything with no filter", () => {
    const tf = new ToolFilter();
    expect(tf.isToolAllowed("create_company", "companies")).toBe(true);
  });

  it("exclude wins over everything", () => {
    const tf = new ToolFilter({
      tools: new Set(["create_company"]),
      excludeTools: new Set(["create_company"]),
    });
    expect(tf.isToolAllowed("create_company", "companies")).toBe(false);
  });

  it("readOnly blocks write tools", () => {
    const tf = new ToolFilter({ readOnly: true });
    expect(tf.isToolAllowed("create_company", "companies")).toBe(false);
    expect(tf.isToolAllowed("list_companies", "companies")).toBe(true);
  });

  it("readOnly takes precedence over tools allowlist", () => {
    const tf = new ToolFilter({
      tools: new Set(["create_company"]),
      readOnly: true,
    });
    expect(tf.isToolAllowed("create_company", "companies")).toBe(false);
  });

  it("tools allowlist", () => {
    const tf = new ToolFilter({
      tools: new Set(["list_companies", "get_company"]),
    });
    expect(tf.isToolAllowed("list_companies", "companies")).toBe(true);
    expect(tf.isToolAllowed("get_company", "companies")).toBe(true);
    expect(tf.isToolAllowed("create_company", "companies")).toBe(false);
    expect(tf.isToolAllowed("list_employees", "employees")).toBe(false);
  });

  it("tools overrides toolsets", () => {
    const tf = new ToolFilter({
      toolsets: new Set(["employees"]),
      tools: new Set(["list_companies"]),
    });
    expect(tf.isToolAllowed("list_companies", "companies")).toBe(true);
    expect(tf.isToolAllowed("list_employees", "employees")).toBe(false);
  });

  it("toolsets filter", () => {
    const tf = new ToolFilter({ toolsets: new Set(["companies"]) });
    expect(tf.isToolAllowed("list_companies", "companies")).toBe(true);
    expect(tf.isToolAllowed("create_company", "companies")).toBe(true);
    expect(tf.isToolAllowed("list_employees", "employees")).toBe(false);
  });

  it("exclude with toolsets", () => {
    const tf = new ToolFilter({
      toolsets: new Set(["companies"]),
      excludeTools: new Set(["create_company"]),
    });
    expect(tf.isToolAllowed("list_companies", "companies")).toBe(true);
    expect(tf.isToolAllowed("create_company", "companies")).toBe(false);
  });

  it("readOnly with toolsets", () => {
    const tf = new ToolFilter({
      toolsets: new Set(["companies"]),
      readOnly: true,
    });
    expect(tf.isToolAllowed("list_companies", "companies")).toBe(true);
    expect(tf.isToolAllowed("create_company", "companies")).toBe(false);
    expect(tf.isToolAllowed("list_employees", "employees")).toBe(false);
  });
});

// --- Invalid toolset handling ---

describe("invalid toolsets", () => {
  it("strips unknown toolsets", () => {
    const tf = new ToolFilter({ toolsets: new Set(["companies", "not_a_real_one"]) });
    expect(tf.toolsets).toEqual(new Set(["companies"]));
  });

  it("all unknown yields empty set", () => {
    const tf = new ToolFilter({ toolsets: new Set(["bogus"]) });
    expect(tf.toolsets!.size).toBe(0);
    expect(tf.isToolAllowed("list_companies", "companies")).toBe(false);
  });
});

// --- TOOLSETS constant ---

describe("TOOLSETS", () => {
  it("has 17 toolsets", () => {
    expect(TOOLSETS.size).toBe(17);
  });

  it("contains expected toolsets", () => {
    const expected = new Set([
      "bank_accounts", "companies", "compensation", "components",
      "contractor_payments", "contractors", "documents", "employees",
      "external_payrolls", "forms", "payments", "payroll_items",
      "payrolls", "platform", "tax", "webhooks", "workplaces",
    ]);
    expect(TOOLSETS).toEqual(expected);
  });
});
