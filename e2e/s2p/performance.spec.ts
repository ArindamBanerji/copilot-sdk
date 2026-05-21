import { test, expect, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function openPerformance(page: Page) {
  await page.goto("/");
  await clickTab(page, "Performance");
  await expect(page.getByRole("heading", { name: "Performance" })).toBeVisible();
}

function panel(page: Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

test("trajectory chart or empty learning curve renders", async ({ page }) => {
  await openPerformance(page);

  await expect(panel(page, "Learning trajectory")).toContainText(/Centroid checkpoints|No centroid trajectory/i);
});

test("conservation shows penalty verified or accuracy", async ({ page }) => {
  await openPerformance(page);

  await expect(panel(page, "Conservation mini-gauge")).toContainText(/penalty 5:1|verified|accuracy/i);
});

test("what-if simulator has controls", async ({ page }) => {
  await openPerformance(page);

  await expect(panel(page, "What-if simulator")).toContainText(/Projected conservation/i);
  await expect(page.getByLabel(/Additional correct/i)).toBeVisible();
  await expect(page.getByLabel(/Additional incorrect/i)).toBeVisible();
});

test("operational summary shows metrics and savings", async ({ page }) => {
  await openPerformance(page);

  const summary = panel(page, "Operational summary");
  await expect(summary).toContainText(/Learning, approvals, savings/i);
  await expect(summary).toContainText(/Scored|Accuracy|Auto approve|Savings estimate|Annual target/i);
});

test("dashboard mini process context shows bottleneck", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  const process = panel(page, "Celonis bottleneck");
  await expect(process).toContainText(/Process context/i);
  await expect(process).toContainText(/Match Invoice|bottleneck|50 invoice/i);
});
