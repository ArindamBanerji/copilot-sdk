import { test, expect } from "@playwright/test";
import { checkBackendHealth, checkPreseedActive, copilotUrl, navigateToTab } from "./demo-fixture";

test.describe.serial("Trader Demo Cut - 3 beats", () => {
  test.beforeAll(async ({ request }) => {
    test.skip(!(await checkPreseedActive(request, "trading")), "Demo preseed is not active: Trading IKS is zero");
  });

  test("TR1: Dashboard shows archetype and decision count", async ({ page, request }) => {
    test.skip(!(await checkBackendHealth(request, "trading")), "Trading backend is not running");
    await page.goto(copilotUrl("trading"));
    await navigateToTab(page, "Dashboard");

    await expect(page.getByText(/archetype/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/decision|trade/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/\b\d+\b/).first()).toBeVisible({ timeout: 20_000 });
  });

  test("TR2: Analysis shows Trust Radar, YOUR TWO SELVES, and numeric data", async ({ page, request }) => {
    test.skip(!(await checkBackendHealth(request, "trading")), "Trading backend is not running");
    await page.goto(copilotUrl("trading"));
    await navigateToTab(page, "Analysis");

    await expect(page.getByText(/Signal Trust Analysis|Trust Radar/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("YOUR TWO SELVES")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/\d+(\.\d+)?%|\b0\.\d+\b|\b\d+\b/).first()).toBeVisible({ timeout: 20_000 });
  });

  test("TR3: Performance shows evolution, trajectory IKS, and conservation", async ({ page, request }) => {
    test.skip(!(await checkBackendHealth(request, "trading")), "Trading backend is not running");
    await page.goto(copilotUrl("trading"));
    await navigateToTab(page, "Performance");

    await expect(page.getByText(/variant|evolution|shadow tested|promotion/i).first()).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByText(/trajectory|IKS/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/conservation|GREEN|AMBER|RED/i).first()).toBeVisible({ timeout: 20_000 });
  });
});
