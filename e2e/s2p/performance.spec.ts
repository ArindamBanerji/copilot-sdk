import { test, expect, type Page } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

async function openPerformance(page: Page) {
  await page.goto("/");
  await clickTab(page, "Performance");
  await expect(page.getByRole("heading", { name: "Performance" })).toBeVisible();
}

test("trajectory chart or empty learning curve renders", async ({ page }) => {
  await openPerformance(page);

  await expectAnyText(page, [/Learning trajectory/i, /Centroid checkpoints/i, /No centroid trajectory/i]);
});

test("conservation shows penalty verified or accuracy", async ({ page }) => {
  await openPerformance(page);

  await expectAnyText(page, [/Conservation mini-gauge/i, /penalty 5:1/i, /verified/i, /accuracy/i]);
});

test("what-if simulator has controls", async ({ page }) => {
  await openPerformance(page);

  await expectAnyText(page, [/What-if simulator/i, /Projected conservation/i]);
  await expect(page.getByLabel(/Additional correct/i)).toBeVisible();
  await expect(page.getByLabel(/Additional incorrect/i)).toBeVisible();
});

test("operational summary shows metrics and savings", async ({ page }) => {
  await openPerformance(page);

  await expectAnyText(page, [/Operational summary/i, /Learning, approvals, savings/i]);
  await expectAnyText(page, [/Scored/i, /Accuracy/i, /Auto approve/i, /Savings estimate/i, /Annual target/i]);
});

test("dashboard mini process context shows bottleneck", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expectAnyText(page, [/Process context/i, /Celonis bottleneck/i]);
  await expectAnyText(page, [/Match Invoice/i, /bottleneck/i, /50 invoice/i]);
});
