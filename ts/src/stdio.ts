/** Node.js stdio entrypoint for local dev with Claude Desktop. */

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import type { Env } from "./env.js";
import { createServer } from "./server.js";
import { ToolFilter } from "./tool-filter.js";

async function main() {
  const apiKey = process.env.CHECK_API_KEY;
  if (!apiKey) {
    console.error("Error: CHECK_API_KEY environment variable is required");
    process.exit(1);
  }

  const env: Env = {
    CHECK_API_KEY: apiKey,
    CHECK_API_BASE_URL: process.env.CHECK_API_BASE_URL,
    CHECK_TOOLSETS: process.env.CHECK_TOOLSETS,
    CHECK_TOOLS: process.env.CHECK_TOOLS,
    CHECK_EXCLUDE_TOOLS: process.env.CHECK_EXCLUDE_TOOLS,
    CHECK_READ_ONLY: process.env.CHECK_READ_ONLY,
  };

  const filter = ToolFilter.fromEnv(env);

  if (filter.readOnly) {
    console.error("Running in read-only mode (CHECK_READ_ONLY is set)");
  }
  if (filter.toolsets) {
    console.error(`Active toolsets: ${[...filter.toolsets].sort().join(", ")}`);
  }

  const server = createServer(env, filter);
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
