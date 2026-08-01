/**
 * DOM Scraper — visits every tab of every copilot and dumps:
 *   - All headings (h1-h6)
 *   - All data-testid attributes
 *   - All button texts and aria-labels
 *   - All role="heading" elements
 *
 * Run from: copilot-sdk/e2e/
 * Requires: all copilots running (python demo.py --no-browser)
 *
 * Usage:
 *   npx playwright test scrape-dom.spec.ts --reporter=line
 *
 * Output: dom-scrape.json (in e2e/ directory)
 */

import { test } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

interface TabScrape {
  headings: { tag: string; text: string }[];
  testIds: { testId: string; tag: string; text: string }[];
  buttons: { text: string; ariaLabel: string; name: string }[];
  roleHeadings: string[];
  visibleText: string[];
}

const COPILOTS = [
  {
    name: "trading",
    url: "http://127.0.0.1:5174",
    tabs: ["Dashboard", "Log Trade", "Analysis", "Performance", "Journal"],
  },
  {
    name: "purchasing",
    url: "http://127.0.0.1:5175",
    tabs: ["Dashboard", "Order", "Analysis", "Inventory", "Performance"],
  },
  {
    name: "dataops",
    url: "http://127.0.0.1:5176",
    tabs: ["Dashboard", "Triage", "Insight", "Evidence", "Curve"],
  },
  {
    name: "s2p",
    url: "http://127.0.0.1:5177",
    tabs: [
      "Dashboard",
      "Exception Triage",
      "Insight",
      "Evidence",
      "Suppliers",
      "Performance",
    ],
  },
];

async function scrapeTab(
  page: import("@playwright/test").Page
): Promise<TabScrape> {
  const headings = await page.evaluate(() =>
    Array.from(document.querySelectorAll("h1,h2,h3,h4,h5,h6"))
      .map((el) => ({
        tag: el.tagName.toLowerCase(),
        text: (el.textContent || "").trim(),
      }))
      .filter((h) => h.text.length > 0 && h.text.length < 200)
  );

  const testIds = await page.evaluate(() =>
    Array.from(document.querySelectorAll("[data-testid]"))
      .map((el) => ({
        testId: el.getAttribute("data-testid") || "",
        tag: el.tagName.toLowerCase(),
        text: (el.textContent || "").trim().slice(0, 80),
      }))
      .filter((t) => t.testId.length > 0)
  );

  const buttons = await page.evaluate(() =>
    Array.from(document.querySelectorAll("button, [role='button']"))
      .map((el) => ({
        text: (el.textContent || "").trim().slice(0, 80),
        ariaLabel: el.getAttribute("aria-label") || "",
        name: el.getAttribute("name") || "",
      }))
      .filter((b) => b.text.length > 0 || b.ariaLabel.length > 0)
  );

  const roleHeadings = await page.evaluate(() =>
    Array.from(document.querySelectorAll('[role="heading"]'))
      .map((el) => (el.textContent || "").trim())
      .filter((t) => t.length > 0 && t.length < 200)
  );

  // Capture prominent visible text (section labels, panel titles)
  const visibleText = await page.evaluate(() =>
    Array.from(
      document.querySelectorAll(
        "h1,h2,h3,h4,h5,h6,label,[class*='title'],[class*='heading'],[class*='label'],th,dt,legend,summary"
      )
    )
      .map((el) => (el.textContent || "").trim())
      .filter((t) => t.length > 2 && t.length < 100)
      .filter((t, i, arr) => arr.indexOf(t) === i) // deduplicate
  );

  return { headings, testIds, buttons, roleHeadings, visibleText };
}

async function clickTab(
  page: import("@playwright/test").Page,
  tabName: string
): Promise<boolean> {
  // Try multiple selector strategies (different copilots use different patterns)
  const strategies = [
    () => page.getByRole("tab", { name: tabName, exact: true }),
    () => page.getByRole("button", { name: tabName, exact: true }),
    () => page.getByRole("tab", { name: new RegExp(`^${tabName}$`, "i") }),
    () =>
      page.getByRole("button", { name: new RegExp(`^${tabName}$`, "i") }),
    () => page.locator(`[data-tab="${tabName.toLowerCase().replace(/ /g, "-")}"]`),
    () => page.getByText(tabName, { exact: true }),
  ];

  for (const strategy of strategies) {
    try {
      const locator = strategy();
      if ((await locator.count()) > 0) {
        await locator.first().click({ timeout: 3000 });
        return true;
      }
    } catch {
      // try next strategy
    }
  }
  return false;
}

test("scrape all copilot tabs DOM", async ({ page }) => {
  test.setTimeout(180_000); // 3 minutes total

  const result: Record<string, Record<string, TabScrape | { error: string }>> =
    {};
  const summary: { copilot: string; tab: string; headings: number; testIds: number; buttons: number }[] = [];

  for (const copilot of COPILOTS) {
    result[copilot.name] = {};
    console.log(`\n=== ${copilot.name.toUpperCase()} (${copilot.url}) ===`);

    // Check if copilot is reachable
    try {
      const response = await page.goto(copilot.url, {
        timeout: 10000,
        waitUntil: "domcontentloaded",
      });
      if (!response || !response.ok()) {
        console.log(`  SKIP: ${copilot.name} not reachable`);
        result[copilot.name]["_status"] = { error: "not reachable" } as any;
        continue;
      }
    } catch (err) {
      console.log(`  SKIP: ${copilot.name} connection refused`);
      result[copilot.name]["_status"] = {
        error: `connection failed: ${err}`,
      } as any;
      continue;
    }

    // Wait for app shell to render
    await page.waitForTimeout(3000);

    for (const tab of copilot.tabs) {
      console.log(`  Scraping: ${tab}...`);

      try {
        const clicked = await clickTab(page, tab);
        if (!clicked) {
          console.log(`    WARN: could not click tab "${tab}"`);
          result[copilot.name][tab] = { error: `tab "${tab}" not clickable` } as any;
          continue;
        }

        // Wait for tab content to render
        await page.waitForTimeout(2000);

        const scrape = await scrapeTab(page);
        result[copilot.name][tab] = scrape;

        summary.push({
          copilot: copilot.name,
          tab,
          headings: scrape.headings.length,
          testIds: scrape.testIds.length,
          buttons: scrape.buttons.length,
        });

        console.log(
          `    headings=${scrape.headings.length} testIds=${scrape.testIds.length} buttons=${scrape.buttons.length}`
        );
      } catch (err) {
        console.log(`    ERROR: ${err}`);
        result[copilot.name][tab] = { error: String(err) } as any;
      }
    }
  }

  // Write results
  const outPath = path.join(__dirname, "dom-scrape.json");
  fs.writeFileSync(outPath, JSON.stringify(result, null, 2));
  console.log(`\nWrote: ${outPath}`);

  // Print summary
  console.log("\n=== SUMMARY ===");
  console.log(
    `${"Copilot".padEnd(12)} ${"Tab".padEnd(20)} ${"Headings".padStart(8)} ${"TestIDs".padStart(8)} ${"Buttons".padStart(8)}`
  );
  console.log("-".repeat(60));
  for (const s of summary) {
    console.log(
      `${s.copilot.padEnd(12)} ${s.tab.padEnd(20)} ${String(s.headings).padStart(8)} ${String(s.testIds).padStart(8)} ${String(s.buttons).padStart(8)}`
    );
  }

  const totalHeadings = summary.reduce((a, s) => a + s.headings, 0);
  const totalTestIds = summary.reduce((a, s) => a + s.testIds, 0);
  const totalButtons = summary.reduce((a, s) => a + s.buttons, 0);
  console.log("-".repeat(60));
  console.log(
    `${"TOTAL".padEnd(12)} ${"".padEnd(20)} ${String(totalHeadings).padStart(8)} ${String(totalTestIds).padStart(8)} ${String(totalButtons).padStart(8)}`
  );
});
