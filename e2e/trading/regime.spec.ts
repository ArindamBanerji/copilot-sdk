import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";

function regimePanel(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Market Regime" }) }).first();
}

test("Regime badge is visible on Dashboard", async ({ page }) => {
  await page.goto("/");

  const panel = regimePanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel.getByText(/TRENDING|RANGING|VOLATILE/i).first()).toBeVisible();
});

test("Regime panel shows VIX and source context", async ({ page }) => {
  await page.goto("/");

  const panel = regimePanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel.getByText("VIX", { exact: true })).toBeVisible();
  await expect(panel.getByText("ADX", { exact: true })).toBeVisible();
  await expect(panel.getByText("Source", { exact: true })).toBeVisible();
  await expect(panel.getByText(/Default regime context|default|cached|yfinance/i).first()).toBeVisible({ timeout: 15_000 });
});

test("Regime panel handles recommendation or empty accuracy state", async ({ page }) => {
  await page.goto("/");

  const panel = regimePanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(
    panel
      .getByText(/Score more trades to build regime accuracy|increase|reduce|hold|accuracy/i)
      .first(),
  ).toBeVisible();
});

test("Regime panel has no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await page.goto("/");
  await expect(regimePanel(page)).toBeVisible({ timeout: 15_000 });

  expectNoConsoleErrors(errors);
});
