import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

const BACKEND = process.env.TRADING_BACKEND || "http://127.0.0.1:8010";
const categories = ["trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"];
const stageText = /Paper trading|Small position|Full position/i;

type PromotionRow = {
  category?: string;
  ready?: boolean;
};

async function gotoPerformance(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(page.getByText("Performance Summary")).toBeVisible({ timeout: 15_000 });
}

test("Promotion dashboard renders on Performance", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByTestId("promotion-dashboard")).toBeVisible({ timeout: 20_000 });
});

test("Dashboard shows all Trading categories", async ({ page }) => {
  await gotoPerformance(page);

  for (const category of categories) {
    await expect(page.getByTestId(`promotion-category-${category}`)).toBeVisible({ timeout: 20_000 });
  }
});

test("Each category shows stage badge", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoPerformance(page);
  await expect(page.getByTestId("promotion-dashboard")).toBeVisible({ timeout: 20_000 });

  for (const category of categories) {
    await expect(page.getByTestId(`promotion-stage-${category}`)).toContainText(stageText, { timeout: 20_000 });
  }
});

test("Sizing cap displayed per category", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoPerformance(page);
  await expect(page.getByTestId("promotion-dashboard")).toBeVisible({ timeout: 20_000 });

  for (const category of categories) {
    await expect(page.getByTestId(`promotion-sizing-${category}`)).toContainText(/% max/i, { timeout: 20_000 });
  }
});

test("Dashboard endpoint returns all categories", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/trading/promotion/dashboard`);
  expect(response.status()).toBe(200);
  const body = await response.json();

  expect(Array.isArray(body)).toBe(true);
  expect(body.length).toBeGreaterThanOrEqual(5);
});

test("Category detail endpoint returns evaluation", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/trading/promotion/trend_following`);
  expect(response.status()).toBe(200);
  const body = await response.json();

  expect(body).toHaveProperty("current_stage");
  expect(body).toHaveProperty("ready");
  expect(body).toHaveProperty("evidence");
  expect(body).toHaveProperty("recommendation");
});

test("Promote rejects when not ready", async ({ request }) => {
  const dashboard = await request.get(`${BACKEND}/api/trading/promotion/dashboard`);
  expect(dashboard.status()).toBe(200);
  const body = await dashboard.json();
  const rows: PromotionRow[] = Array.isArray(body) ? body : [];
  const notReady = rows.find((row) => row.category && !row.ready);
  test.skip(!notReady, "All promotion categories are ready; rejection path is unavailable.");
  if (!notReady?.category) return;

  const response = await request.post(`${BACKEND}/api/trading/promotion/${encodeURIComponent(notReady.category)}/promote`, {
    data: { confirmed_by: "trader" },
  });

  expect(response.status()).toBe(409);
});

test("Recommendation text visible", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByTestId("promotion-dashboard")).toContainText(
    /Ready to promote|Need \d+ more|Fully promoted|decisions needed|Conservation/i,
    { timeout: 20_000 },
  );
});

test("Blockers displayed when not ready", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByTestId("promotion-blockers-trend_following")).toBeVisible({ timeout: 20_000 });
});

test("Promotion history section exists", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByTestId("promotion-history-trend_following")).toBeVisible({ timeout: 20_000 });
});

test("Kitchen language - no enum names", async ({ page }) => {
  await gotoPerformance(page);

  const text = await page.getByTestId("promotion-dashboard").textContent();
  expect(text || "").not.toMatch(/PAPER|SMALL_LIVE|FULL_LIVE/);
});

test("No console errors on promotion dashboard", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoPerformance(page);
  await expect(page.getByTestId("promotion-dashboard")).toBeVisible({ timeout: 20_000 });

  expectNoConsoleErrors(errors);
});
