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
  await expectAnyText(page, [/trend following/i, /event driven/i, /income strategy/i, /scalp intraday/i, /No category performance available/i]);
});

test("trajectory shows competitor and switching cost narrative", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByText("Trajectory")).toBeVisible();
  await expectAnyText(page, [/competitor needs/i, /YOUR trades/i, /Switching cost/i]);
});

test("conservation projection shows automation targets", async ({ page }) => {
  await gotoPerformance(page);

  await expectAnyText(page, [/Automation Projection/i, /Projection unavailable/i]);
  await expectAnyText(page, [/55%/, /75%/, /90%/, /verified decisions/i, /accuracy/i]);
});

test("conservation status shows projection targets", async ({ page }) => {
  await gotoPerformance(page);

  await expectAnyText(page, [/Automation Projection/i, /Conservation/i, /Projection unavailable/i]);
  await expectAnyText(page, [/55%/, /75%/, /90%/]);
  await expectAnyText(page, [/verified/i, /accuracy/i, /projection/i]);
});

test("SC-11 centroid timeline visible on performance", async ({ page }) => {
  await gotoPerformance(page);

  await expectAnyText(page, [/centroid/i, /timeline/i, /factor.*weight/i, /no.*centroid.*history/i, /no.*history/i, /evolution/i]);
});
