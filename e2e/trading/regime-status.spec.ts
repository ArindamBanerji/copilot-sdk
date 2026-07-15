import { expect, test, type Page } from "@playwright/test";

const FRONTEND = process.env.TRADING_FRONTEND || "http://127.0.0.1:5174";

async function mockRegimeStatus(page: Page) {
  await page.route("**/api/trading/regime-status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        current_regime: "volatile",
        previous_regime: "trending",
        regime_break_active: true,
        decisions_in_new_regime: 5,
        decisions_to_stabilize: 20,
        autonomy_level: "restricted",
        restrictions: ["theta_min tightened 30%", "AE promotions deferred"],
      }),
    });
  });
}

async function gotoPerformance(page: Page) {
  await mockRegimeStatus(page);
  await page.goto(FRONTEND);
  await expect(page.getByRole("heading", { name: "Trading Copilot" })).toBeVisible({ timeout: 20_000 });
  await page.getByRole("button", { name: "Performance" }).click();
  await expect(page.getByTestId("regime-status-panel")).toBeVisible({ timeout: 20_000 });
}

test("regime status panel visible on performance", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByTestId("regime-status-panel")).toBeVisible();
});

test("regime status shows current regime", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByTestId("regime-status-current")).toContainText("trending -> volatile");
});

test("regime break shows restrictions", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByTestId("regime-status-autonomy")).toContainText("restricted");
  await expect(page.getByTestId("regime-status-restrictions")).toContainText("theta_min tightened 30%");
  await expect(page.getByTestId("regime-status-restrictions")).toContainText("AE promotions deferred");
});
