import { test as base, expect, type APIRequestContext, type Page } from "@playwright/test";

export const PORTS = {
  soc: { frontend: "http://127.0.0.1:5173", backend: "http://127.0.0.1:8001" },
  trading: { frontend: "http://127.0.0.1:5174", backend: "http://127.0.0.1:8010" },
  purchasing: { frontend: "http://127.0.0.1:5175", backend: "http://127.0.0.1:8020" },
  dataops: { frontend: "http://127.0.0.1:5176", backend: "http://127.0.0.1:8030" },
  s2p: { frontend: "http://127.0.0.1:5177", backend: "http://127.0.0.1:8002" },
} as const;

export type CopilotName = keyof typeof PORTS;
export type JsonRecord = Record<string, unknown>;

// Compatibility exports for the older staged-trust draft in this directory.
export const SOC = PORTS.soc;

async function getJson(url: string, timeoutMs: number): Promise<JsonRecord> {
  const response = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return (await response.json()) as JsonRecord;
}

export async function checkHealth(backend: string): Promise<boolean> {
  try {
    const response = await fetch(`${backend}/health`, { signal: AbortSignal.timeout(5_000) });
    return response.ok;
  } catch {
    return false;
  }
}

async function hasPreseedData(backend: string): Promise<boolean> {
  try {
    const diagnostics = await getJson(`${backend}/api/self/diagnostics`, 5_000);
    const iks = diagnostics.iks ?? diagnostics.iks_score ?? 0;
    return typeof iks === "number" && iks > 0;
  } catch {
    return false;
  }
}

async function isDemoReady(): Promise<boolean> {
  const health = await Promise.all(Object.values(PORTS).map(({ backend }) => checkHealth(backend)));
  if (health.some((healthy) => !healthy)) return false;

  const preseeded = await Promise.all(
    Object.values(PORTS).map(({ backend }) => hasPreseedData(backend)),
  );
  return preseeded.every(Boolean);
}

export async function gotoCopilot(page: Page, copilot: CopilotName): Promise<void> {
  await page.goto(PORTS[copilot].frontend, { waitUntil: "domcontentloaded" });
  await page.locator("main").waitFor({ state: "attached", timeout: 25_000 });
  await expect(page.locator("main")).not.toBeEmpty({ timeout: 25_000 });
}

export async function gotoTab(page: Page, copilot: CopilotName, tabName: string): Promise<void> {
  await gotoCopilot(page, copilot);
  const pattern = new RegExp(tabName, "i");
  const button = page.getByRole("button", { name: pattern });
  const tab = page.getByRole("tab", { name: pattern });
  if (await button.count()) {
    await button.first().click();
  } else {
    await expect(tab).toHaveCount(1);
    await tab.click();
  }
  await expect(page.locator("main")).not.toBeEmpty({ timeout: 25_000 });
}

export async function apiGet(backend: string, path: string): Promise<JsonRecord> {
  return getJson(`${backend}${path}`, 10_000);
}

export async function apiPost(
  backend: string,
  path: string,
  body: JsonRecord,
): Promise<JsonRecord> {
  const response = await fetch(`${backend}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`);
  }
  return (await response.json()) as JsonRecord;
}

export const test = base.extend<{}, { demoReady: boolean }>({
  demoReady: [
    async ({}, use) => {
      await use(await isDemoReady());
    },
    { scope: "worker" },
  ],
});

export { expect };

export async function isBackendHealthy(request: APIRequestContext, config: { backend: string }): Promise<boolean> {
  try {
    return (await request.get(`${config.backend}/health`, { timeout: 5_000 })).ok();
  } catch {
    return false;
  }
}

export async function openCopilotTab(
  page: Page,
  config: { frontend: string },
  tabName: string | RegExp,
): Promise<void> {
  await page.goto(config.frontend, { waitUntil: "domcontentloaded" });
  await page.locator("main").waitFor({ state: "attached", timeout: 25_000 });
  const button = page.getByRole("button", { name: tabName });
  if (await button.count()) {
    await button.first().click();
  } else {
    await page.getByRole("tab", { name: tabName }).click();
  }
}

export async function expectAnyText(page: Page, patterns: RegExp[], timeout = 10_000): Promise<void> {
  const content = page.locator("main");
  for (const pattern of patterns) {
    if (await content.getByText(pattern).count()) {
      await expect(content.getByText(pattern).first()).toBeVisible({ timeout });
      return;
    }
  }
  throw new Error(`None of the expected content patterns matched: ${patterns.join(", ")}`);
}
