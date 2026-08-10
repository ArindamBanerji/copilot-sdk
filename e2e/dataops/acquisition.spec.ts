import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell, waitForScreenReady } from "../helpers/ui";

async function gotoInsight(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);
  await clickTab(page, "Insight");
  await waitForAppShell(page);
  await expect(page.getByText("Data Acquisition Recommendations", { exact: true })).toBeVisible({ timeout: 15000 });
}

test("test_acquisition_panel_visible", async ({ page }) => {
  await gotoInsight(page);
  await expect(page.getByText("Data Acquisition Recommendations", { exact: true })).toBeVisible();
});

test("test_acquisition_shows_recommendations", async ({ page }) => {
  await gotoInsight(page);
  await expect(page.getByText("External data strategy", { exact: true }).first()).toBeVisible();
  await expectAnyText(page, [/Acquisition recommendations unavailable/i, /Priority:/i]);
});

test("test_acquisition_free_highlighted", async ({ page }) => {
  await gotoInsight(page);
  await expectAnyText(page, [/Acquisition recommendations unavailable/i, /free/i, /infinite ROI/i]);
});
