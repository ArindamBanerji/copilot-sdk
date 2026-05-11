import { test, expect } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

const tabs = [
  { name: "Dashboard", pattern: /Dashboard|Exception Queue/i },
  { name: "Exception Triage", pattern: /Exception Triage|verification reason codes/i },
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
  await expectAnyText(page, [/Insight/i, /decision explorer/i, /centroid explorer/i]);

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/Evidence/i, /rule lifecycle/i, /audit trail/i]);

  await clickTab(page, "Suppliers");
  await expectAnyText(page, [/Suppliers/i, /OTIF/i, /profile/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Performance/i, /conservation projection/i, /switching cost/i]);

  await clickTab(page, "Dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expectAnyText(page, [/Exception Queue/i, /Conservation Status/i]);
});
