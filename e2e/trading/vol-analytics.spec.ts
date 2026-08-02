import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

const BACKEND = process.env.TRADING_BACKEND || "http://127.0.0.1:8010";

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expect(page.getByTestId("vol-analytics-grid")).toBeVisible({ timeout: 20_000 });
}

test("V1 risk-adjusted quality panel renders", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("vol-sharpe-card")).toContainText(/Risk-Adjusted Decision Quality/i);
  await expect(page.getByTestId("vol-sharpe-card")).toContainText(/By market condition|Accumulating decisions/i);
  await expect(page.getByTestId("vol-sharpe-card").getByText(/measured|accumulating/i).first()).toBeVisible();
});

test("V2 VRP attribution panel renders", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("vrp-attribution-card")).toContainText(/VRP Edge or Insurance/i);
  await expect(page.getByTestId("vrp-attribution-card")).toContainText(/Average IV-RV spread|Insufficient volatility data/i);
  await expect(page.getByTestId("vrp-classification")).toContainText(/Edge|Insurance|Neutral|Accumulating/i);
});

test("V1 and V2 panels use decision-quality and volatility language", async ({ page }) => {
  await gotoAnalysis(page);
  const quality = page.getByTestId("vol-sharpe-card");
  const vrp = page.getByTestId("vrp-attribution-card");

  await expect(quality).not.toContainText(/Sharpe/i);
  await expect(quality).toContainText(/Market condition|Accumulating decisions/i);
  await expect(vrp).toContainText(/Volatility Risk Premium|VRP/i);
  await expect(page.getByTestId("vrp-classification")).toContainText(/Edge|Insurance|Neutral|Accumulating/i);
});

test("volatility cards show provenance", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("vol-sharpe-card").getByText(/accumulating|measured/i).first()).toBeVisible();
  await expect(page.getByTestId("vrp-attribution-card").getByText(/accumulating|measured|instrument validated/i).first()).toBeVisible();
});

test("V1 endpoint returns cluster data", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/trading/analytics/vol-sharpe`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(Array.isArray(body.clusters)).toBe(true);
});

test("V2 endpoint returns a volatility-data state", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/trading/analytics/vrp-attribution`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(["measured", "accumulating", "instrument_validated"]).toContain(body.status);
});

test("V5 regime VRP panel renders", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("regime-vrp-card")).toContainText(/Regime-Conditioned Rich\/Cheap/i);
});

test("V6 dispersion follow-rate panel renders", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("dispersion-follow-card")).toContainText(/Dispersion Follow-Rate/i);
});

test("V7 tail bets panel renders", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("tail-bets-card")).toContainText(/Effective Bets in a Tail/i);
});
