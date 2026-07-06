/**
 * Live Tab Discovery — visits all 5 copilots at runtime, captures tabs + panels.
 *
 * Source:  claude_projects/diagnostics/src/collect_live_tabs.spec.ts
 * Deploy:  Copy to copilot-sdk/e2e/diagnostics/collect_live_tabs.spec.ts
 *
 * Run:
 *   cd copilot-sdk/e2e
 *   npx playwright test diagnostics/collect_live_tabs.spec.ts --reporter=list
 *
 * Requires: demo.py --no-browser running (all 5 copilots + SOC)
 * Output:   claude_projects/diagnostics/live_tab_inventory.json
 */

import { test } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ── Copilot ports (must match demo.py) ──
const COPILOTS = [
  { name: "Trading",    fePort: 5174, bePort: 8010 },
  { name: "Purchasing", fePort: 5175, bePort: 8020 },
  { name: "DataOps",    fePort: 5176, bePort: 8030 },
  { name: "S2P",        fePort: 5177, bePort: 8002 },
  { name: "SOC",        fePort: 5173, bePort: 8001 },
];

// ── Expected tabs from source analysis (ground truth) ──
const EXPECTED_TABS: Record<string, string[]> = {
  Trading:    ["Dashboard", "Log Trade", "Analysis", "Performance", "Journal"],
  Purchasing: ["Dashboard", "Order", "Analysis", "Inventory", "Performance"],
  DataOps:    ["Dashboard", "Triage", "Insight", "Evidence", "Curve"],
  S2P:        ["Dashboard", "Exception Triage", "Insight", "Evidence", "Suppliers", "Performance"],
  SOC:        ["SOC Analytics", "Runtime Evolution", "Alert Triage", "Compounding", "Executive Narrative", "S2P Preview"],
};

// ── S2P panels that live in SOC repo but render on S2P Preview tab ──
const S2P_PREVIEW_PANELS = [
  "Financial Impact", "Working Capital", "Disruption",
  "Compliance", "Process Fusion", "Novelty", "Trend",
];

interface TabResult {
  label: string;
  found: boolean;
  clickable: boolean;
  panelsVisible: string[];
  headingsVisible: string[];
  hasContent: boolean;
  consoleErrors: string[];
}

interface CopilotResult {
  copilot: string;
  frontendPort: number;
  backendPort: number;
  frontendUp: boolean;
  backendUp: boolean;
  backendHealth: Record<string, unknown> | null;
  expectedTabs: string[];
  discoveredTabs: TabResult[];
  extraButtons: string[];
  missingTabs: string[];
  totalPanels: number;
  s2pPreviewPanels: string[];
  timestamp: string;
}

const allResults: CopilotResult[] = [];

// Use serial to avoid port conflicts
test.describe("Live Tab Discovery", () => {

  for (const cop of COPILOTS) {
    test(`${cop.name} — discover tabs and panels`, async ({ page, request }) => {

      const result: CopilotResult = {
        copilot: cop.name,
        frontendPort: cop.fePort,
        backendPort: cop.bePort,
        frontendUp: false,
        backendUp: false,
        backendHealth: null,
        expectedTabs: EXPECTED_TABS[cop.name] || [],
        discoveredTabs: [],
        extraButtons: [],
        missingTabs: [],
        totalPanels: 0,
        s2pPreviewPanels: [],
        timestamp: new Date().toISOString(),
      };

      // ── Capture console errors before any navigation ──
      const consoleErrors: string[] = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") {
          consoleErrors.push(msg.text().slice(0, 200));
        }
      });

      // ── 1. Check backend health (try multiple paths) ──
      const healthPaths = ["/health", "/api/health"];
      for (const hp of healthPaths) {
        try {
          const resp = await request.get(
            `http://127.0.0.1:${cop.bePort}${hp}`,
            { timeout: 5000 },
          );
          if (resp.ok()) {
            result.backendUp = true;
            result.backendHealth = await resp.json().catch(() => ({}));
            break;
          }
        } catch {
          // Try next path
        }
      }

      // ── 2. Navigate to frontend ──
      try {
        await page.goto(`http://127.0.0.1:${cop.fePort}`, {
          timeout: 15000,
          waitUntil: "domcontentloaded",
        });
        result.frontendUp = true;
      } catch {
        result.frontendUp = false;
        allResults.push(result);
        return;
      }

      // Wait for app shell to render
      await page.waitForTimeout(3000);

      // ── 3. Click each expected tab and capture panels ──
      const expected = EXPECTED_TABS[cop.name] || [];
      const clickedLabels = new Set<string>();

      for (const tabLabel of expected) {
        const tabResult: TabResult = {
          label: tabLabel,
          found: false,
          clickable: false,
          panelsVisible: [],
          headingsVisible: [],
          hasContent: false,
          consoleErrors: [],
        };

        // Try multiple selectors (ordered by specificity)
        const selectors = [
          page.getByRole("tab", { name: tabLabel }),
          page.getByText(tabLabel, { exact: true }).first(),
          page.locator(`button:has-text("${tabLabel}")`).first(),
        ];

        let clicked = false;
        for (const sel of selectors) {
          try {
            if ((await sel.count()) > 0 && (await sel.first().isVisible())) {
              tabResult.found = true;
              // Clear console errors before clicking
              consoleErrors.length = 0;
              await sel.first().click({ timeout: 3000 });
              tabResult.clickable = true;
              clicked = true;
              break;
            }
          } catch {
            continue;
          }
        }

        if (clicked) {
          await page.waitForTimeout(2000);

          // Capture headings (h2, h3, h4)
          const headings = await page
            .locator("h2, h3, h4")
            .allTextContents()
            .catch(() => []);
          tabResult.headingsVisible = headings
            .map((h) => h.trim())
            .filter((h) => h.length > 1 && h.length < 60);

          // Capture panel/section titles
          const sections = await page
            .locator(
              "section, [class*='panel' i], [class*='Panel']"
            )
            .all();

          const panelSet = new Set<string>();
          for (const sec of sections.slice(0, 20)) {
            const heading = await sec
              .locator(
                "h2, h3, h4, p[class*='title' i], p[class*='heading' i], " +
                "p[class*='uppercase']"
              )
              .first()
              .textContent()
              .catch(() => null);
            if (heading) {
              const clean = heading.trim();
              if (clean.length > 1 && clean.length < 60) {
                panelSet.add(clean);
              }
            }
          }
          tabResult.panelsVisible = [...panelSet];
          tabResult.hasContent = panelSet.size > 0 || tabResult.headingsVisible.length > 0;
          result.totalPanels += panelSet.size;

          // Capture any console errors from this tab
          tabResult.consoleErrors = [...consoleErrors];
          consoleErrors.length = 0;

          // Special: if this is S2P Preview tab, check for S2P panels
          if (tabLabel === "S2P Preview") {
            for (const panelName of S2P_PREVIEW_PANELS) {
              const found = tabResult.panelsVisible.some(
                (p) => p.toLowerCase().includes(panelName.toLowerCase())
              ) || tabResult.headingsVisible.some(
                (h) => h.toLowerCase().includes(panelName.toLowerCase())
              );
              if (found) {
                result.s2pPreviewPanels.push(panelName);
              }
            }
          }
        }

        result.discoveredTabs.push(tabResult);
        clickedLabels.add(tabLabel);
      }

      // ── 4. Scan for extra buttons not in expected list ──
      try {
        const allBtns = await page
          .locator("button, [role='tab']")
          .allTextContents();
        for (const text of allBtns) {
          const label = text.trim();
          if (
            label.length > 2 &&
            label.length < 30 &&
            !clickedLabels.has(label) &&
            label[0] === label[0].toUpperCase() &&
            !label.match(/^[0-9<>×✕]/)
          ) {
            if (!result.extraButtons.includes(label)) {
              result.extraButtons.push(label);
            }
          }
        }
      } catch {
        // Ignore
      }

      // ── 5. Missing tabs ──
      result.missingTabs = expected.filter(
        (t) => !result.discoveredTabs.some((d) => d.label === t && d.found)
      );

      allResults.push(result);
    });
  }

  test.afterAll(() => {
    // Output to diagnostics/ directory (3 levels up from e2e/diagnostics/)
    // copilot-sdk/e2e/diagnostics/ -> copilot-sdk/ -> claude_projects/diagnostics/
    const projectRoot = path.resolve(__dirname, "..", "..", "..");
    const diagDir = path.join(projectRoot, "diagnostics");
    if (!fs.existsSync(diagDir)) {
      fs.mkdirSync(diagDir, { recursive: true });
    }
    const outPath = path.join(diagDir, "live_tab_inventory.json");
    fs.writeFileSync(outPath, JSON.stringify(allResults, null, 2));

    // Print summary
    console.log("\n" + "=".repeat(60));
    console.log("  LIVE TAB DISCOVERY SUMMARY");
    console.log("=".repeat(60) + "\n");

    for (const r of allResults) {
      const found = r.discoveredTabs.filter((t) => t.found).length;
      const total = r.expectedTabs.length;
      const panels = r.totalPanels;
      const missing = r.missingTabs.length;
      const errors = r.discoveredTabs.reduce(
        (sum, t) => sum + t.consoleErrors.length, 0
      );
      const be = r.backendUp ? "UP  " : "DOWN";
      const fe = r.frontendUp ? "UP  " : "DOWN";

      console.log(
        `  ${r.copilot.padEnd(12)} ` +
        `BE:${be} FE:${fe} ` +
        `Tabs:${found}/${total}  ` +
        `Panels:${String(panels).padStart(3)}  ` +
        `Missing:${missing}  ` +
        `Errors:${errors}`
      );
      if (missing > 0) {
        console.log(`    Missing: ${r.missingTabs.join(", ")}`);
      }
      if (r.s2pPreviewPanels.length > 0) {
        console.log(`    S2P Preview panels: ${r.s2pPreviewPanels.join(", ")}`);
      }
    }

    console.log(`\n  Output: ${outPath}\n`);
  });
});
