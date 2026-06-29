import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(page.getByText("Payment Timing Intelligence", { exact: true })).toBeVisible({ timeout: 15000 });
}

test("test_payment_panel_visible", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText("Payment Timing Intelligence", { exact: true })).toBeVisible();
});

test("test_payment_shows_dpo", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText("DPO", { exact: true })).toBeVisible();
});

test("test_payment_shows_opportunity", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText(/Annual opportunity/i).first()).toBeVisible();
  await expect(page.getByText(/\$[\d,]+/).first()).toBeVisible();
});
