/**
 * Capture actual rendered content from all SDK copilot tabs.
 *
 * Equivalent of SOC's collect_tab_content.py. Navigates each copilot,
 * clicks every tab, captures visible text. Output is the test oracle.
 *
 * Usage:
 *   cd C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\e2e
 *   npx tsx helpers/capture-content.ts
 *   npx tsx helpers/capture-content.ts --copilot dataops
 *   npx tsx helpers/capture-content.ts --copilot trading --tab "Log Trade"
 *
 * Requires: all 3 backends + frontends running (python demo.py)
 */

import { chromium, Page } from "playwright";
import * as fs from "fs";

const E2E_DIR = "C:\\Users\\baner\\CopyFolder\\IoT_thoughts\\python-projects\\kaggle_experiments\\claude_projects\\copilot-sdk\\e2e";

interface CopilotConfig {
  name: string;
  url: string;
  backendPort: number;
  tabs: string[];
  setupSteps?: Record<string, (page: Page) => Promise<void>>;
}

const COPILOTS: CopilotConfig[] = [
  {
    name: "trading",
    url: "http://127.0.0.1:5174",
    backendPort: 8010,
    tabs: ["Dashboard", "Log Trade", "Analysis", "Performance"],
  },
  {
    name: "purchasing",
    url: "http://127.0.0.1:5175",
    backendPort: 8020,
    tabs: ["Dashboard", "Order", "Analysis", "Inventory", "Performance"],
  },
  {
    name: "dataops",
    url: "http://127.0.0.1:5176",
    backendPort: 8030,
    tabs: ["Dashboard", "Triage", "Insight", "Evidence", "Curve"],
    setupSteps: {
      Triage: async (page: Page) => {
        const triageBtn = page
          .locator("section")
          .filter({ hasText: /Alert Root Causes/i })
          .getByRole("button", { name: /triage/i })
          .first();
        if (await triageBtn.isVisible({ timeout: 3000 })) {
          await triageBtn.click();
          await page.waitForTimeout(2000);
        }
      },
    },
  },
];

interface TabContent {
  tab: string;
  text: string;
  headings: string[];
  buttons: string[];
  links: string[];
  numbers: string[];
  cards: string[];
}

interface CopilotContent {
  copilot: string;
  url: string;
  capturedAt: string;
  healthStatus: string;
  tabs: Record<string, TabContent>;
}

async function checkHealth(port: number): Promise<string> {
  try {
    const resp = await fetch(`http://127.0.0.1:${port}/health`);
    const data = await resp.json();
    return `${data.status} (${data.domain || "unknown"})`;
  } catch {
    return "UNREACHABLE";
  }
}

async function captureTab(page: Page, tabName: string): Promise<TabContent> {
  await page.waitForTimeout(1500);

  const mainLocator = page.locator("main").first();
  let fullText = "";
  try {
    fullText = await mainLocator.innerText({ timeout: 5000 });
  } catch {
    fullText = await page.locator("body").innerText({ timeout: 5000 });
  }

  const headings: string[] = [];
  for (const tag of ["h1", "h2", "h3", "h4"]) {
    const els = page.locator(tag);
    const count = await els.count();
    for (let i = 0; i < count; i++) {
      try {
        const text = await els.nth(i).innerText({ timeout: 1000 });
        if (text.trim()) headings.push(text.trim());
      } catch {
        /* skip hidden */
      }
    }
  }

  const buttons: string[] = [];
  const btnEls = page.getByRole("button");
  const btnCount = await btnEls.count();
  for (let i = 0; i < Math.min(btnCount, 30); i++) {
    try {
      const text = await btnEls.nth(i).innerText({ timeout: 1000 });
      if (text.trim()) buttons.push(text.trim());
    } catch {
      /* skip */
    }
  }

  const links: string[] = [];
  const linkEls = page.getByRole("link");
  const linkCount = await linkEls.count();
  for (let i = 0; i < Math.min(linkCount, 20); i++) {
    try {
      const text = await linkEls.nth(i).innerText({ timeout: 1000 });
      if (text.trim()) links.push(text.trim());
    } catch {
      /* skip */
    }
  }

  const numbers = Array.from(
    new Set(
      fullText.match(/\d+(\.\d+)?%|\$[\d,.]+|\d+\.\d+|\b\d{2,}\b/g) || []
    )
  );

  const cards: string[] = [];
  const sections = page.locator("section, [class*='card'], [class*='panel']");
  const sectionCount = await sections.count();
  for (let i = 0; i < Math.min(sectionCount, 20); i++) {
    try {
      const text = await sections.nth(i).innerText({ timeout: 1000 });
      if (text.trim()) {
        cards.push(text.trim().substring(0, 150).replace(/\n/g, " | "));
      }
    } catch {
      /* skip */
    }
  }

  return {
    tab: tabName,
    text: fullText,
    headings,
    buttons: [...new Set(buttons)],
    links,
    numbers,
    cards,
  };
}

async function clickTab(page: Page, tabName: string): Promise<boolean> {
  const strategies = [
    () => page.getByRole("button", { name: new RegExp(`^${tabName}$`, "i") }),
    () => page.getByRole("tab", { name: new RegExp(tabName, "i") }),
    () => page.getByText(tabName, { exact: true }),
    () => page.locator(`button:has-text("${tabName}")`).first(),
  ];

  for (const strategy of strategies) {
    try {
      const el = strategy();
      if (await el.isVisible({ timeout: 2000 })) {
        await el.click();
        return true;
      }
    } catch {
      continue;
    }
  }

  console.warn(`  WARNING: Could not find tab: ${tabName}`);
  return false;
}

async function captureCopilot(
  config: CopilotConfig,
  specificTab?: string
): Promise<CopilotContent> {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const health = await checkHealth(config.backendPort);
  console.log(`\n${"=".repeat(60)}`);
  console.log(`  ${config.name.toUpperCase()} COPILOT - ${config.url}`);
  console.log(`  Health: ${health}`);
  console.log("=".repeat(60));

  const content: CopilotContent = {
    copilot: config.name,
    url: config.url,
    capturedAt: new Date().toISOString(),
    healthStatus: health,
    tabs: {},
  };

  await page.goto(config.url, { waitUntil: "networkidle", timeout: 15000 });

  const tabsToCapture = specificTab
    ? config.tabs.filter((t) => t.toLowerCase() === specificTab.toLowerCase())
    : config.tabs;

  for (const tabName of tabsToCapture) {
    console.log(`\n  --- ${tabName} ---`);

    if (config.setupSteps?.[tabName]) {
      if (tabName !== "Dashboard") {
        await clickTab(page, "Dashboard");
        await page.waitForTimeout(1000);
      }
      await config.setupSteps[tabName](page);
    } else if (tabName !== config.tabs[0]) {
      await clickTab(page, tabName);
    }

    const tabContent = await captureTab(page, tabName);
    content.tabs[tabName] = tabContent;

    console.log(`  Headings: ${tabContent.headings.join(" | ") || "(none)"}`);
    console.log(`  Buttons:  ${tabContent.buttons.slice(0, 8).join(" | ")}`);
    console.log(`  Numbers:  ${tabContent.numbers.slice(0, 10).join(", ")}`);
    console.log(
      `  Text (first 200): ${tabContent.text.substring(0, 200).replace(/\n/g, " ")}`
    );
    console.log(`  Cards:    ${tabContent.cards.length}`);
  }

  await browser.close();
  return content;
}

async function main() {
  const args = process.argv.slice(2);
  let filterCopilot: string | undefined;
  let filterTab: string | undefined;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--copilot" && args[i + 1]) filterCopilot = args[i + 1];
    if (args[i] === "--tab" && args[i + 1]) filterTab = args[i + 1];
  }

  const copilots = filterCopilot
    ? COPILOTS.filter((c) => c.name === filterCopilot.toLowerCase())
    : COPILOTS;

  if (copilots.length === 0) {
    console.error(
      `Unknown copilot: ${filterCopilot}. Options: ${COPILOTS.map((c) => c.name).join(", ")}`
    );
    process.exit(1);
  }

  console.log("============================================================");
  console.log("  Tab Content Capture - SDK Copilots                         ");
  console.log("  Equivalent of SOC collect_tab_content.py                   ");
  console.log("============================================================");

  const allContent: Record<string, CopilotContent> = {};

  for (const config of copilots) {
    try {
      const content = await captureCopilot(config, filterTab);
      allContent[config.name] = content;

      const outPath = E2E_DIR + "\\tab-content-" + config.name + ".json";
      fs.writeFileSync(outPath, JSON.stringify(content, null, 2), "utf-8");
      console.log(`\n  Saved: ${outPath}`);
    } catch (err) {
      console.error(`\n  Failed to capture ${config.name}: ${err}`);
    }
  }

  if (copilots.length > 1) {
    const combinedPath = E2E_DIR + "\\tab-content-all.json";
    fs.writeFileSync(
      combinedPath,
      JSON.stringify(allContent, null, 2),
      "utf-8"
    );
    console.log(`\n  Saved combined: ${combinedPath}`);
  }

  console.log("\n============================================================");
  console.log("  Assertion Verification Summary                             ");
  console.log("============================================================");

  for (const [name, content] of Object.entries(allContent)) {
    console.log(`\n  ${name.toUpperCase()}:`);
    for (const [tabName, tab] of Object.entries(content.tabs)) {
      const textLen = tab.text.length;
      const hasIKS = /IKS/i.test(tab.text);
      const hasFingerprint = /fingerprint/i.test(tab.text);
      const hasConservation = /conservation/i.test(tab.text);
      console.log(
        `    ${tabName}: ${textLen} chars, ` +
          `IKS=${hasIKS ? "Y" : "N"} ` +
          `FP=${hasFingerprint ? "Y" : "N"} ` +
          `CON=${hasConservation ? "Y" : "N"} ` +
          `${tab.headings.length} headings, ${tab.buttons.length} buttons`
      );
    }
  }

  console.log(
    "\n  Use tab-content-*.json to verify E2E assertion patterns."
  );
  console.log(
    "  Every expectAnyText pattern should match at least one string.\n"
  );
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
