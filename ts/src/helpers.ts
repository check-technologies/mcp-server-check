/** Shared helpers for the Check MCP server. */

export interface CheckApiOptions {
  apiKey: string;
  baseUrl: string;
}

const DEFAULT_BASE_URL = "https://sandbox.checkhq.com";

export function buildApiOptions(apiKey: string, baseUrl?: string): CheckApiOptions {
  return {
    apiKey,
    baseUrl: (baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, ""),
  };
}

// ---------------------------------------------------------------------------
// Pagination helpers
// ---------------------------------------------------------------------------

export function extractCursor(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.searchParams.get("cursor") ?? null;
  } catch {
    return null;
  }
}

export function formatListResponse(data: Record<string, unknown>): Record<string, unknown> {
  return {
    results: data.results ?? [],
    next_cursor: extractCursor(data.next as string | undefined),
    previous_cursor: extractCursor(data.previous as string | undefined),
  };
}

// ---------------------------------------------------------------------------
// Core request function — never throws
// ---------------------------------------------------------------------------

export async function checkApiRequest(
  api: CheckApiOptions,
  method: string,
  path: string,
  options?: {
    params?: Record<string, unknown>;
    data?: unknown;
  },
): Promise<Record<string, unknown>> {
  const url = new URL(`${api.baseUrl}${path}`);
  if (options?.params) {
    for (const [k, v] of Object.entries(options.params)) {
      if (v !== undefined && v !== null) {
        url.searchParams.set(k, String(v));
      }
    }
  }

  const headers: Record<string, string> = {
    Authorization: `Bearer ${api.apiKey}`,
    Accept: "application/json",
  };

  const init: RequestInit = { method, headers };

  if (options?.data !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.data);
  }

  try {
    const response = await fetch(url.toString(), init);

    if (!response.ok) {
      let errorBody: unknown;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      return {
        error: true,
        status_code: response.status,
        detail: errorBody,
      };
    }

    if (response.status === 204) {
      return { success: true };
    }

    return (await response.json()) as Record<string, unknown>;
  } catch (e: unknown) {
    return { error: true, detail: String(e) };
  }
}

// ---------------------------------------------------------------------------
// Convenience wrappers
// ---------------------------------------------------------------------------

export function checkApiGet(
  api: CheckApiOptions,
  path: string,
  params?: Record<string, unknown>,
) {
  return checkApiRequest(api, "GET", path, { params });
}

export function checkApiPost(
  api: CheckApiOptions,
  path: string,
  data?: unknown,
) {
  return checkApiRequest(api, "POST", path, { data });
}

export function checkApiPatch(
  api: CheckApiOptions,
  path: string,
  data: unknown,
) {
  return checkApiRequest(api, "PATCH", path, { data });
}

export function checkApiPut(
  api: CheckApiOptions,
  path: string,
  data: unknown,
) {
  return checkApiRequest(api, "PUT", path, { data });
}

export function checkApiDelete(
  api: CheckApiOptions,
  path: string,
  params?: Record<string, unknown>,
) {
  return checkApiRequest(api, "DELETE", path, { params });
}

export async function checkApiList(
  api: CheckApiOptions,
  path: string,
  params?: Record<string, unknown>,
) {
  const data = await checkApiGet(api, path, params);
  if ("error" in data) return data;
  return formatListResponse(data);
}
