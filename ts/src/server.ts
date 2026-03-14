/** Factory: create a configured McpServer with filtered tools registered. */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { Env } from "./env.js";
import { buildApiOptions } from "./helpers.js";
import { ToolFilter } from "./tool-filter.js";
import { registerAll } from "./tools/index.js";

export function createServer(env: Env, filter: ToolFilter): McpServer {
  const server = new McpServer({
    name: "Check Payroll API",
    version: "0.1.0",
  });

  const api = buildApiOptions(env.CHECK_API_KEY, env.CHECK_API_BASE_URL);
  registerAll(server, api, filter);

  return server;
}
