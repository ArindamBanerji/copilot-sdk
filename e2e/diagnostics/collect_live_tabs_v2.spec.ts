/**
 * Live Tab Discovery v2 — visits all 5 copilots, captures tabs + panels.
 *
 * Deploy to: copilot-sdk/e2e/diagnostics/collect_live_tabs_v2.spec.ts
 * Run:       npx playwright test --config=diagnostics/playwright.config.ts diagnostics/collect_live_tabs_v2.spec.ts --reporter=list
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

interface TabInfo { label: string; found: boolean; panels: string[]; headings: string[] }
interface Result {
  copilot: string; fePort: number; bePort: number;
  feUp: boolean; beUp: boolean;
  tabs: TabInfo[]; missingTabs: string[];
  s2pPreviewPanels: string[]; totalPanels: number;
  timestamp: string;
}

const allResults: Result[] = [];

test.describe("Live Tab Discovery", () => {
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

      // Wait for tabs to render
      await page.waitForTimeout(2000);

      // Click each expected tab using ONLY getByRole("tab") — the proven selector
      for (const tabLabel of cop.tabs) {
        const info: TabInfo = { label: tabLabel, found: false, panels: [], headings: [] };
        const tab = page.getByRole("tab", { name: tabLabel });

        try {
          const count = await tab.count();
          if (count === 0) {
            result.tabs.push(info);
            continue;
          }
          info.found = true;
          await tab.first().click({ timeout: 5000 });
          await page.waitForTimeout(1500);

          // Capture section/panel headings
          const sections = await page.locator("section, [class*='Panel']").all();
          const seen = new Set<string>();
          for (const sec of sections.slice(0, 20)) {
            const h = await sec.locator("h2, h3, h4, p[class*='uppercase']").first().textContent().catch(() => null);
            if (h && h.trim().length > 1 && h.trim().length < 60 && !seen.has(h.trim())) {
              seen.add(h.trim());
              info.panels.push(h.trim());
            }
          }

          // S2P Preview: check for S2P panels
          if (tabLabel === "S2P Preview") {
            const pageText = (await page.locator("body").textContent().catch(() => "")) ?? "";
            for (const kw of S2P_PREVIEW_KEYWORDS) {
              if (pageText.toLowerCase().includes(kw.toLowerCase())) {
                result.s2pPreviewPanels.push(kw);
              }
            }
          }

          result.totalPanels += info.panels.length;
        } catch {
          info.found = false;
        }
        result.tabs.push(info);
      }

      result.missingTabs = cop.tabs.filter(t => !result.tabs.some(ti => ti.label === t && ti.found));
      allResults.push(result);
    });
  }

  test.afterAll(() => {
    const diagDir = path.resolve(__dirname, "..", "..", "..", "diagnostics");
    if (!fs.existsSync(diagDir)) fs.mkdirSync(diagDir, { recursive: true });
    const outPath = path.join(diagDir, "live_tab_inventory.json");
    fs.writeFileSync(outPath, JSON.stringify(allResults, null, 2));

    console.log("\n" + "=".repeat(60));
    console.log("  LIVE TAB DISCOVERY");
    console.log("=".repeat(60));
    for (const r of allResults) {
      const found = r.tabs.filter(t => t.found).length;
      const total = r.tabs.length;
      const be = r.beUp ? "UP  " : "DOWN";
      const fe = r.feUp ? "UP  " : "DOWN";
      console.log(`  ${r.copilot.padEnd(12)} BE:${be} FE:${fe} Tabs:${found}/${total} Panels:${r.totalPanels} Missing:${r.missingTabs.length}`);
      if (r.missingTabs.length) console.log(`    Missing: ${r.missingTabs.join(", ")}`);
      if (r.s2pPreviewPanels.length) console.log(`    S2P Preview: ${r.s2pPreviewPanels.join(", ")}`);
    }
    console.log(`\n  Output: ${outPath}\n`);
  });
});
