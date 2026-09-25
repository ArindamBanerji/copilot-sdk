import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

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
  await expect(page.getByTestId("vol-sharpe-card")).toContainText(/Clustering-adjusted Sharpe/i);
  await expect(page.getByTestId("vol-sharpe-card")).toContainText(/Adjusted quality|Evidence: insufficient|Observation data is accumulating/i);
  await expect(page.getByTestId("vol-sharpe-card").getByText(/Evidence: insufficient|accumulating/i).first()).toBeVisible();
});

test("V2 VRP attribution panel renders", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("vrp-attribution-card")).toContainText(/VRP and tail-dependence window/i);
  await expect(page.getByTestId("vrp-attribution-card")).toContainText(/VRP spread|Tail capture|Evidence: insufficient/i);
  await expect(page.getByTestId("vrp-classification")).toContainText(/Edge|Insurance|Neutral|Accumulating|Evidence/i);
});

test("V1 and V2 panels use decision-quality and volatility language", async ({ page }) => {
  await gotoAnalysis(page);
  const quality = page.getByTestId("vol-sharpe-card");
  const vrp = page.getByTestId("vrp-attribution-card");

  await expect(quality).toContainText(/Clustering-adjusted Sharpe|Adjusted quality/i);
  await expect(vrp).toContainText(/Volatility Risk Premium|VRP/i);
  await expect(page.getByTestId("vrp-classification")).toContainText(/Edge|Insurance|Neutral|Accumulating|Evidence/i);
});

test("volatility cards show provenance", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("vol-sharpe-card").getByText(/Evidence: insufficient|accumulating/i).first()).toBeVisible();
  await expect(page.getByTestId("vrp-attribution-card").getByText(/Evidence: insufficient|accumulating|Neutral/i).first()).toBeVisible();
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
  await expect(page.getByTestId("vrp-attribution-card")).toContainText(/VRP|tail-dependence|window/i);
});

test("V6 dispersion follow-rate panel renders", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("dispersion-follow-card")).toContainText(/Dispersion Follow-Rate/i);
});

test("V7 tail bets panel renders", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("tail-bets-card")).toContainText(/Effective bets in tail/i);
});

test("TRD-V1: clustering adjustment factor is visible", async ({ page }) => {
  await gotoAnalysis(page);
  const panel = page.getByTestId("vol-sharpe-card");
  await expect(panel).toBeVisible({ timeout: 20_000 });
  await expect(panel).toContainText(/Clustering-adjusted Sharpe/i);
  await expect(panel).toContainText(/Adjusted quality/i);
});

test("TRD-V1: tail-risk indicator is present", async ({ page }) => {
  await gotoAnalysis(page);
  await expectAnyText(page, [/VRP|tail-dependence/i, /Effective bets in tail/i], { timeout: 20_000 });
});

test("TRD-V1: short-vol illusion detection warning is shown", async ({ page }) => {
  await gotoAnalysis(page);
  const panel = page.getByTestId("volatility-panel");
  await expect(panel).toBeVisible({ timeout: 20_000 });
  await expect(panel).toContainText(/clustering adjustment/i);
  await expect(panel).toContainText(/Diagnostic only|Observation/i);
});

