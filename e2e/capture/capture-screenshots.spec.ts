import { mkdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { retryHealthCheck } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell, waitForScreenReady } from "../helpers/ui";
import { waitForTriageQueue } from "../s2p/helpers";

const HOST = process.env.COPILOT_HOST || "127.0.0.1";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SCREENSHOT_ROOT = path.resolve(__dirname, "../../screenshots");

const COPILOTS = {
  soc: { frontend: 5173, backend: 8001 },
  trading: { frontend: 5174, backend: 8010 },
  purchasing: { frontend: 5175, backend: 8020 },
  dataops: { frontend: 5176, backend: 8030 },
  s2p: { frontend: 5177, backend: 8002 },
} as const;

type Copilot = keyof typeof COPILOTS;
type Provenance = "illustrative_preseed" | "measured";
type ManifestEntry = {
  file: string;
  copilot: Copilot;
  tab: string;
  timestamp: string;
  provenance: Provenance;
};
type SkippedEntry = { copilot: Copilot; tab: string; reason: string };
type Manifest = {
  generated_at: string;
  viewport: { width: number; height: number };
  screenshots: ManifestEntry[];
  skipped: SkippedEntry[];
};

function frontendUrl(copilot: Copilot): string {
  return `http://${HOST}:${COPILOTS[copilot].frontend}`;
}

function filenameTimestamp(timestamp: string): string {
  return timestamp.replace(/[-:.]/g, "");
}

function errorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  return message.split("\n", 1)[0].replace(/\u001b\[[0-9;]*m/g, "");
}

async function runningReason(request: APIRequestContext, copilot: Copilot): Promise<string | null> {
  const { backend, frontend } = COPILOTS[copilot];
  try {
    await retryHealthCheck(request, `http://${HOST}:${backend}/health`, 2, 250);
  } catch (error) {
    return `backend :${backend} unavailable: ${errorMessage(error)}`;
  }
  try {
    const response = await request.get(`http://${HOST}:${frontend}`, { timeout: 5_000 });
    if (!response.ok()) return `frontend :${frontend} returned HTTP ${response.status()}`;
  } catch (error) {
    return `frontend :${frontend} unavailable: ${errorMessage(error)}`;
  }
  return null;
}

async function capture(
  page: Page,
  manifest: Manifest,
  copilot: Copilot,
  tab: string,
  provenance: Provenance = "illustrative_preseed",
): Promise<void> {
  const timestamp = new Date().toISOString();
  const relativeFile = path.posix.join(copilot, `${tab}-${filenameTimestamp(timestamp)}.png`);
  const output = path.join(SCREENSHOT_ROOT, ...relativeFile.split("/"));
  mkdirSync(path.dirname(output), { recursive: true });
  await page.screenshot({ path: output, fullPage: true });
  expect(statSync(output).size, `${relativeFile} must be non-empty`).toBeGreaterThan(0);
  manifest.screenshots.push({ file: relativeFile, copilot, tab, timestamp, provenance });
}

async function attemptSurface(
  manifest: Manifest,
  copilot: Copilot,
  tab: string,
  action: () => Promise<void>,
): Promise<void> {
  try {
    await action();
  } catch (error) {
    manifest.skipped.push({ copilot, tab, reason: errorMessage(error) });
  }
}

async function openSdkDashboard(
  page: Page,
  copilot: "trading" | "purchasing" | "dataops",
): Promise<void> {
  await page.goto(frontendUrl(copilot), { waitUntil: "domcontentloaded" });
  await waitForScreenReady(page, 60_000);
  await waitForAppShell(page, 60_000);
  const heading = copilot === "dataops" ? /DataOps Copilot/i : /Dashboard/i;
  await expect(page.getByRole("heading", { name: heading }).first()).toBeVisible();
}

test("capture live outreach dashboard surfaces", async ({ page, request }) => {
  const manifest: Manifest = {
    generated_at: new Date().toISOString(),
    viewport: { width: 1440, height: 900 },
    screenshots: [],
    skipped: [],
  };

  const availability = new Map<Copilot, string | null>();
  for (const copilot of Object.keys(COPILOTS) as Copilot[]) {
    availability.set(copilot, await runningReason(request, copilot));
  }

  const socUnavailable = availability.get("soc");
  if (socUnavailable) {
    manifest.skipped.push({ copilot: "soc", tab: "*", reason: socUnavailable });
  } else {
    await attemptSurface(manifest, "soc", "runtime-evolution", async () => {
      await page.goto(frontendUrl("soc"), { waitUntil: "domcontentloaded" });
      await page.locator("main").waitFor({ state: "attached", timeout: 60_000 });
      await clickTab(page, /Runtime Evolution/i);
      await expect(page.getByText(/Institutional Knowledge Score/i).first()).toBeVisible({ timeout: 60_000 });
      await capture(page, manifest, "soc", "runtime-evolution");
    });

    const evolutionSections = [
      { key: "a", tab: "this-decision", tag: /\[A\]/ },
      { key: "b", tab: "situational", tag: /\[B\]/ },
      { key: "c", tab: "adaptation", tag: /\[C\]/ },
      { key: "d", tab: "system-health", tag: /\[D\]/ },
    ] as const;
    for (const section of evolutionSections) {
      await attemptSurface(manifest, "soc", `runtime-evolution-${section.tab}`, async () => {
        const button = page.locator("button").filter({ hasText: section.tag }).first();
        await button.click({ timeout: 20_000 });
        const panel = page.locator(`#section-${section.key}`);
        await panel.scrollIntoViewIfNeeded();
        await expect(panel.locator("h2, h3, h4").first()).toBeVisible({ timeout: 30_000 });
        if (section.key === "d") {
          await expect(panel).not.toContainText(/Loading IKS|Loading conservation status/i, { timeout: 60_000 });
        }
        await capture(page, manifest, "soc", `runtime-evolution-${section.tab}`);
      });
    }

    await attemptSurface(manifest, "soc", "soc-analytics", async () => {
      await clickTab(page, /SOC Analytics/i);
      await expect(page.locator("main")).not.toBeEmpty({ timeout: 30_000 });
      await capture(page, manifest, "soc", "soc-analytics");
    });
  }

  const s2pUnavailable = availability.get("s2p");
  if (s2pUnavailable) {
    manifest.skipped.push({ copilot: "s2p", tab: "*", reason: s2pUnavailable });
  } else {
    await attemptSurface(manifest, "s2p", "dashboard", async () => {
      await page.goto(frontendUrl("s2p"), { waitUntil: "domcontentloaded" });
      await waitForScreenReady(page, 60_000);
      await waitForAppShell(page, 60_000);
      await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
      await capture(page, manifest, "s2p", "dashboard");
    });

    await attemptSurface(manifest, "s2p", "rl-decision-loop", async () => {
      await clickTab(page, "Exception Triage");
      await waitForScreenReady(page, 90_000);
      await waitForTriageQueue(page);
      await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
      await capture(page, manifest, "s2p", "rl-decision-loop");
    });

    await attemptSurface(manifest, "s2p", "centroid-explorer", async () => {
      await clickTab(page, "Insight");
      await waitForScreenReady(page, 60_000);
      await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
      await expect(page.getByText(/Centroid explorer/i).first()).toBeVisible({ timeout: 60_000 });
      await capture(page, manifest, "s2p", "centroid-explorer");
    });

    await attemptSurface(manifest, "s2p", "learning-trajectory", async () => {
      await clickTab(page, "Performance");
      await waitForScreenReady(page, 60_000);
      await expect(page.getByRole("heading", { name: "Performance" })).toBeVisible();
      await expect(page.getByText(/Learning trajectory/i).first()).toBeVisible({ timeout: 60_000 });
      await capture(page, manifest, "s2p", "learning-trajectory");
    });
  }

  for (const copilot of ["trading", "purchasing", "dataops"] as const) {
    const unavailable = availability.get(copilot);
    if (unavailable) {
      manifest.skipped.push({ copilot, tab: "dashboard", reason: unavailable });
      continue;
    }
    await attemptSurface(manifest, copilot, "dashboard", async () => {
      await openSdkDashboard(page, copilot);
      await capture(page, manifest, copilot, "dashboard");
    });
  }

  mkdirSync(SCREENSHOT_ROOT, { recursive: true });
  writeFileSync(path.join(SCREENSHOT_ROOT, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
});
