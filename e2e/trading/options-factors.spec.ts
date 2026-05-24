import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";

async function openLogTrade(page: Page) {
  await page.goto("/");
  await clickTab(page, "Log Trade");
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();
}

function optionsPanel(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Options Factors" }) }).first();
}

async function selectIncomeStrategy(page: Page) {
  const thesis = page.locator("section", { has: page.getByRole("heading", { name: "Trade Thesis" }) }).first();
  await thesis.getByLabel("Category").selectOption("income_strategy");
}

test("Options factors panel appears for income strategy context", async ({ page }) => {
  await openLogTrade(page);
  await selectIncomeStrategy(page);

  const panel = optionsPanel(page);
  await expect(panel).toBeVisible();
  await expect(panel.getByText("Analytics-only - not scored by the engine.")).toBeVisible();
  await expect(panel.getByText("No options data available.")).toBeVisible();
});

test("Options factors empty state is stable before options data exists", async ({ page }) => {
  await openLogTrade(page);
  await selectIncomeStrategy(page);

  const panel = optionsPanel(page);
  await expect(panel.getByText("No options data available.")).toBeVisible();
  await expect(panel.getByText(/IV\/RV ratio|Greeks exposure|Theta efficiency/i)).toHaveCount(0);
});

test("Options factors label does not imply engine scoring", async ({ page }) => {
  await openLogTrade(page);
  await selectIncomeStrategy(page);

  const panel = optionsPanel(page);
  await expect(panel).toBeVisible();
  await expect(panel.getByText("analytics-only").first()).toBeVisible();
  await expect(panel.getByText(/not scored by the engine/i)).toBeVisible();
});

test("Options factors panel has no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await openLogTrade(page);
  await selectIncomeStrategy(page);
  await expect(optionsPanel(page)).toBeVisible();

  expectNoConsoleErrors(errors);
});


