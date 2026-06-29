import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(page.getByText("Supply Disruption Recovery", { exact: true })).toBeVisible({ timeout: 15000 });
}

test("test_recovery_panel_visible", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText("Supply Disruption Recovery", { exact: true })).toBeVisible();
});

test("test_recovery_shows_status", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText(/recovering|stable|disrupted/i).first()).toBeVisible();
});

test("test_recovery_shows_progress", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText(/Recovery/i).first()).toBeVisible();
  await expect(page.getByText(/\d+%/).first()).toBeVisible();
});
