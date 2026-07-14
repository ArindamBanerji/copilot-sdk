import { test as base, expect, type Page } from "@playwright/test";

const BACKEND_PORTS = {
  trading: 8010,
  purchasing: 8020,
  dataops: 8030,
} as const;

type CopilotProject = keyof typeof BACKEND_PORTS;

function isCopilotProject(name: string): name is CopilotProject {
  return name in BACKEND_PORTS;
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
      const healthUrl = `http://127.0.0.1:${port}/health`;
      let responseText = "";

      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const response = await request.get(healthUrl, { timeout: 5_000 });
          responseText = await response.text().catch(() => "");
          if (!response.ok()) {
            throw new Error(`HTTP ${response.status()} ${response.statusText()} ${responseText}`.trim());
          }
          break;
        } catch (error) {
          if (attempt < 2) {
            await new Promise(r => setTimeout(r, 2000));
            continue;
          }
          const message = error instanceof Error ? error.message : String(error);
          throw new Error(
            `${projectName} backend is not healthy at ${healthUrl}. Start the live stack before running E2E tests. ${message}`,
          );
        }
      }

      const base = `http://127.0.0.1:${port}`;
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
