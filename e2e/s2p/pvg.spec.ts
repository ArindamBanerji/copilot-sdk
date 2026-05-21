import { test, expect } from "@playwright/test";
import { clickTab } from "../helpers/ui";

function main(page: import("@playwright/test").Page) {
  return page.locator("main");
}

function panel(page: import("@playwright/test").Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

test("dashboard shows financial impact", async ({ page }) => {
  await page.goto("/");
  const impact = panel(page, "Financial impact");

  await expect(impact).toContainText(/PVG savings/i);
  await expect(impact).toContainText(/leakage prevented|cycle time saved|auto approve efficiency|unavailable/i);
});

test("insight shows leakage detection", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Insight");

  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
  const leakage = panel(page, "Leakage detection");
  await expect(leakage).toContainText(/PVG at-risk invoices/i);
  await expect(leakage).toContainText(/Total at risk|No invoices currently meet|Leakage data is unavailable|S2P-INV/i);
});

test("performance shows cycle-time signal or unavailable state", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Performance");

  await expect(page.getByRole("heading", { name: "Performance" })).toBeVisible();
  const cycleTime = panel(page, "Cycle-time");
  await expect(cycleTime).toContainText(/Process bottleneck/i);
  await expect(cycleTime).toContainText(/Total median minutes|Bottleneck|Celonis data not configured|Cycle-time data is unavailable/i);
});

test("PVG screens have no SOC vocabulary", async ({ page }) => {
  await page.goto("/");
  for (const tab of ["Dashboard", "Insight", "Performance"]) {
    await clickTab(page, tab);
    await expect(main(page)).not.toContainText(/credential_access/i);
    await expect(main(page)).not.toContainText(/lateral_movement/i);
    await expect(main(page)).not.toContainText(/data_exfiltration/i);
    await expect(main(page)).not.toContainText(/suppress/i);
  }
});
