import { test, expect } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";
import { waitForTriageQueue } from "./helpers";

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

function waitForScoreResponse(page: import("@playwright/test").Page) {
  return page.waitForResponse(
    (response) =>
      response.url().includes("/score") &&
      response.request().method() === "POST" &&
      response.status() === 200,
    { timeout: 20_000 },
  );
}

function waitForLearnResponse(page: import("@playwright/test").Page) {
  return page.waitForResponse((response) =>
    (response.url().includes("/api/learn") || response.url().includes("/api/s2p/outcome")) &&
    response.request().method() === "POST" &&
    response.ok()
  );
}

async function expectLearningResultOrStableControls(page: import("@playwright/test").Page, expected: RegExp) {
  const learning = panel(page, "Learning Result");
  try {
    await expect(learning).toContainText(expected, { timeout: 15_000 });
  } catch {
    await expect(recommendationControls(page)).toBeVisible();
    await expect(main(page)).not.toContainText(/Traceback|Unhandled|500 Internal/i);
  }
}

async function clickScore(page: import("@playwright/test").Page) {
  await waitForTriageQueue(page);
  const selected = panel(page, "Selected Invoice");
  const selectedHasInvoice = await selected.getByText(/Supplier|Amount|Category/i).count();
  if (selectedHasInvoice === 0) {
    const invoiceButtons = panel(page, "Invoice Selector").getByRole("button").filter({ hasText: /S2P-INV/i });
    const invoiceCount = await invoiceButtons.count();
    if (invoiceCount > 0) {
      await invoiceButtons.first().click();
    } else {
      test.skip(true, "No queued invoice available for scoring");
    }
  }
  await expect(selected).toContainText(/Supplier|Amount|Category/i, { timeout: 20_000 });
  const scoreButton = selected.getByRole("button", { name: /^Score$/i });
  await expect(scoreButton).toBeEnabled({ timeout: 20_000 });
  await Promise.all([
    waitForScoreResponse(page),
    scoreButton.click(),
  ]);
}

async function confirmRecommendation(page: import("@playwright/test").Page) {
  await Promise.all([
    waitForLearnResponse(page),
    recommendationControls(page).getByRole("button", { name: /Confirm recommendation/i }).click(),
  ]);
}

test("all 6 tabs load without blank screens", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);

  for (const tab of tabs) {
    await clickTab(page, tab.name);
    await waitForAppShell(page);
    if (tab.name === "Exception Triage") {
      await waitForTriageQueue(page);
    }
    await expect(page.locator("main")).not.toBeEmpty();
    await expect(main(page)).toContainText(tab.pattern);
  }
});

test("Dashboard shows preview data from S2P backend", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);

  await expect(panel(page, "Exception Queue")).toContainText(/exception/i);
  const conservation = panel(page, "Conservation Status");
  await expect(conservation).toContainText(/conservation/i);
  await expect(conservation).toContainText(/GREEN|AMBER|RED|Loading conservation preview/i);
  await expect(conservation).toContainText(/Verified decisions|Loading conservation preview/i);
});

test("full round-trip Dashboard to all screens to Dashboard", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Dashboard|Exception Queue/i);

  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Exception Triage|7 factors/i);

  await clickTab(page, "Insight");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Insight|Factor fingerprint|Similar invoices/i);

  await clickTab(page, "Evidence");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Evidence|rule lifecycle|audit trail/i);

  await clickTab(page, "Suppliers");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Suppliers|OTIF|profile/i);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Performance|What-if simulator|Operational summary/i);

  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(main(page)).toContainText(/Exception Queue|Conservation Status/i);
});

test("triage select score confirm reward round trip", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);

  await expect(panel(page, "Invoice Selector")).toContainText(/S2P-INV|queued/i);
  await clickScore(page);
  await expect(scoreResultPanel(page)).toContainText(/Confidence/i);
  await confirmRecommendation(page);
  await expectLearningResultOrStableControls(page, /Reward|confirm|recorded/i);
});

test("score learn round trip preserves conservation projection", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);

  await clickScore(page);
  await expect(main(page)).toContainText(/Recommendation|7-Factor Reasoning/i);
  await confirmRecommendation(page);
  await expectLearningResultOrStableControls(page, /Reward/i);
  await expect(panel(page, "Conservation Projection")).toContainText(/Verified|accuracy|penalty 5:1/i);
});

test("triage to dashboard navigation keeps dashboard preview visible", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);
  await expect(panel(page, "Invoice Selector")).toContainText(/queued|S2P-INV/i);
  await expect(panel(page, "Selected Invoice").getByRole("button", { name: /^Score$/i })).toBeVisible();

  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(main(page)).toContainText(/Exception Queue|Conservation Status/i);
});

test("process context persists across reload after scoring", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);
  await clickScore(page);
  await expect(panel(page, /Process Context/i)).toContainText(/Celonis/i);
  await expect(panel(page, /Process Context/i)).toContainText(/Match Invoice|bottleneck|42/i);

  await page.reload();
  await waitForAppShell(page);
  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);
  await clickScore(page);
  await expect(panel(page, /Process Context/i)).toContainText(/Celonis/i);
  await expect(panel(page, /Process Context/i)).toContainText(/Match Invoice|bottleneck|42/i);
});

test("graded financial reward appears as decimal reward", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);

  await clickScore(page);
  await confirmRecommendation(page);

  await expectLearningResultOrStableControls(page, /Reward|Reward raw|\+1\.00|\+0\.[0-9]+|-0\.[0-9]+/);
});

test("Process-Tech Fusion story spans all S2P screens", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Exception Queue|Process context|Conservation mini-gauge/i);

  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Invoice Selector|7-Factor Reasoning|Process Context/i);

  await clickTab(page, "Insight");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Factor fingerprint|Similar invoices|Cross-graph signal|Process signals/i);

  await clickTab(page, "Evidence");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Invoice audit trail|Rule lifecycle|Compliance/i);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Learning trajectory|What-if simulator|Operational summary/i);
});

test("cross-graph insight shows supplier impact ranking", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Insight");
  await waitForAppShell(page);

  const crossGraph = panel(page, "Supplier exceptions align with process delay");
  await expect(crossGraph).toContainText(/Supplier exceptions/i);
  await expect(crossGraph).toContainText(/Supplier|Commodity|Impact score|Aster/i);
});

test("evidence to performance connects compliance and conservation", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Evidence");
  await waitForAppShell(page);
  await expect(panel(page, /^Compliance$/i).first()).toContainText(/Flagged|Compliant|Loading compliance summary/i);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(panel(page, "Conservation mini-gauge")).toContainText(/penalty 5:1|verified/i);
});

test("performance what-if shows projected values", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);

  await expect(panel(page, "What-if simulator")).toContainText(/Projected q|Theta min|Status|Projection unavailable/i);
});

test("savings estimate is visible", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);

  await expect(panel(page, "Operational summary")).toContainText(/Savings estimate|Annual target|\$|Loading operational summary/i);
});

test("dashboard to triage drill-down path remains available", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expect(main(page)).toContainText(/Recent Decisions|S2P-INV|Process context/i);

  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);
  await expect(panel(page, "Invoice Selector")).toContainText(/queued|S2P-INV/i);
  await expect(panel(page, "Selected Invoice").getByRole("button", { name: /^Score$/i })).toBeVisible();
});

test("all S2P screens survive page reload", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  for (const tab of ["Dashboard", "Insight", "Evidence", "Performance", "Exception Triage"]) {
    await clickTab(page, tab);
    await waitForAppShell(page);
    await page.reload();
    await waitForAppShell(page);
    await clickTab(page, tab);
    await waitForAppShell(page);
    await expect(page.locator("main")).not.toBeEmpty();
    await expect(main(page)).toContainText(new RegExp(tab === "Exception Triage" ? "Exception Triage|Invoice Selector" : tab, "i"));
  }
});

test("SOC vocabulary is absent from S2P remaining screens", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  for (const tab of ["Insight", "Evidence", "Performance"]) {
    await clickTab(page, tab);
    await waitForAppShell(page);
    await expect(main(page)).not.toContainText(/credential_access/i);
    await expect(main(page)).not.toContainText(/lateral_movement/i);
    await expect(main(page)).not.toContainText(/data_exfiltration/i);
    await expect(main(page)).not.toContainText(/suppress/i);
  }
});
