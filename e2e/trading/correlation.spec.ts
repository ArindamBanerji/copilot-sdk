import { test, expect, type APIRequestContext, type Page } from "@playwright/test";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

const FRONTEND = process.env.TRADING_FRONTEND ?? "http://127.0.0.1:5174";
const BACKEND = process.env.TRADING_BACKEND ?? "http://127.0.0.1:8010";

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

async function gotoAnalysis(page: Page) {
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expect(page.getByText("YOUR TWO SELVES")).toBeVisible({ timeout: 15_000 });
}

function correlationPanel(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Cross-Position Correlation" }) }).first();
}

test("Correlation panel is visible on Analysis", async ({ page }) => {
  await gotoAnalysis(page);

  const panel = correlationPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel.getByText("Correlation monitoring")).toBeVisible();
  await expect(panel.getByText(/concentration risk/i)).toBeVisible();
});

test("Correlation panel shows pairs or insufficient data", async ({ page }) => {
  await gotoAnalysis(page);

  const panel = correlationPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(
    panel
      .getByText(/Top correlated pairs|Need at least 2 tickers|fewer than 2 tickers|insufficient|unavailable|yfinance is unavailable|numpy is unavailable/i)
      .first(),
  ).toBeVisible({ timeout: 15_000 });
});

test("Correlation panel shows alerts or no-alert state", async ({ page }) => {
  await gotoAnalysis(page);

  const panel = correlationPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel).not.toContainText(/Loading correlation monitor/i, { timeout: 30_000 });
  const alertState = panel.getByText(/Alerts|No active correlation alerts|critical|warning/i).first();
  const insufficientState = panel
    .getByText(/Need at least 2 tickers|At least two tickers are required|Fewer than two tickers|Insufficient price history|yfinance is unavailable|numpy is unavailable|Correlation monitoring unavailable/i)
    .first();

  await expect(alertState.or(insufficientState)).toBeVisible({ timeout: 30_000 });
});

test("Correlation panel has no SOC vocabulary", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(correlationPanel(page)).not.toContainText(/\bSOC\b|\bSC-\d+\b/i);
});

test("Correlation panel has no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoAnalysis(page);
  await expect(correlationPanel(page)).toBeVisible({ timeout: 15_000 });

  expectNoConsoleErrors(errors);
});

test("test_correlation_shows_effective_multiplier", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoAnalysis(page);

  const panel = correlationPanel(page);
  await expect(panel).toBeVisible({ timeout: 30_000 });
  await expect(page.getByTestId("tail-bets-card")).toContainText(/effective|multiplier|exposure/i, { timeout: 30_000 });
});
