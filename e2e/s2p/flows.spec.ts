import { test, expect } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

const tabs = [
  { name: "Dashboard", pattern: /Dashboard|Exception Queue/i },
  { name: "Exception Triage", pattern: /Exception Triage|Invoice Selector/i },
  { name: "Insight", pattern: /Insight|fingerprint/i },
  { name: "Evidence", pattern: /Evidence|audit trail/i },
  { name: "Suppliers", pattern: /Suppliers|supplier profiles/i },
  { name: "Performance", pattern: /Performance|trajectory/i },
];

test("all 6 tabs load without blank screens", async ({ page }) => {
  await page.goto("/");

  for (const tab of tabs) {
    await clickTab(page, tab.name);
    await expect(page.locator("main")).not.toBeEmpty();
    await expectAnyText(page, [tab.pattern]);
  }
});

test("Dashboard shows preview data from S2P backend", async ({ page }) => {
  await page.goto("/");

  await expectAnyText(page, [/Exception Queue/i, /exception/i]);
  await expectAnyText(page, [/Conservation Status/i, /conservation/i]);
  await expectAnyText(page, [/GREEN/i, /AMBER/i, /RED/i]);
  await expectAnyText(page, [/Verified decisions/i]);
});

test("full round-trip Dashboard to all screens to Dashboard", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Dashboard/i, /Exception Queue/i]);

  await clickTab(page, "Exception Triage");
  await expectAnyText(page, [/Exception Triage/i, /7 factors/i]);

  await clickTab(page, "Insight");
  await expectAnyText(page, [/Insight/i, /Factor fingerprint/i, /Similar invoices/i]);

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/Evidence/i, /rule lifecycle/i, /audit trail/i]);

  await clickTab(page, "Suppliers");
  await expectAnyText(page, [/Suppliers/i, /OTIF/i, /profile/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Performance/i, /What-if simulator/i, /Operational summary/i]);

  await clickTab(page, "Dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expectAnyText(page, [/Exception Queue/i, /Conservation Status/i]);
});

test("triage select score confirm reward round trip", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");

  await expectAnyText(page, [/Invoice Selector/i, /S2P-INV/i, /queued/i]);
  await page.getByRole("button", { name: /^Score$/i }).first().click();
  await expectAnyText(page, [/Recommendation/i, /Confidence/i]);
  await page.getByRole("button", { name: /Confirm recommendation/i }).first().click();
  await expectAnyText(page, [/Learning Result/i, /Reward/i, /confirm/i, /recorded/i]);
});

test("score learn round trip preserves conservation projection", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");

  await page.getByRole("button", { name: /^Score$/i }).first().click();
  await expectAnyText(page, [/Recommendation/i, /7-Factor Reasoning/i]);
  await page.getByRole("button", { name: /Confirm recommendation/i }).first().click();
  await expectAnyText(page, [/Reward/i, /Learning Result/i]);
  await expectAnyText(page, [/Conservation Projection/i, /Verified/i, /accuracy/i, /penalty 5:1/i]);
});

test("triage to dashboard navigation keeps dashboard preview visible", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");
  await expectAnyText(page, [/Invoice Selector/i, /Score/i]);

  await clickTab(page, "Dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expectAnyText(page, [/Exception Queue/i, /Conservation Status/i]);
});

test("process context persists across reload after scoring", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");
  await page.getByRole("button", { name: /^Score$/i }).first().click();
  await expectAnyText(page, [/Process Context/i, /Celonis/i]);
  await expectAnyText(page, [/Match Invoice/i, /bottleneck/i, /42/i]);

  await page.reload();
  await clickTab(page, "Exception Triage");
  await page.getByRole("button", { name: /^Score$/i }).first().click();
  await expectAnyText(page, [/Process Context/i, /Celonis/i]);
  await expectAnyText(page, [/Match Invoice/i, /bottleneck/i, /42/i]);
});

test("graded financial reward appears as decimal reward", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");

  await page.getByRole("button", { name: /^Score$/i }).first().click();
  await page.getByRole("button", { name: /Confirm recommendation/i }).first().click();

  await expectAnyText(page, [/Reward/i, /Reward raw/i, /\+1\.00|\+0\.[0-9]+|-0\.[0-9]+/]);
});

test("Process-Tech Fusion story spans all S2P screens", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Exception Queue/i, /Process context/i, /Conservation mini-gauge/i]);

  await clickTab(page, "Exception Triage");
  await expectAnyText(page, [/Invoice Selector/i, /7-Factor Reasoning/i, /Process Context/i]);

  await clickTab(page, "Insight");
  await expectAnyText(page, [/Factor fingerprint/i, /Similar invoices/i, /Cross-graph signal/i, /Process signals/i]);

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/Invoice audit trail/i, /Rule lifecycle/i, /Compliance/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Learning trajectory/i, /What-if simulator/i, /Operational summary/i]);
});

test("cross-graph insight shows supplier impact ranking", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Insight");

  await expectAnyText(page, [/Cross-graph signal/i, /Supplier exceptions/i]);
  await expectAnyText(page, [/Supplier/i, /Commodity/i, /Impact score/i, /Aster/i]);
});

test("evidence to performance connects compliance and conservation", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expectAnyText(page, [/Compliance/i, /Flagged/i, /Compliant/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Conservation mini-gauge/i, /penalty 5:1/i, /verified/i]);
});

test("performance what-if shows projected values", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Performance");

  await expectAnyText(page, [/What-if simulator/i, /Projected q/i, /Theta min/i, /Status/i]);
});

test("savings estimate is visible", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Performance");

  await expectAnyText(page, [/Savings estimate/i, /Annual target/i, /\$/i]);
});

test("dashboard to triage drill-down path remains available", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Recent Decisions/i, /S2P-INV/i, /Process context/i]);

  await clickTab(page, "Exception Triage");
  await expectAnyText(page, [/Invoice Selector/i, /Score/i, /queued/i]);
});

test("all S2P screens survive page reload", async ({ page }) => {
  await page.goto("/");
  for (const tab of ["Dashboard", "Insight", "Evidence", "Performance", "Exception Triage"]) {
    await clickTab(page, tab);
    await page.reload();
    await clickTab(page, tab);
    await expect(page.locator("main")).not.toBeEmpty();
    await expectAnyText(page, [new RegExp(tab === "Exception Triage" ? "Exception Triage|Invoice Selector" : tab, "i")]);
  }
});

test("SOC vocabulary is absent from S2P remaining screens", async ({ page }) => {
  await page.goto("/");
  for (const tab of ["Insight", "Evidence", "Performance"]) {
    await clickTab(page, tab);
    await expect(page.getByText(/credential_access/i)).toHaveCount(0);
    await expect(page.getByText(/lateral_movement/i)).toHaveCount(0);
    await expect(page.getByText(/data_exfiltration/i)).toHaveCount(0);
    await expect(page.getByText(/suppress/i)).toHaveCount(0);
  }
});
