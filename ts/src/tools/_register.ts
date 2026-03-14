/** Shared tool registration helper. */

import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { ToolFilter } from "../tool-filter.js";

/**
 * Register a single tool on the server if the filter allows it.
 * Wraps `server.tool()` to avoid TypeScript overload-resolution issues
 * when using spread args.
 */
export function tool(
  server: McpServer,
  filter: ToolFilter,
  toolsetName: string,
  name: string,
  description: string,
  schema: Record<string, z.ZodTypeAny>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  handler: (args: any, extra: any) => any,
) {
  if (filter.isToolAllowed(name, toolsetName)) {
    server.tool(name, description, schema, handler);
  }
}
