import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

async function gotoPerformance(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(page.getByText("Performance Summary")).toBeVisible({ timeout: 15_000 });
}

function executionCard(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Execution Quality" }) }).first();
}

test("execution analysis endpoint returns broker stats", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/trading/execution/analysis");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(Array.isArray(data.brokers)).toBeTruthy();
});

test("execution summary endpoint returns object", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/trading/execution/summary");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(typeof data).toBe("object");
  expect(Array.isArray(data.brokers)).toBeTruthy();
});

test("execution quality card renders on Performance tab", async ({ page }) => {
  await gotoPerformance(page);
  await expect(executionCard(page)).toBeVisible({ timeout: 15_000 });
});

test("execution card shows broker comparison or empty state", async ({ page }) => {
  await gotoPerformance(page);
  const card = executionCard(page);
  await expect(card.getByText(/Broker|No execution data yet/i).first()).toBeVisible({ timeout: 15_000 });
});

test("execution card shows savings estimate when multiple brokers", async ({ page }) => {
  await page.route("**/api/trading/execution/summary", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        broker_count: 2,
        best_broker: "ibkr",
        annual_savings_estimate: 1200,
        recommendation: "Switch to ibkr to save about $1,200/year.",
        brokers: [
          { broker: "alpaca", trade_count: 10, avg_slippage: 0.08, fill_rate: 0.8 },
          { broker: "ibkr", trade_count: 10, avg_slippage: 0.02, fill_rate: 0.9 },
        ],
      }),
    });
  });
  await gotoPerformance(page);
  await expect(executionCard(page).getByText(/^Annual savings estimate:/i)).toBeVisible({ timeout: 15_000 });
});
