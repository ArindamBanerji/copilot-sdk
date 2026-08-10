import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForScreenReady } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
}

test("WeeklyReportPanel visible on Performance tab", async ({ page }) => {
  await gotoPerformance(page);
  const panel = page.getByTestId("weekly-report-panel");
  await panel.scrollIntoViewIfNeeded();
  await expect(panel).toBeVisible();
  await expect(panel.getByText("Weekly Report")).toBeVisible();
});

test("WeeklyReportPanel renders dollar amounts", async ({ page }) => {
  await gotoPerformance(page);
  const panel = page.getByTestId("weekly-report-panel");
  await panel.scrollIntoViewIfNeeded();
  await expect(panel.getByText(/\$[0-9,]+/).first()).toBeVisible();
});

test("WeeklyReportPanel uses kitchen language", async ({ page }) => {
  await gotoPerformance(page);
  const panel = page.getByTestId("weekly-report-panel");
  await panel.scrollIntoViewIfNeeded();
  await expect(panel).toContainText("Found");
  await expect(panel).toContainText("Prevented");
  await expect(panel).toContainText("Flagged");
  await expect(panel).not.toContainText(/recovered|optimized|analyzed/i);
});
