import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expect(page.getByTestId("vol-analytics-grid")).toBeVisible({ timeout: 20_000 });
}

test("V1 clustering-adjusted Sharpe panel renders", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("vol-sharpe-card")).toContainText(/Clustering-Adjusted Sharpe/i);
});

test("V2 VRP attribution panel renders", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("vrp-attribution-card")).toContainText(/VRP Edge or Insurance/i);
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
