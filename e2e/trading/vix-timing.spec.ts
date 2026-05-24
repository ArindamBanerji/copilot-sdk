import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";

async function gotoPerformance(page: Page) {
  await page.goto("/");
  await clickTab(page, "Performance");
  await expect(page.getByText("Performance Summary")).toBeVisible({ timeout: 15_000 });
}

function vixTimingPanel(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "VIX-Aware Hold Timing" }) }).first();
}

test("VIX timing panel is visible on Performance", async ({ page }) => {
  await gotoPerformance(page);

  const panel = vixTimingPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel.getByText("Performance analysis")).toBeVisible();
});

test("VIX timing panel shows matrix or insufficient data", async ({ page }) => {
  await gotoPerformance(page);

  const panel = vixTimingPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(
    panel.getByText(/Hold period|Low VIX|Medium VIX|High VIX|Score more trades with entry\/exit times|unavailable/i).first(),
  ).toBeVisible({ timeout: 15_000 });
});

test("VIX timing panel shows recommendations or insufficient data", async ({ page }) => {
  await gotoPerformance(page);

  const panel = vixTimingPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel.getByRole("heading", { name: "Performance Observations" })).toBeVisible({ timeout: 15_000 });
  await expect(
    panel
      .getByText(/Insufficient VIX timing history|Score more trades with entry\/exit times|No VIX timing observations|outperformed|performed/i)
      .first(),
  ).toBeVisible({ timeout: 15_000 });
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
