/**
 * Live Tab Discovery v4
 *
 * Design principles:
 * 1. getByText(exact:true).first() — apps use plain buttons, not ARIA tabs (§7.3)
 * 2. force:true on click — bypasses "element is intercepted" errors from overlays/animations
 * 3. discoverTab NEVER throws — always returns TabInfo, found:false on any error
 * 4. No complex race/timeout wrappers — just try/catch at every level
 *
 * Deploy to: copilot-sdk/e2e/diagnostics/
 * Run:       npx playwright test --config=diagnostics/playwright.config.ts
 *              diagnostics/collect_live_tabs_v4.spec.ts --reporter=list
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

interface TabInfo { label: string; found: boolean; clicked: boolean; panels: string[]; error: string | null }
interface Result {
  copilot: string; fePort: number; bePort: number;
  feUp: boolean; beUp: boolean;
  tabs: TabInfo[]; missingTabs: string[];
  s2pPreviewPanels: string[]; totalPanels: number;
  timestamp: string;
}

const allResults: Result[] = [];

/**
 * Discover one tab. NEVER throws — returns TabInfo with found:false on any error.
 */
async function discoverTab(
  page: import("@playwright/test").Page,
  tabLabel: string,
): Promise<TabInfo> {
  const info: TabInfo = { label: tabLabel, found: false, clicked: false, panels: [], error: null };

  try {
    const btn = page.getByText(tabLabel, { exact: true }).first();
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) {
      info.error = "not visible";
      return info;
    }
    info.found = true;

    // force:true bypasses "click intercepted by overlay" errors
    await btn.click({ timeout: 5000, force: true });
    info.clicked = true;
    await page.waitForTimeout(1500);

    // Capture section headings — also in try/catch
    try {
      const sections = await page.locator("section, [class*='Panel']").all();
      const seen = new Set<string>();
      for (const sec of sections.slice(0, 20)) {
        const h = await sec
          .locator("h2, h3, h4, p[class*='uppercase']")
          .first()
          .textContent({ timeout: 1000 })
          .catch(() => null);
        if (h && h.trim().length > 1 && h.trim().length < 60 && !seen.has(h.trim())) {
          seen.add(h.trim());
          info.panels.push(h.trim());
        }
      }
    } catch {
      info.error = "panel capture failed";
    }
  } catch (e) {
    info.error = String(e).slice(0, 100);
  }

  return info;
}

test.describe("Live Tab Discovery v4", () => {
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

      // Discover each tab — discoverTab never throws
      for (const tabLabel of cop.tabs) {
        const info = await discoverTab(page, tabLabel);

        // S2P Preview: check for known S2P panels
        if (tabLabel === "S2P Preview" && info.clicked) {
          try {
            const body = await page.locator("body").textContent({ timeout: 3000 });
            for (const kw of S2P_PREVIEW_KEYWORDS) {
              if (body.toLowerCase().includes(kw.toLowerCase())) {
                result.s2pPreviewPanels.push(kw);
              }
            }
          } catch { /* ignore */ }
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
    const diagDir = path.resolve(__dirname, "..", "..", "..", "diagnostics");
    if (!fs.existsSync(diagDir)) fs.mkdirSync(diagDir, { recursive: true });
    const outPath = path.join(diagDir, "live_tab_inventory.json");
    fs.writeFileSync(outPath, JSON.stringify(allResults, null, 2));

    console.log("\n" + "=".repeat(60));
    console.log("  LIVE TAB DISCOVERY v4");
    console.log("=".repeat(60));
    for (const r of allResults) {
      const found = r.tabs.filter((t) => t.found).length;
      const clicked = r.tabs.filter((t) => t.clicked).length;
      const total = r.tabs.length;
      const be = r.beUp ? "UP  " : "DOWN";
      const fe = r.feUp ? "UP  " : "DOWN";
      const errors = r.tabs.filter((t) => t.error).length;
      console.log(
        `  ${r.copilot.padEnd(12)} BE:${be} FE:${fe} ` +
        `Found:${found}/${total} Clicked:${clicked}/${total} ` +
        `Panels:${r.totalPanels} Errors:${errors}`,
      );
      if (r.missingTabs.length) console.log(`    Missing: ${r.missingTabs.join(", ")}`);
      if (r.s2pPreviewPanels.length) console.log(`    S2P Preview: ${r.s2pPreviewPanels.join(", ")}`);
      for (const t of r.tabs) {
        if (t.error) console.log(`    ${t.label}: ${t.error}`);
      }
    }
    console.log(`\n  Output: ${outPath}\n`);
  });
});
