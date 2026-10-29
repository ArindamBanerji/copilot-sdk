import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function openPerformanceTab(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Centroid Timeline/i, /Accuracy Alerts/i, /Decision Explorer/i]);
}

async function openDashboard(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expectAnyText(page, [/Dashboard/i, /Decision History/i]);
}

function archetypeComparisonCard(page: Page) {
  return page.getByRole("heading", { name: "Archetype Advantage", exact: true }).locator("../../..");
}

async function mockTransferStatus(page: Page) {
  await page.route("**/api/transfer/status", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        warm_started: true,
        source_copilot: "soc",
        patterns_transferred: 3,
        categories_transferred: 3,
        source_accuracy: 0.84,
        provenance: "transfer",
      }),
    });
  });
}

async function mockArchetypeCurrent(page: Page) {
  await page.route("**/api/archetypes?domain=trading", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify([
        {
          name: "financial_services",
          domain: "trading",
          description: "Trading archetype for financial services",
          categories: ["trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"],
          actions: ["strong_execution", "partial_execution", "poor_execution"],
          factors: [
            "signal_alignment",
            "market_regime",
            "position_sizing",
            "timing_quality",
            "risk_reward_actual",
            "emotional_indicator",
          ],
        },
      ]),
    });
  });
  await page.route("**/api/archetypes/current", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ current: "financial_services" }),
    });
  });
  await page.route("**/api/archetypes/financial_services", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        name: "financial_services",
        domain: "trading",
        description: "Trading archetype for financial services",
        expected_initial_accuracy: 0.72,
        categories: ["trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"],
        actions: ["strong_execution", "partial_execution", "poor_execution"],
        factors: [
          "signal_alignment",
          "market_regime",
          "position_sizing",
          "timing_quality",
          "risk_reward_actual",
          "emotional_indicator",
        ],
        shape: [5, 3, 6],
        centroids: [[0.7, 0.6, 0.8, 0.5, 0.9, 0.7]],
        penalty_ratio: 2.0,
        calibration_note: "Calibrated for financial services trading",
        calibration_notes: ["Deterministic Playwright fixture"],
      }),
    });
  });
}

test("transfer comparison card shows on Performance after transfer status", async ({ page }) => {
  await mockTransferStatus(page);
  await openPerformanceTab(page);
  await expect(page.getByRole("heading", { name: "Transfer Impact" })).toBeVisible();
});

test("transfer comparison card shows baseline vs post-transfer", async ({ page }) => {
  await mockTransferStatus(page);
  await openPerformanceTab(page);
  await expectAnyText(page, [/Before transfer/i, /After transfer/i, /Estimated calibration saved/i]);
});

test("archetype comparison card shows on Dashboard", async ({ page }) => {
  await mockArchetypeCurrent(page);
  await openDashboard(page);
  await expect(archetypeComparisonCard(page)).toBeVisible();
});

test("archetype comparison shows generic vs selected", async ({ page }) => {
  await mockArchetypeCurrent(page);
  await openDashboard(page);
  await expect(archetypeComparisonCard(page)).toContainText(/Generic start.*Archetype start.*Estimated head start/is);
});

test("first-run suggestion hidden when decisions exist", async ({ page }) => {
  await openDashboard(page);
  await expect(page.getByRole("heading", { name: "Get started faster" })).not.toBeVisible();
});

test("first-run suggestion browse button hidden when decisions exist", async ({ page }) => {
  await openDashboard(page);
  await expect(page.getByRole("button", { name: "Browse Industry Templates" })).not.toBeVisible();
});

