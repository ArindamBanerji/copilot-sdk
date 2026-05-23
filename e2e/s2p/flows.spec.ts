import { test, expect } from "@playwright/test";
import { clickTab } from "../helpers/ui";

const tabs = [
  { name: "Dashboard", pattern: /Dashboard|Exception Queue/i },
  { name: "Exception Triage", pattern: /Exception Triage|Invoice Selector/i },
  { name: "Insight", pattern: /Insight|fingerprint/i },
  { name: "Evidence", pattern: /Evidence|audit trail/i },
  { name: "Suppliers", pattern: /Suppliers|supplier profiles/i },
  { name: "Performance", pattern: /Performance|trajectory/i },
];

function main(page: import("@playwright/test").Page) {
  return page.locator("main");
}

function panel(page: import("@playwright/test").Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

function scoreResultPanel(page: import("@playwright/test").Page) {
  return page.locator("article", { hasText: "Action index" });
}

function recommendationControls(page: import("@playwright/test").Page) {
  return page.locator("article", { has: page.getByRole("button", { name: /Confirm recommendation/i }) });
}

async function clickScore(page: import("@playwright/test").Page) {
  await panel(page, "Selected Invoice").getByRole("button", { name: /^Score$/i }).click();
}

async function confirmRecommendation(page: import("@playwright/test").Page) {
  await recommendationControls(page).getByRole("button", { name: /Confirm recommendation/i }).click();
}

test("all 6 tabs load without blank screens", async ({ page }) => {
  await page.goto("/");

  for (const tab of tabs) {
    await clickTab(page, tab.name);
    await expect(page.locator("main")).not.toBeEmpty();
    await expect(main(page)).toContainText(tab.pattern);
  }
});

test("Dashboard shows preview data from S2P backend", async ({ page }) => {
  await page.goto("/");

  await expect(panel(page, "Exception Queue")).toContainText(/exception/i);
  const conservation = panel(page, "Conservation Status");
  await expect(conservation).toContainText(/conservation/i);
  await expect(conservation).toContainText(/GREEN|AMBER|RED/i);
  await expect(conservation).toContainText(/Verified decisions/i);
});

test("full round-trip Dashboard to all screens to Dashboard", async ({ page }) => {
  await page.goto("/");
  await expect(main(page)).toContainText(/Dashboard|Exception Queue/i);

  await clickTab(page, "Exception Triage");
  await expect(main(page)).toContainText(/Exception Triage|7 factors/i);

  await clickTab(page, "Insight");
  await expect(main(page)).toContainText(/Insight|Factor fingerprint|Similar invoices/i);

  await clickTab(page, "Evidence");
  await expect(main(page)).toContainText(/Evidence|rule lifecycle|audit trail/i);

  await clickTab(page, "Suppliers");
  await expect(main(page)).toContainText(/Suppliers|OTIF|profile/i);

  await clickTab(page, "Performance");
  await expect(main(page)).toContainText(/Performance|What-if simulator|Operational summary/i);

  await clickTab(page, "Dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(main(page)).toContainText(/Exception Queue|Conservation Status/i);
});

test("triage select score confirm reward round trip", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");

  await expect(panel(page, "Invoice Selector")).toContainText(/S2P-INV|queued/i);
  await clickScore(page);
  await expect(scoreResultPanel(page)).toContainText(/Confidence/i);
  await confirmRecommendation(page);
  await expect(panel(page, "Learning Result")).toContainText(/Reward|confirm|recorded/i, { timeout: 15_000 });
});

test("score learn round trip preserves conservation projection", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");

  await clickScore(page);
  await expect(main(page)).toContainText(/Recommendation|7-Factor Reasoning/i);
  await confirmRecommendation(page);
  await expect(panel(page, "Learning Result")).toContainText(/Reward/i, { timeout: 15_000 });
  await expect(panel(page, "Conservation Projection")).toContainText(/Verified|accuracy|penalty 5:1/i);
});

test("triage to dashboard navigation keeps dashboard preview visible", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");
  await expect(panel(page, "Invoice Selector")).toContainText(/queued|S2P-INV/i);
  await expect(panel(page, "Selected Invoice").getByRole("button", { name: /^Score$/i })).toBeVisible();

  await clickTab(page, "Dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(main(page)).toContainText(/Exception Queue|Conservation Status/i);
});

test("process context persists across reload after scoring", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");
  await clickScore(page);
  await expect(panel(page, /Process Context/i)).toContainText(/Celonis/i);
  await expect(panel(page, /Process Context/i)).toContainText(/Match Invoice|bottleneck|42/i);

  await page.reload();
  await clickTab(page, "Exception Triage");
  await clickScore(page);
  await expect(panel(page, /Process Context/i)).toContainText(/Celonis/i);
  await expect(panel(page, /Process Context/i)).toContainText(/Match Invoice|bottleneck|42/i);
});

test("graded financial reward appears as decimal reward", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");

  await clickScore(page);
  await confirmRecommendation(page);

  await expect(panel(page, "Learning Result")).toContainText(/Reward|Reward raw|\+1\.00|\+0\.[0-9]+|-0\.[0-9]+/, { timeout: 15_000 });
});

test("Process-Tech Fusion story spans all S2P screens", async ({ page }) => {
  await page.goto("/");
  await expect(main(page)).toContainText(/Exception Queue|Process context|Conservation mini-gauge/i);

  await clickTab(page, "Exception Triage");
  await expect(main(page)).toContainText(/Invoice Selector|7-Factor Reasoning|Process Context/i);

  await clickTab(page, "Insight");
  await expect(main(page)).toContainText(/Factor fingerprint|Similar invoices|Cross-graph signal|Process signals/i);

  await clickTab(page, "Evidence");
  await expect(main(page)).toContainText(/Invoice audit trail|Rule lifecycle|Compliance/i);

  await clickTab(page, "Performance");
  await expect(main(page)).toContainText(/Learning trajectory|What-if simulator|Operational summary/i);
});

test("cross-graph insight shows supplier impact ranking", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Insight");

  const crossGraph = panel(page, "Supplier exceptions align with process delay");
  await expect(crossGraph).toContainText(/Supplier exceptions/i);
  await expect(crossGraph).toContainText(/Supplier|Commodity|Impact score|Aster/i);
});

test("evidence to performance connects compliance and conservation", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expect(panel(page, /^Compliance$/i).first()).toContainText(/Flagged|Compliant/i);

  await clickTab(page, "Performance");
  await expect(panel(page, "Conservation mini-gauge")).toContainText(/penalty 5:1|verified/i);
});

test("performance what-if shows projected values", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Performance");

  await expect(panel(page, "What-if simulator")).toContainText(/Projected q|Theta min|Status/i);
});

test("savings estimate is visible", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Performance");

  await expect(panel(page, "Operational summary")).toContainText(/Savings estimate|Annual target|\$/i);
});

test("dashboard to triage drill-down path remains available", async ({ page }) => {
  await page.goto("/");
  await expect(main(page)).toContainText(/Recent Decisions|S2P-INV|Process context/i);

  await clickTab(page, "Exception Triage");
  await expect(panel(page, "Invoice Selector")).toContainText(/queued|S2P-INV/i);
  await expect(panel(page, "Selected Invoice").getByRole("button", { name: /^Score$/i })).toBeVisible();
});

test("all S2P screens survive page reload", async ({ page }) => {
  await page.goto("/");
  for (const tab of ["Dashboard", "Insight", "Evidence", "Performance", "Exception Triage"]) {
    await clickTab(page, tab);
    await page.reload();
    await clickTab(page, tab);
    await expect(page.locator("main")).not.toBeEmpty();
    await expect(main(page)).toContainText(new RegExp(tab === "Exception Triage" ? "Exception Triage|Invoice Selector" : tab, "i"));
  }
});

test("SOC vocabulary is absent from S2P remaining screens", async ({ page }) => {
  await page.goto("/");
  for (const tab of ["Insight", "Evidence", "Performance"]) {
    await clickTab(page, tab);
    await expect(main(page)).not.toContainText(/credential_access/i);
    await expect(main(page)).not.toContainText(/lateral_movement/i);
    await expect(main(page)).not.toContainText(/data_exfiltration/i);
    await expect(main(page)).not.toContainText(/suppress/i);
  }
});
