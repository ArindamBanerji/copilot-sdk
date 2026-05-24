import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";

async function gotoAnalysis(page: Page) {
  await page.goto("/");
  await clickTab(page, "Analysis");
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
  const alertState = panel.getByText(/Alerts|No active correlation alerts|critical|warning/i).first();
  const insufficientState = panel
    .getByText(/Need at least 2 tickers|At least two tickers are required|Fewer than two tickers|Insufficient price history|yfinance is unavailable|numpy is unavailable|Correlation monitoring unavailable/i)
    .first();

  await expect(alertState.or(insufficientState)).toBeVisible({ timeout: 15_000 });
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
