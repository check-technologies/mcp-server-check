/** Tests for HTTP helpers — mock native fetch. */

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  checkApiGet,
  checkApiPost,
  checkApiPatch,
  checkApiPut,
  checkApiDelete,
  checkApiList,
  extractCursor,
  formatListResponse,
  type CheckApiOptions,
} from "../src/helpers.js";

const api: CheckApiOptions = {
  apiKey: "test-key",
  baseUrl: "https://sandbox.checkhq.com",
};

function mockFetch(response: { status: number; json?: unknown; text?: string }) {
  const fn = vi.fn(async () => ({
    ok: response.status >= 200 && response.status < 300,
    status: response.status,
    json: async () => response.json,
    text: async () => response.text ?? JSON.stringify(response.json),
  }));
  vi.stubGlobal("fetch", fn);
  return fn;
}

beforeEach(() => {
  vi.restoreAllMocks();
});

// --- extractCursor ---

describe("extractCursor", () => {
  it("extracts cursor from URL", () => {
    expect(extractCursor("https://sandbox.checkhq.com/items?cursor=c2")).toBe("c2");
  });

  it("returns null for null/undefined", () => {
    expect(extractCursor(null)).toBeNull();
    expect(extractCursor(undefined)).toBeNull();
  });

  it("returns null for URL without cursor", () => {
    expect(extractCursor("https://sandbox.checkhq.com/items")).toBeNull();
  });
});

// --- formatListResponse ---

describe("formatListResponse", () => {
  it("normalizes paginated response", () => {
    const result = formatListResponse({
      results: [{ id: "i_1" }],
      next: "https://sandbox.checkhq.com/items?cursor=c2",
      previous: null,
    });
    expect(result.results).toEqual([{ id: "i_1" }]);
    expect(result.next_cursor).toBe("c2");
    expect(result.previous_cursor).toBeNull();
  });
});

// --- checkApiGet ---

describe("checkApiGet", () => {
  it("makes GET request and returns JSON", async () => {
    const fetchMock = mockFetch({ status: 200, json: { id: "t_1" } });
    const result = await checkApiGet(api, "/test");
    expect(result).toEqual({ id: "t_1" });
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("https://sandbox.checkhq.com/test");
    expect(init.method).toBe("GET");
  });

  it("sends query params", async () => {
    const fetchMock = mockFetch({ status: 200, json: { id: "t_1" } });
    await checkApiGet(api, "/test", { limit: 5 });
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("limit=5");
  });
});

// --- checkApiPost ---

describe("checkApiPost", () => {
  it("makes POST request with body", async () => {
    const fetchMock = mockFetch({ status: 201, json: { id: "t_new" } });
    const result = await checkApiPost(api, "/test", { name: "foo" });
    expect(result).toEqual({ id: "t_new" });
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ name: "foo" }));
  });
});

// --- checkApiPatch ---

describe("checkApiPatch", () => {
  it("makes PATCH request", async () => {
    mockFetch({ status: 200, json: { id: "t_1", name: "updated" } });
    const result = await checkApiPatch(api, "/test/t_1", { name: "updated" });
    expect((result as Record<string, unknown>).name).toBe("updated");
  });
});

// --- checkApiPut ---

describe("checkApiPut", () => {
  it("makes PUT request", async () => {
    mockFetch({ status: 200, json: { id: "t_1", name: "replaced" } });
    const result = await checkApiPut(api, "/test/t_1", { name: "replaced" });
    expect((result as Record<string, unknown>).name).toBe("replaced");
  });
});

// --- checkApiDelete ---

describe("checkApiDelete", () => {
  it("returns success for 204", async () => {
    mockFetch({ status: 204 });
    const result = await checkApiDelete(api, "/test/t_1");
    expect(result).toEqual({ success: true });
  });

  it("returns JSON for non-204", async () => {
    mockFetch({ status: 200, json: { deleted: true } });
    const result = await checkApiDelete(api, "/test/t_1");
    expect(result).toEqual({ deleted: true });
  });
});

// --- checkApiList ---

describe("checkApiList", () => {
  it("normalizes list response", async () => {
    mockFetch({
      status: 200,
      json: {
        next: "https://sandbox.checkhq.com/items?cursor=c2",
        previous: null,
        results: [{ id: "i_1" }],
      },
    });
    const result = await checkApiList(api, "/items");
    expect(result.results).toEqual([{ id: "i_1" }]);
    expect(result.next_cursor).toBe("c2");
    expect(result.previous_cursor).toBeNull();
  });
});

// --- Error handling ---

describe("error handling", () => {
  it("returns error dict for HTTP error with JSON body", async () => {
    mockFetch({ status: 422, json: { detail: "Validation error" } });
    const result = await checkApiGet(api, "/bad");
    expect(result.error).toBe(true);
    expect(result.status_code).toBe(422);
    expect(result.detail).toEqual({ detail: "Validation error" });
  });

  it("returns error dict for HTTP error with text body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error("not json");
        },
        text: async () => "Internal Server Error",
      })),
    );
    const result = await checkApiGet(api, "/bad");
    expect(result.error).toBe(true);
    expect(result.status_code).toBe(500);
  });

  it("returns error dict for network error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("Network failure");
      }),
    );
    const result = await checkApiGet(api, "/bad");
    expect(result.error).toBe(true);
    expect(result.detail).toContain("Network failure");
  });
});
