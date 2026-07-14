/**
 * Deep Live Tab Discovery v5
 *
 * Goes beyond "does the tab exist?" to capture what's ON each tab:
 * - Panel/section headings
 * - Buttons and actions (what can the user DO)
 * - Content state: data / loading / error / empty
 * - Data tables and their row counts
 *
 * Output is structured for roadmap and narrative review sessions.
 *
 * Deploy to: copilot-sdk/e2e/diagnostics/
 * Run:       npx playwright test --config=diagnostics/playwright.config.ts
 *              diagnostics/collect_live_tabs_v5.spec.ts --reporter=list
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

const S2P_PREVIEW_KEYWORDS = [
  "Financial Impact", "Working Capital", "Disruption",
  "Compliance", "Process Fusion", "Novelty", "Trend",
];

// ── Types ──

interface PanelInfo {
  title: string;
  state: "data" | "loading" | "error" | "empty" | "unknown";
  buttons: string[];
  badges: string[];
}

interface TabDetail {
  label: string;
  found: boolean;
  clicked: boolean;
  headings: string[];
  panels: PanelInfo[];
  buttons: string[];       // all visible buttons on the tab
  tableCount: number;      // how many data tables
  inputCount: number;      // how many form inputs
  state: "populated" | "partial" | "empty" | "error" | "not_found";
  error: string | null;
}

interface CopilotResult {
  copilot: string;
  fePort: number;
  bePort: number;
  feUp: boolean;
  beUp: boolean;
  tabs: TabDetail[];
  missingTabs: string[];
  s2pPreviewPanels: string[];
  summary: {
    tabsFound: number;
    tabsTotal: number;
    totalPanels: number;
    totalButtons: number;
    populatedTabs: number;
    errorTabs: number;
  };
  timestamp: string;
}

const allResults: CopilotResult[] = [];

// ── Helpers ──

/** Deduplicate and clean a string array */
function clean(items: string[]): string[] {
  const seen = new Set<string>();
  return items
    .map((s) => s.trim())
    .filter((s) => s.length > 0 && s.length < 80 && !seen.has(s) && (seen.add(s), true));
}

/** Classify content state based on visible text patterns */
function classifyState(text: string): PanelInfo["state"] {
  const lower = text.toLowerCase();
  if (lower.includes("loading") || lower.includes("fetching")) return "loading";
  if (
    lower.includes("backend unavailable") ||
    lower.includes("service not connected") ||
    lower.includes("unable to load") ||
    lower.includes("request failed") ||
    lower.includes("failed") ||
    lower.includes(" error")
  ) return "error";
  if (lower.includes("no data") || lower.includes("no results") || lower.includes("empty")) return "empty";
  if (text.length > 20) return "data";
  return "unknown";
}

/** Discover everything rendered on the current tab */
async function discoverTabContent(
  page: import("@playwright/test").Page,
  tabLabel: string,
): Promise<TabDetail> {
  const detail: TabDetail = {
    label: tabLabel,
    found: false,
    clicked: false,
    headings: [],
    panels: [],
    buttons: [],
    tableCount: 0,
    inputCount: 0,
    state: "not_found",
    error: null,
  };

  try {
    // Click the tab
    const btn = page.getByText(tabLabel, { exact: true }).first();
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) return detail;

    detail.found = true;
    await btn.click({ timeout: 5000, force: true });
    detail.clicked = true;
    await page.waitForTimeout(2000);

    // 1. Capture ALL headings (h1-h6)
    const headingEls = await page.locator("h1, h2, h3, h4, h5, h6").allTextContents().catch(() => []);
    detail.headings = clean(headingEls);

    // 2. Capture sections/panels with their content
    const sections = await page.locator("section, [class*='Panel'], [class*='panel']").all();
    for (const sec of sections.slice(0, 30)) {
      try {
        // Panel title
        const titleEl = sec.locator("h2, h3, h4, p[class*='uppercase'], p[class*='semibold']").first();
        const title = await titleEl.textContent({ timeout: 500 }).catch(() => null);
        if (!title || title.trim().length < 2 || title.trim().length > 80) continue;

        // Panel content state
        const content = (await sec.textContent({ timeout: 500 }).catch(() => "")) ?? "";
        const state = classifyState(content);

        // Buttons inside this panel
        const panelBtns = await sec.locator("button").allTextContents().catch(() => []);
        const cleanBtns = clean(panelBtns).filter((b) => b.length > 1 && b.length < 40);

        // Badges (spans with short text, often status indicators)
        const badgeEls = await sec
          .locator("span[class*='badge'], span[class*='Badge'], span[class*='status'], span[class*='tag']")
          .allTextContents()
          .catch(() => []);
        const badges = clean(badgeEls).filter((b) => b.length < 30);

        detail.panels.push({
          title: title.trim(),
          state,
          buttons: cleanBtns,
          badges,
        });
      } catch {
        // Skip this section
      }
    }

    // 3. ALL buttons visible on the tab (not just in panels)
    const allBtns = await page.locator("button").allTextContents().catch(() => []);
    detail.buttons = clean(allBtns).filter(
      (b) => b.length > 1 && b.length < 40 && !b.match(/^[×✕<>]$/),
    );

    // 4. Data tables
    detail.tableCount = await page.locator("table").count().catch(() => 0);

    // 5. Form inputs
    detail.inputCount = await page
      .locator("input, select, textarea")
      .count()
      .catch(() => 0);

    // 6. Classify overall tab state
    const dataPanels = detail.panels.filter((p) => p.state === "data").length;
    const errorPanels = detail.panels.filter((p) => p.state === "error").length;
    const hasData = dataPanels > 0;
    const hasError = errorPanels > 0;
    if (hasData && !hasError) detail.state = "populated";
    else if (dataPanels >= 3 && errorPanels < dataPanels) detail.state = "populated";
    else if (hasData && hasError) detail.state = "partial";
    else if (hasError) detail.state = "error";
    else if (detail.headings.length > 0 || detail.buttons.length > 0) detail.state = "populated";
    else detail.state = "empty";
  } catch (e) {
    detail.error = String(e).slice(0, 150);
    detail.state = "error";
  }

  return detail;
}

// ── Tests ──

test.describe("Deep Live Tab Discovery v5", () => {
  for (const cop of COPILOTS) {
    test(`${cop.name}`, async ({ page, request }) => {
      const result: CopilotResult = {
        copilot: cop.name,
        fePort: cop.fePort,
        bePort: cop.bePort,
        feUp: false,
        beUp: false,
        tabs: [],
        missingTabs: [],
        s2pPreviewPanels: [],
        summary: {
          tabsFound: 0,
          tabsTotal: cop.tabs.length,
          totalPanels: 0,
          totalButtons: 0,
          populatedTabs: 0,
          errorTabs: 0,
        },
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
        await page.goto(`http://127.0.0.1:${cop.fePort}`, {
          timeout: 10000,
          waitUntil: "domcontentloaded",
        });
        result.feUp = true;
      } catch {
        allResults.push(result);
        return;
      }

      await page.waitForTimeout(2000);

      // Deep-discover each tab
      for (const tabLabel of cop.tabs) {
        const detail = await discoverTabContent(page, tabLabel);

        // S2P Preview: check for known S2P panels
        if (tabLabel === "S2P Preview" && detail.clicked) {
          try {
            const body = (await page.locator("body").textContent({ timeout: 3000 })) ?? "";
            for (const kw of S2P_PREVIEW_KEYWORDS) {
              if (body.toLowerCase().includes(kw.toLowerCase())) {
                result.s2pPreviewPanels.push(kw);
              }
            }
          } catch { /* ignore */ }
        }

        result.tabs.push(detail);
      }

      // Compute summary
      result.missingTabs = cop.tabs.filter(
        (t) => !result.tabs.some((td) => td.label === t && td.found),
      );
      result.summary.tabsFound = result.tabs.filter((t) => t.found).length;
      result.summary.totalPanels = result.tabs.reduce((s, t) => s + t.panels.length, 0);
      result.summary.totalButtons = result.tabs.reduce((s, t) => s + t.buttons.length, 0);
      result.summary.populatedTabs = result.tabs.filter((t) => t.state === "populated").length;
      result.summary.errorTabs = result.tabs.filter((t) => t.state === "error").length;

      allResults.push(result);
    });
  }

  test.afterAll(() => {
    // Write to diagnostics directory
    const diagDir = path.resolve(__dirname, "..", "..", "..", "diagnostics");
    if (!fs.existsSync(diagDir)) fs.mkdirSync(diagDir, { recursive: true });
    const outPath = path.join(diagDir, "live_tab_inventory.json");
    fs.writeFileSync(outPath, JSON.stringify(allResults, null, 2));

    // Print summary
    console.log("\n" + "=".repeat(70));
    console.log("  DEEP LIVE TAB DISCOVERY v5");
    console.log("=".repeat(70));

    for (const r of allResults) {
      const s = r.summary;
      const be = r.beUp ? "UP  " : "DOWN";
      const fe = r.feUp ? "UP  " : "DOWN";
      console.log(
        `\n  ${r.copilot.toUpperCase()}` +
        `  BE:${be} FE:${fe}` +
        `  Tabs:${s.tabsFound}/${s.tabsTotal}` +
        `  Panels:${s.totalPanels}` +
        `  Buttons:${s.totalButtons}` +
        `  Populated:${s.populatedTabs}` +
        `  Errors:${s.errorTabs}`,
      );
      for (const t of r.tabs) {
        const icon = t.state === "populated" ? "✅" :
                     t.state === "partial" ? "🟡" :
                     t.state === "error" ? "❌" :
                     t.state === "empty" ? "⬜" : "❓";
        const panelNames = t.panels.map((p) => p.title).join(", ");
        const btnCount = t.buttons.length;
        console.log(
          `    ${icon} ${t.label.padEnd(22)} ` +
          `Panels:${String(t.panels.length).padStart(2)} ` +
          `Btns:${String(btnCount).padStart(2)} ` +
          `Tables:${t.tableCount} ` +
          `Inputs:${t.inputCount}` +
          (panelNames ? `  [${panelNames.slice(0, 70)}]` : ""),
        );
      }
      if (r.s2pPreviewPanels.length) {
        console.log(`    S2P Preview: ${r.s2pPreviewPanels.join(", ")}`);
      }
    }

    console.log(`\n  Output: ${outPath}\n`);
  });
});
