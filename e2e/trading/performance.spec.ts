import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, expectTrajectoryOrEmpty } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Performance");
  await expect(page.getByText("Performance Summary")).toBeVisible();
}

test("trajectory chart renders", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByText("Trajectory")).toBeVisible();
  await expectAnyText(page, [/Current IKS/i, /Win Rate/i, /Decisions/i]);
  await expectTrajectoryOrEmpty(page);
});

test("rolling metrics visible", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByText("Rolling 10")).toBeVisible();
  await expectAnyText(page, [/Recent win rate/i, /Rolling P&L/i, /No rolling metrics available/i]);
});

test("category performance shows categories", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByText("Category Performance")).toBeVisible();
  await expectAnyText(page, [/equity/i, /crypto/i, /options/i, /etf/i, /No category performance available/i]);
});
