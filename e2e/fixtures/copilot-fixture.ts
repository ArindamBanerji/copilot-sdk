import { test as base, expect, type APIRequestContext, type Page } from "@playwright/test";

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
  page: async ({ page }, use) => {
    const originalGoto = page.goto.bind(page);
    page.goto = ((url: Parameters<Page["goto"]>[0], options?: Parameters<Page["goto"]>[1]) =>
      originalGoto(url, { waitUntil: "domcontentloaded", ...options })) as Page["goto"];
    await use(page);
  },
  backendHealth: [
    async ({ request }, use, testInfo) => {
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
