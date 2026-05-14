import { test, expect } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

test("Dashboard loads with exception queue", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expectAnyText(page, [/Exception Queue/i, /exception/i]);
  await expectAnyText(page, [/Conservation Status/i, /conservation/i]);
});

test("Exception Triage screen loads", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");

  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
  await expectAnyText(page, [/triage/i, /exception/i, /invoice/i, /Phase 1/i]);
});

test("Insight screen loads", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Insight");

  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
  await expectAnyText(page, [/profile/i, /fingerprint/i, /Phase 1/i]);
});

test("Evidence screen loads", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Evidence");

  await expect(page.getByRole("heading", { name: "Evidence", exact: true })).toBeVisible();
  await expectAnyText(page, [/governance/i, /audit/i, /Phase 1/i]);
});

test("Suppliers screen loads with profiles", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Suppliers");

  await expect(page.getByRole("heading", { name: "Suppliers" })).toBeVisible();
  await expectAnyText(page, [/supplier/i, /profile/i, /OTIF/i]);
  await expectAnyText(page, [/Chen-Lin/i, /Exception rate/i, /No supplier profiles available/i]);
});

test("Performance screen loads", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Performance");

  await expect(page.getByRole("heading", { name: "Performance" })).toBeVisible();
  await expectAnyText(page, [/performance/i, /trajectory/i, /IKS/i, /Phase 1/i]);
});
