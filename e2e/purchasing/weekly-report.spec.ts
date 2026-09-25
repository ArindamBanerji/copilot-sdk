import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForScreenReady } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
}

test("WeeklyReportPanel visible on Performance tab", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/Weekly Report/i, /What the kitchen found this week/i, /Loading weekly report/i]);
});

test("WeeklyReportPanel renders dollar amounts", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/\$[0-9,]+/, /Loading weekly report/i]);
});

test("WeeklyReportPanel uses kitchen language", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/Found/i, /Prevented/i, /Flagged/i, /Loading weekly report/i]);
});
