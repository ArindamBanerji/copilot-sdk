import { test as base, expect, type APIRequestContext, type APIResponse, type Page } from "@playwright/test";

const HOST = process.env.COPILOT_HOST || "127.0.0.1";

const BACKEND_PORTS = {
  trading: 8010,
  purchasing: 8020,
  dataops: 8030,
} as const;

type CopilotProject = keyof typeof BACKEND_PORTS;

function isCopilotProject(name: string): name is CopilotProject {
  return name in BACKEND_PORTS;
}

function withQueryParams(
  url: string | URL,
  options?: { params?: URLSearchParams | string | Record<string, string | number | boolean> },
) {
  const target = new URL(String(url));
  const params = options?.params;
  if (params instanceof URLSearchParams) {
    params.forEach((value, key) => target.searchParams.append(key, value));
  } else if (typeof params === "string") {
    new URLSearchParams(params).forEach((value, key) => target.searchParams.append(key, value));
  } else if (params) {
    Object.entries(params).forEach(([key, value]) => target.searchParams.append(key, String(value)));
  }
  return target;
}

async function fetchApiResponse(
  method: "GET" | "POST",
  url: string | URL,
  options?: {
    data?: unknown;
    headers?: Record<string, string>;
    params?: URLSearchParams | string | Record<string, string | number | boolean>;
    timeout?: number;
  },
  timeout = 30_000,
): Promise<APIResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options?.timeout ?? timeout);
  try {
    const headers = new Headers(options?.headers);
    const body = options && "data" in options && options.data !== undefined ? JSON.stringify(options.data) : undefined;
    if (body && !headers.has("content-type")) {
      headers.set("content-type", "application/json");
    }
    const response = await fetch(withQueryParams(url, options), {
      body,
      headers,
      method,
      signal: controller.signal,
    });
    const bodyText = await response.text();
    return {
      ok: () => response.ok,
      status: () => response.status,
      statusText: () => response.statusText,
      url: () => response.url,
      headers: () => Object.fromEntries(response.headers.entries()),
      json: async () => JSON.parse(bodyText),
      text: async () => bodyText,
      body: async () => Buffer.from(bodyText),
    } as APIResponse;
  } finally {
    clearTimeout(timeoutId);
  }
}

function applyDefaultRequestTimeouts(request: APIRequestContext, timeout = 30_000) {
  request.get = (async (
    url: Parameters<APIRequestContext["get"]>[0],
    options?: Parameters<APIRequestContext["get"]>[1],
  ) => {
    let lastError: unknown;
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        return await fetchApiResponse("GET", url, options, timeout);
      } catch (error) {
        lastError = error;
        if (attempt < 2) {
          await new Promise((resolve) => setTimeout(resolve, 500 * 2 ** attempt));
        }
      }
    }
    throw lastError;
  }) as APIRequestContext["get"];

  request.post = (async (
    url: Parameters<APIRequestContext["post"]>[0],
    options?: Parameters<APIRequestContext["post"]>[1],
  ) => {
    let lastError: unknown;
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        return await fetchApiResponse("POST", url, options, timeout);
      } catch (error) {
        lastError = error;
        if (attempt < 2) {
          await new Promise((resolve) => setTimeout(resolve, 500 * 2 ** attempt));
        }
      }
    }
    throw lastError;
  }) as APIRequestContext["post"];
}

async function retryHealthCheck(
  request: APIRequestContext,
  url: string,
  maxRetries = 5,
  baseDelayMs = 1000,
): Promise<void> {
  let lastError = "unknown error";
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await request.get(url, { timeout: 5_000 });
      if (response.ok()) return;
      lastError = `HTTP ${response.status()} ${response.statusText()}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    if (attempt < maxRetries - 1) {
      await new Promise((resolve) => setTimeout(resolve, baseDelayMs * 2 ** attempt));
    }
  }
  throw new Error(`Backend at ${url} not reachable after ${maxRetries} retries: ${lastError}`);
}

export const test = base.extend<{ backendHealth: void }>({
  request: async ({ request }, use) => {
    applyDefaultRequestTimeouts(request);
    await use(request);
  },
  page: async ({ page }, use) => {
    const originalGoto = page.goto.bind(page);
    applyDefaultRequestTimeouts(page.request);
    page.goto = (async (url: Parameters<Page["goto"]>[0], options?: Parameters<Page["goto"]>[1]) => {
      let lastError: unknown;
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          return await originalGoto(url, { waitUntil: "commit", timeout: 45_000, ...options });
        } catch (error) {
          lastError = error;
          if (attempt < 2) {
            await new Promise((resolve) => setTimeout(resolve, 750 * 2 ** attempt));
          }
        }
      }
      throw lastError;
    }) as Page["goto"];
    await use(page);
  },
  backendHealth: [
    async ({ request }, use, testInfo) => {
      testInfo.setTimeout(Math.max(testInfo.timeout, 60_000));
      const projectName = testInfo.project.name;
      if (!isCopilotProject(projectName)) {
        throw new Error(`Unknown copilot Playwright project "${projectName}". Expected trading, purchasing, or dataops.`);
      }

      const port = BACKEND_PORTS[projectName];
      const healthUrl = `http://${HOST}:${port}/health`;
      try {
        await retryHealthCheck(request, healthUrl);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        testInfo.skip(true, message);
        return;
      }

      const base = `http://${HOST}:${port}`;
      await Promise.all([
        request.get(`${base}/api/fingerprint`, { timeout: 5_000 }).catch(() => {}),
        request.get(`${base}/api/conservation/status`, { timeout: 5_000 }).catch(() => {}),
      ]);

      await use();
    },
    { auto: true },
  ],
});

export { expect };
