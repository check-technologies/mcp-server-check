/** Smoke test: verify all tools register correctly and count matches expectations. */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { buildApiOptions } from "../../src/helpers.js";
import { ToolFilter } from "../../src/tool-filter.js";
import { registerAll } from "../../src/tools/index.js";

const api = buildApiOptions("test-key");

describe("tool registration", () => {
  let server: McpServer;
  let toolNames: string[];

  beforeEach(() => {
    server = new McpServer({ name: "test", version: "0.0.1" });
    toolNames = [];

    // Spy on server.tool to capture registered tool names
    const originalTool = server.tool.bind(server);
    server.tool = vi.fn((...args: unknown[]) => {
      const name = args[0] as string;
      toolNames.push(name);
      return (originalTool as Function)(...args);
    }) as typeof server.tool;
  });

  it("registers all 263 tools with no filter", () => {
    const filter = new ToolFilter();
    registerAll(server, api, filter);
    expect(toolNames.length).toBe(263);
  });

  it("registers no component tools in read-only mode", () => {
    const filter = new ToolFilter({ readOnly: true });
    registerAll(server, api, filter);
    const componentTools = toolNames.filter((n) => n.includes("_component"));
    expect(componentTools.length).toBe(0);
  });

  it("filters by toolset", () => {
    const filter = new ToolFilter({ toolsets: new Set(["webhooks"]) });
    registerAll(server, api, filter);
    expect(toolNames.length).toBe(7);
    expect(toolNames).toContain("list_webhook_configs");
    expect(toolNames).toContain("retry_webhook_events");
  });

  it("all tool names are unique", () => {
    const filter = new ToolFilter();
    registerAll(server, api, filter);
    const unique = new Set(toolNames);
    expect(unique.size).toBe(toolNames.length);
  });
});
