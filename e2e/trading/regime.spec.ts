import { expect, test, type Page } from "@playwright/test";

const FRONTEND = process.env.TRADING_FRONTEND || "http://127.0.0.1:5174";
const BACKEND = process.env.TRADING_BACKEND || "http://127.0.0.1:8010";
const REGIME_TEXT = /Trending market|Ranging market|Volatile market/i;
const RAW_REGIMES = ["trending", "ranging", "volatile"];

async function gotoAnalysis(page: Page) {
  await page.goto(FRONTEND);
  await expect(page.getByRole("heading", { name: "Trading Copilot" })).toBeVisible({ timeout: 20_000 });
  await page.getByRole("button", { name: "Analysis" }).click();
  await expect(page.getByRole("main")).not.toBeEmpty({ timeout: 20_000 });
}

test("Analysis tab loads after regime addition", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(page.getByRole("main")).toContainText(/Market Regime|Signal Trust Analysis/i);
});

test("regime panel renders on mount", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(page.getByTestId("regime-panel")).toBeVisible({ timeout: 20_000 });
});

test("regime badge shows current regime", async ({ page }) => {
  await gotoAnalysis(page);

  const badge = page.getByTestId("regime-badge");
  await expect(badge).toBeVisible({ timeout: 20_000 });
  await expect(badge).toContainText(REGIME_TEXT);
});

test("regime confidence displayed", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(page.getByTestId("regime-confidence")).toBeVisible({ timeout: 20_000 });
});

test("regime recommendation displayed", async ({ page }) => {
  await gotoAnalysis(page);

  const recommendation = page.getByTestId("regime-recommendation");
  await expect(recommendation).toBeVisible({ timeout: 20_000 });
  expect((await recommendation.textContent())?.trim().length).toBeGreaterThan(0);
});

test("regime performance section renders", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(page.getByTestId("regime-performance")).toBeVisible({ timeout: 20_000 });
});

test("regime history section renders", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(page.getByTestId("regime-history")).toBeVisible({ timeout: 20_000 });
});

test("regime current endpoint returns valid data", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/trading/regime/current`);
  expect(response.status()).toBe(200);
  const body = await response.json();

  expect(RAW_REGIMES).toContain(body.regime);
  expect(body).toHaveProperty("confidence");
  expect(body).toHaveProperty("vix");
  expect(body).toHaveProperty("adx");
});

test("regime history endpoint returns array", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/trading/regime/history?days=90`);
  expect(response.status()).toBe(200);

  expect(Array.isArray(await response.json())).toBe(true);
});

test("regime performance endpoint returns data", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/trading/regime/performance`);
  expect(response.status()).toBe(200);
  const body = await response.json();

  expect(body).toHaveProperty("per_regime_accuracy");
});

test("regime recommendation endpoint returns data", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/trading/regime/recommendation`);
  expect(response.status()).toBe(200);
  const body = await response.json();

  expect(body).toHaveProperty("current_regime");
  expect(body).toHaveProperty("shifts");
});

test("no console errors on regime panel", async ({ page }) => {
  const unexpected: string[] = [];
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    const text = message.text();
    if (/Failed to load|fetch|favicon|ResizeObserver/i.test(text)) return;
    unexpected.push(text);
  });

  await gotoAnalysis(page);
  await expect(page.getByTestId("regime-panel")).toBeVisible({ timeout: 20_000 });

  expect(unexpected).toEqual([]);
});
