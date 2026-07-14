import { expect, type APIRequestContext, type Page } from "@playwright/test";

export type DemoCopilotConfig = {
  name: string;
  frontend: string;
  backend: string;
};

export type DemoCopilotKey = "soc" | "s2p" | "dataops" | "trading" | "purchasing";

export type DemoCopilot = DemoCopilotConfig | DemoCopilotKey;

export const SOC: DemoCopilotConfig = {
  name: "SOC",
  frontend: "http://127.0.0.1:5173",
  backend: "http://127.0.0.1:8001",
};

export const DATAOPS: DemoCopilotConfig = {
  name: "DataOps",
  frontend: "http://127.0.0.1:5176",
  backend: "http://127.0.0.1:8030",
};

export const S2P: DemoCopilotConfig = {
  name: "S2P",
  frontend: "http://127.0.0.1:5177",
  backend: "http://127.0.0.1:8002",
};

export const TRADING: DemoCopilotConfig = {
  name: "Trading",
  frontend: "http://127.0.0.1:5174",
  backend: "http://127.0.0.1:8010",
};

export const PURCHASING: DemoCopilotConfig = {
  name: "Purchasing",
  frontend: "http://127.0.0.1:5175",
  backend: "http://127.0.0.1:8020",
};

const COPILOTS: Record<DemoCopilotKey, DemoCopilotConfig> = {
  soc: SOC,
  s2p: S2P,
  dataops: DATAOPS,
  trading: TRADING,
  purchasing: PURCHASING,
};

function resolveCopilot(copilot: DemoCopilot): DemoCopilotConfig {
  return typeof copilot === "string" ? COPILOTS[copilot] : copilot;
}

export async function isBackendHealthy(request: APIRequestContext, copilot: DemoCopilot): Promise<boolean> {
  const resolved = resolveCopilot(copilot);
  for (const path of ["/health", "/api/health"]) {
    const response = await request.get(`${resolved.backend}${path}`, { timeout: 5_000 }).catch(() => null);
    if (response?.ok()) return true;
  }
  return false;
}

export async function checkBackendHealth(request: APIRequestContext, copilot: DemoCopilot): Promise<boolean> {
  return isBackendHealthy(request, copilot);
}

export function copilotUrl(copilot: DemoCopilot): string {
  return resolveCopilot(copilot).frontend;
}

export async function openCopilotTab(page: Page, copilot: DemoCopilot, tabName: string | RegExp): Promise<void> {
  const resolved = resolveCopilot(copilot);
  await page.goto(resolved.frontend, { waitUntil: "domcontentloaded" });

  const tab = page.getByRole("tab", { name: tabName });
  if (await tab.count()) {
    await tab.first().click();
  } else {
    const button = page.getByRole("button", { name: tabName });
    if (await button.count()) {
      await button.first().click();
    } else {
      await page.getByText(tabName).first().click();
    }
  }

  await expect(page.locator("main")).not.toBeEmpty({ timeout: 15_000 });
}

export async function navigateToTab(page: Page, tabName: string | RegExp): Promise<void> {
  const tab = page.getByRole("tab", { name: tabName });
  if (await tab.count()) {
    await tab.first().click();
  } else {
    const button = page.getByRole("button", { name: tabName });
    if (await button.count()) {
      await button.first().click();
    } else {
      await page.getByText(tabName).first().click();
    }
  }

  await expect(page.locator("main")).not.toBeEmpty({ timeout: 15_000 });
}

export async function checkPreseedActive(request: APIRequestContext, copilot: DemoCopilot): Promise<boolean> {
  const resolved = resolveCopilot(copilot);
  if (!(await isBackendHealthy(request, resolved))) return false;

  for (const path of [
    "/api/trajectory",
    "/api/soc/learning-state",
    "/api/soc/profile",
    "/api/soc/analytics",
    "/api/learning-state",
    "/api/s2p/preview/queue",
  ]) {
    const response = await request.get(`${resolved.backend}${path}`, { timeout: 5_000 }).catch(() => null);
    if (!response?.ok()) continue;
    const data = (await response.json().catch(() => ({}))) as Record<string, unknown>;
    const values = [
      data.iks,
      data.current_iks,
      data.currentIks,
      data.iks_v2,
      data.institutional_knowledge_score,
      typeof data.iks === "object" && data.iks ? (data.iks as Record<string, unknown>).score : undefined,
      typeof data.iks === "object" && data.iks ? (data.iks as Record<string, unknown>).value : undefined,
    ];
    if (values.some((value) => Number(value) > 0)) return true;
    if (Array.isArray(data.points) && data.points.some((point) => Number((point as Record<string, unknown>).iks) > 0)) {
      return true;
    }
    if (Number(data.total) > 0 || Number(data.showing) > 0) return true;
    if (Array.isArray(data.exceptions) && data.exceptions.length > 0) return true;
    if (Array.isArray(data.invoices) && data.invoices.length > 0) return true;
  }

  return false;
}

export async function expectAnyText(
  page: Page,
  patterns: Array<RegExp | string>,
  timeout = 10_000,
): Promise<void> {
  const deadline = Date.now() + timeout;
  let lastError = "";

  while (Date.now() < deadline) {
    for (const pattern of patterns) {
      const locator = page.getByText(pattern).first();
      try {
        await expect(locator).toBeVisible({ timeout: 300 });
        return;
      } catch (error) {
        lastError = error instanceof Error ? error.message : String(error);
      }
    }
    await page.waitForTimeout(200);
  }

  throw new Error(
    `Expected one of these texts within ${timeout}ms: ${patterns.map(String).join(", ")}${
      lastError ? `\nLast error: ${lastError}` : ""
    }`,
  );
}
