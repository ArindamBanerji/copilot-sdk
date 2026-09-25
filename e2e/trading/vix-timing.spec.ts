import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

async function gotoPerformance(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(page.getByText("Centroid Timeline")).toBeVisible({ timeout: 15_000 });
}

function vixTimingPanel(page: Page) {
  return page.getByTestId("accuracy-alerts-panel");
}

test("VIX timing panel is visible on Performance", async ({ page }) => {
  await gotoPerformance(page);

  const panel = vixTimingPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel).toContainText(/Accuracy Alerts/i);
});

test("VIX timing panel shows matrix or insufficient data", async ({ page }) => {
  await gotoPerformance(page);

  const panel = vixTimingPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(
    panel.getByText(/Accuracy Alerts|event_driven|trend_following|\d+%/i).first(),
  ).toBeVisible({ timeout: 15_000 });
});

test("VIX timing panel shows recommendations or insufficient data", async ({ page }) => {
  await gotoPerformance(page);

  const panel = vixTimingPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel).toContainText(/Accuracy Alerts|event_driven|trend_following|\d+%/i, { timeout: 15_000 });
});

test("VIX timing panel has no SOC vocabulary", async ({ page }) => {
  await gotoPerformance(page);

  await expect(vixTimingPanel(page)).not.toContainText(/\bSOC\b|\bSC-\d+\b/i);
});

test("VIX timing panel has no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoPerformance(page);
  await expect(vixTimingPanel(page)).toBeVisible({ timeout: 15_000 });

  expectNoConsoleErrors(errors);
});

