/**
 * Live Tab Discovery v3
 *
 * Key design decisions:
 * - Uses getByText(exact:true).first() per Codex Playbook §7.3:
 *   "Tabs are plain buttons; use text click patterns such as
 *    page.getByText('Alert Triage').click()"
 * - getByRole("tab") returns 0 for all copilots because they render
 *   plain <button> elements without ARIA tab roles.
 * - Each tab click is wrapped in a 8s race guard so a false match
 *   (e.g. "Order" inside panel content) cannot hang the entire test.
 * - Non-serial: each copilot is independent.
 *
 * Deploy to: copilot-sdk/e2e/diagnostics/
 * Run:       npx playwright test --config=diagnostics/playwright.config.ts
 *              diagnostics/collect_live_tabs_v3.spec.ts --reporter=list
 * Output:    claude_projects/diagnostics/live_tab_inventory.json
 */

import { test } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COPILOTS = [
  { name: "Trading",    fePort: 5174, bePort: 8010, tabs: ["Dashboard", "Log Trade", "Analysis", "Performance", "Journal"] },
  { name: "Purchasing", fePort: 5175, bePort: 8020, tabs: ["Dashboard", "Order", "Analysis", "Inventory", "Performance"] },
  { name: "DataOps",    fePort: 5176, bePort: 8030, tabs: ["Dashboard", "Triage", "Insight", "Evidence", "Curve"] },
  { name: "S2P",        fePort: 5177, bePort: 8002, tabs: ["Dashboard", "Exception Triage", "Insight", "Evidence", "Suppliers", "Performance"] },
  { name: "SOC",        fePort: 5173, bePort: 8001, tabs: ["SOC Analytics", "Runtime Evolution", "Alert Triage", "Compounding", "Executive Narrative", "S2P Preview"] },
];

const S2P_PREVIEW_KEYWORDS = ["Financial Impact", "Working Capital", "Disruption", "Compliance", "Process Fusion", "Novelty", "Trend"];

interface TabInfo { label: string; found: boolean; panels: string[] }
interface Result {
  copilot: string; fePort: number; bePort: number;
  feUp: boolean; beUp: boolean;
  tabs: TabInfo[]; missingTabs: string[];
  s2pPreviewPanels: string[]; totalPanels: number;
  timestamp: string;
}

const allResults: Result[] = [];

/** Race a promise against a timeout. Returns null on timeout. */
async function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T | null> {
  let timer: ReturnType<typeof setTimeout>;
  const timeout = new Promise<null>((resolve) => {
    timer = setTimeout(() => resolve(null), ms);
  });
  try {
    return await Promise.race([promise, timeout]);
  } finally {
    clearTimeout(timer!);
  }
}

/** Click a tab and capture panels within a hard time budget. */
async function discoverTab(
  page: import("@playwright/test").Page,
  tabLabel: string,
): Promise<TabInfo> {
  const info: TabInfo = { label: tabLabel, found: false, panels: [] };

  const work = async (): Promise<void> => {
    // Per §7.3: tabs are plain buttons, use getByText
    const btn = page.getByText(tabLabel, { exact: true }).first();
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) return;

    info.found = true;
    await btn.click({ timeout: 3000 });
    await page.waitForTimeout(1500);

    // Capture section headings
    const sections = await page.locator("section, [class*='Panel']").all();
    const seen = new Set<string>();
    for (const sec of sections.slice(0, 20)) {
      const h = await sec
        .locator("h2, h3, h4, p[class*='uppercase']")
        .first()
        .textContent()
        .catch(() => null);
      if (h && h.trim().length > 1 && h.trim().length < 60 && !seen.has(h.trim())) {
        seen.add(h.trim());
        info.panels.push(h.trim());
      }
    }
  };

  // Hard 8s guard: if click navigates away or triggers a modal, bail
  await withTimeout(work(), 8000);
  return info;
}

test.describe("Live Tab Discovery v3", () => {
  for (const cop of COPILOTS) {
    test(`${cop.name}`, async ({ page, request }) => {
      const result: Result = {
        copilot: cop.name, fePort: cop.fePort, bePort: cop.bePort,
        feUp: false, beUp: false,
        tabs: [], missingTabs: [], s2pPreviewPanels: [], totalPanels: 0,
        timestamp: new Date().toISOString(),
      };

      // Backend health
      for (const hp of ["/health", "/api/health"]) {
        try {
          const r = await request.get(`http://127.0.0.1:${cop.bePort}${hp}`, { timeout: 3000 });
          if (r.ok()) { result.beUp = true; break; }
        } catch { /* next */ }
      }

      // Frontend
      try {
        await page.goto(`http://127.0.0.1:${cop.fePort}`, { timeout: 10000, waitUntil: "domcontentloaded" });
        result.feUp = true;
      } catch {
        allResults.push(result);
        return;
      }

      await page.waitForTimeout(2000);

      // Discover each tab
      for (const tabLabel of cop.tabs) {
        const info = await discoverTab(page, tabLabel);

        // S2P Preview: check for S2P panels
        if (tabLabel === "S2P Preview" && info.found) {
          const body = await page.locator("body").textContent().catch(() => "");
          for (const kw of S2P_PREVIEW_KEYWORDS) {
            if (body.toLowerCase().includes(kw.toLowerCase())) {
              result.s2pPreviewPanels.push(kw);
            }
          }
        }

        result.totalPanels += info.panels.length;
        result.tabs.push(info);
      }

      result.missingTabs = cop.tabs.filter(
        (t) => !result.tabs.some((ti) => ti.label === t && ti.found),
      );
      allResults.push(result);
    });
  }

  test.afterAll(() => {
    // Output: 3 levels up from e2e/diagnostics/ → claude_projects/diagnostics/
    const diagDir = path.resolve(__dirname, "..", "..", "..", "diagnostics");
    if (!fs.existsSync(diagDir)) fs.mkdirSync(diagDir, { recursive: true });
    const outPath = path.join(diagDir, "live_tab_inventory.json");
    fs.writeFileSync(outPath, JSON.stringify(allResults, null, 2));

    console.log("\n" + "=".repeat(60));
    console.log("  LIVE TAB DISCOVERY v3");
    console.log("=".repeat(60));
    for (const r of allResults) {
      const found = r.tabs.filter((t) => t.found).length;
      const total = r.tabs.length;
      const be = r.beUp ? "UP  " : "DOWN";
      const fe = r.feUp ? "UP  " : "DOWN";
      console.log(
        `  ${r.copilot.padEnd(12)} BE:${be} FE:${fe} ` +
        `Tabs:${found}/${total} Panels:${r.totalPanels} ` +
        `Missing:${r.missingTabs.length}`,
      );
      if (r.missingTabs.length) console.log(`    Missing: ${r.missingTabs.join(", ")}`);
      if (r.s2pPreviewPanels.length) console.log(`    S2P Preview: ${r.s2pPreviewPanels.join(", ")}`);
    }
    console.log(`\n  Output: ${outPath}\n`);
  });
});
