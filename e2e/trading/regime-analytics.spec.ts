import { test, expect, type APIRequestContext } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";

const FRONTEND = process.env.TRADING_FRONTEND || "http://127.0.0.1:5174";
const BACKEND = process.env.TRADING_BACKEND || "http://127.0.0.1:8010";
const TRADING_FACTORS = {
  signal_alignment: 0.82,
  market_regime: 0.88,
  position_sizing: 0.76,
  timing_quality: 0.34,
  risk_reward_actual: 0.67,
  emotional_indicator: 0.71,
  signal_confidence: 0.5,
  options_delta_exposure: 0.5,
  options_iv_percentile: 0.5,
  options_gamma_risk: 0.5,
};

async function isTradingHealthy(request: APIRequestContext): Promise<boolean> {
  const health = await request.get(`${BACKEND}/health`, { timeout: 5_000 }).catch((error) => {
    console.debug("Trading health check unavailable", error);
    return null;
  });
  return health?.ok() === true;
}

test.beforeEach(async ({ request }) => {
  test.skip(!(await isTradingHealthy(request)), "Trading backend is not running");
});

async function gotoRegimeAnalytics(page: import("@playwright/test").Page) {
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(page.getByTestId("regime-analytics-panel")).toBeVisible({ timeout: 20_000 });
}

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);
}

test("test_regime_analytics_panel_on_performance", async ({ page }) => {
  await gotoRegimeAnalytics(page);
  await expect(page.getByTestId("regime-analytics-panel")).toContainText(/Per-Regime Decision Quality/i);
});

test("test_regime_analytics_shows_per_regime_accuracy", async ({ page, request }) => {
  const response = await request.get(`${BACKEND}/api/trading/regime-analytics`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty("regimes");

  await gotoRegimeAnalytics(page);
  await expect(page.getByTestId("regime-analytics-panel")).toContainText(/Accuracy:/i);
  await expect(page.getByTestId("regime-analytics-panel")).toContainText(/Trending|Volatile|Ranging/i);
});

test("test_regime_panel_shows_regime_name", async ({ page }) => {
  await gotoAnalysis(page);

  const panel = page.getByTestId("regime-panel");
  await expect(panel).toBeVisible({ timeout: 20_000 });
  await expect(panel).toContainText(/trending|ranging|volatile/i);
});

test("test_regime_panel_shows_hurst", async ({ page, request }) => {
  const response = await request.get(`${BACKEND}/api/trading/regime/current`);
  expect(response.status()).toBe(200);
  const body = (await response.json()) as Record<string, unknown>;
  const hurst = Number(body.hurst);
  if (!Number.isFinite(hurst)) {
    console.debug("Regime current response did not include finite hurst", body);
  }
  expect(hurst).toBeGreaterThanOrEqual(0);
  expect(hurst).toBeLessThanOrEqual(1);

  await gotoAnalysis(page);
  const hurstEl = page.getByTestId("regime-hurst");
  await expect(hurstEl).toBeVisible({ timeout: 20_000 });
});

test("test_score_response_includes_regime", async ({ request }) => {
  let response = await request.post(`${BACKEND}/api/trading/score`, {
    data: { category: "trend_following", factors: TRADING_FACTORS },
  });
  if (response.status() === 404 || response.status() === 405) {
    console.debug(`/api/trading/score returned ${response.status()}, falling back to /api/score`);
    response = await request.post(`${BACKEND}/api/score`, {
      data: { category: "trend_following", factors: TRADING_FACTORS },
    });
  }

  expect(response.status()).toBe(200);
  const body = (await response.json()) as Record<string, unknown>;
  expect(body).toHaveProperty("regime_context");
  const context = body.regime_context as Record<string, unknown>;
  expect(["trending", "ranging", "volatile"]).toContain(context.regime);
});
