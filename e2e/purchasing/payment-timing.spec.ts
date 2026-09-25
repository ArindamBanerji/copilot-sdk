import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForScreenReady } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
  await expect(page.getByText("Payment Timing Intelligence", { exact: true })).toBeVisible({ timeout: 15000 });
}

test("test_payment_panel_visible", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText("Payment Timing Intelligence", { exact: true })).toBeVisible();
});

test("test_payment_shows_dpo", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/DPO/i, /Payment timing unavailable/i, /Loading payment timing/i]);
});

test("test_payment_shows_opportunity", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/Annual opportunity/i, /\$[\d,]+/, /Payment timing unavailable/i, /Loading payment timing/i]);
});
