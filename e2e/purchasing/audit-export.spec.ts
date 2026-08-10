import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForScreenReady } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
  await expect(page.getByText("Audit & Compliance Pack", { exact: true })).toBeVisible({ timeout: 15000 });
}

test("test_audit_panel_visible", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText("Audit & Compliance Pack", { exact: true })).toBeVisible();
});

test("test_audit_shows_decision_count", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText("Total decisions", { exact: true })).toBeVisible();
  await expect(page.getByText(/\b842\b/).first()).toBeVisible();
});

test("test_audit_export_buttons", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByRole("link", { name: "Download JSON" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Download CSV" })).toBeVisible();
});
