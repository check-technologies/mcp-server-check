/** Toolset-based tool filtering for the Check MCP server. */

import type { Env } from "./env.js";

export const TOOLSETS: ReadonlySet<string> = new Set([
  "bank_accounts",
  "companies",
  "compensation",
  "components",
  "contractor_payments",
  "contractors",
  "documents",
  "employees",
  "external_payrolls",
  "forms",
  "payments",
  "payroll_items",
  "payrolls",
  "platform",
  "tax",
  "webhooks",
  "workplaces",
]);

const WRITE_PREFIXES = [
  "create_",
  "update_",
  "delete_",
  "bulk_update_",
  "bulk_delete_",
];

const WRITE_KEYWORDS = [
  "approve_",
  "reopen_",
  "onboard_",
  "submit_",
  "sign_and_submit_",
  "authorize_",
  "simulate_",
  "retry_",
  "refund_",
  "cancel_",
  "start_implementation",
  "cancel_implementation",
  "request_embedded_setup",
  "ping_",
  "refresh_",
  "toggle_",
  "sync_",
  "upload_",
  "request_tax_",
];

export function isWriteTool(name: string): boolean {
  return (
    WRITE_PREFIXES.some((p) => name.startsWith(p)) ||
    WRITE_KEYWORDS.some((k) => name.startsWith(k))
  );
}

function parseCommaSet(value: string | undefined | null): ReadonlySet<string> | null {
  if (!value) return null;
  const items = new Set(
    value
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
  );
  return items.size > 0 ? items : null;
}

function parseBool(value: string | undefined | null): boolean {
  return ["1", "true", "yes"].includes((value ?? "").toLowerCase());
}

export class ToolFilter {
  readonly toolsets: ReadonlySet<string> | null;
  readonly tools: ReadonlySet<string> | null;
  readonly excludeTools: ReadonlySet<string>;
  readonly readOnly: boolean;

  constructor(opts?: {
    toolsets?: ReadonlySet<string> | null;
    tools?: ReadonlySet<string> | null;
    excludeTools?: ReadonlySet<string>;
    readOnly?: boolean;
  }) {
    let toolsets = opts?.toolsets ?? null;
    if (toolsets !== null) {
      const valid = new Set([...toolsets].filter((t) => TOOLSETS.has(t)));
      toolsets = valid;
    }
    this.toolsets = toolsets;
    this.tools = opts?.tools ?? null;
    this.excludeTools = opts?.excludeTools ?? new Set();
    this.readOnly = opts?.readOnly ?? false;
  }

  isToolAllowed(toolName: string, toolsetName: string): boolean {
    if (this.excludeTools.has(toolName)) return false;
    if (this.readOnly && isWriteTool(toolName)) return false;
    if (this.tools !== null) return this.tools.has(toolName);
    if (this.toolsets !== null) return this.toolsets.has(toolsetName);
    return true;
  }

  /** True when no filtering is configured (default state). */
  isDefault(): boolean {
    return (
      this.toolsets === null &&
      this.tools === null &&
      this.excludeTools.size === 0 &&
      !this.readOnly
    );
  }

  static fromEnv(env: Env): ToolFilter {
    return new ToolFilter({
      toolsets: parseCommaSet(env.CHECK_TOOLSETS),
      tools: parseCommaSet(env.CHECK_TOOLS),
      excludeTools: parseCommaSet(env.CHECK_EXCLUDE_TOOLS) ?? new Set(),
      readOnly: parseBool(env.CHECK_READ_ONLY),
    });
  }

  static fromHeaders(headers: Headers): ToolFilter {
    return new ToolFilter({
      toolsets: parseCommaSet(headers.get("x-mcp-toolsets")),
      tools: parseCommaSet(headers.get("x-mcp-tools")),
      excludeTools: parseCommaSet(headers.get("x-mcp-exclude-tools")) ?? new Set(),
      readOnly: parseBool(headers.get("x-mcp-readonly")),
    });
  }
}
