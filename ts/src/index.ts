/** Cloudflare Worker entrypoint — Streamable HTTP MCP transport. */

import { McpAgent } from "agents/mcp";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { Env } from "./env.js";
import { buildApiOptions } from "./helpers.js";
import { ToolFilter } from "./tool-filter.js";
import { registerAll } from "./tools/index.js";

export class CheckMcpAgent extends McpAgent<Env> {
  server = new McpServer({
    name: "Check Payroll API",
    version: "0.1.0",
  });

  async init() {
    const staticFilter = ToolFilter.fromEnv(this.env);
    // TODO: when agents package supports per-request headers, merge header filter
    const api = buildApiOptions(this.env.CHECK_API_KEY, this.env.CHECK_API_BASE_URL);
    registerAll(this.server, api, staticFilter);
  }
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/sse" || url.pathname === "/sse/message") {
      // @ts-expect-error — McpAgent.fetch typing
      return CheckMcpAgent.fetch(request, env, ctx);
    }

    if (url.pathname === "/mcp") {
      // @ts-expect-error — McpAgent.fetch typing
      return CheckMcpAgent.fetch(request, env, ctx);
    }

    return new Response("Check Payroll MCP Server", { status: 200 });
  },
};
