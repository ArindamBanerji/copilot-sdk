import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, expectTrajectoryOrEmpty } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Performance");
  // Wait for loading to finish, then check content (not tab button)
  await page.waitForTimeout(1000);
  await expectAnyText(page, [/trajectory/i, /performance/i, /IKS/i, /loading/i]);
}

test("trajectory chart renders", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByText("Trajectory")).toBeVisible();
  await expectAnyText(page, [/Current IKS/i, /Win Rate/i, /Decisions/i]);
  await expectTrajectoryOrEmpty(page);
});

test("cost impact visible", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByText("Cost impact")).toBeVisible();
  await expect(page.getByText("Waste and stockouts are now measurable")).toBeVisible();
  await expectAnyText(page, [/Waste reduction/i, /Stockout events/i, /Stockout cost/i, /\$\d[\d,]*/]);
});

test("trajectory shows switching cost narrative", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByText("Trajectory")).toBeVisible();
  await expectAnyText(page, [/orders to learn/i, /years of gut instinct/i, /Switching cost/i]);
});

test("conservation projection shows automation targets", async ({ page }) => {
  await gotoPerformance(page);

  await expectAnyText(page, [/Automation Projection/i, /Projection unavailable/i]);
  await expectAnyText(page, [/55%/, /75%/, /90%/, /verified decisions/i, /accuracy/i]);
});
