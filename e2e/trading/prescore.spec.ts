import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";

async function openLogTrade(page: Page) {
  await page.goto("/");
  await clickTab(page, "Log Trade");
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();
}

function preScorePanel(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Pre-Trade Score" }) }).first();
}

test("Pre-score form is visible on Log Trade", async ({ page }) => {
  await openLogTrade(page);

  const panel = preScorePanel(page);
  await expect(panel).toBeVisible();
  await expect(panel.getByLabel("Pre-score ticker")).toBeVisible();
  await expect(panel.getByLabel("Pre-score direction")).toBeVisible();
  await expect(panel.getByLabel("Strategy tag")).toBeVisible();
  await expect(panel.getByLabel("Size %")).toBeVisible();
  await expect(panel.getByRole("button", { name: "Score Before Trade" })).toBeVisible();
});

test("Pre-score result shows recommendation context", async ({ page }) => {
  await openLogTrade(page);

  const panel = preScorePanel(page);
  await panel.getByLabel("Pre-score ticker").fill("AAPL");
  await panel.getByLabel("Strategy tag").fill("rsi_oversold");
  const response = page.waitForResponse((item) => item.url().includes("/api/trading/prescore") && item.request().method() === "POST");
  await panel.getByRole("button", { name: "Score Before Trade" }).click();
  await response;

  await expect(panel.getByText(/PROCEED|REDUCE|SKIP/i).first()).toBeVisible({ timeout: 10_000 });
  await expect(panel.getByText("Confidence", { exact: true })).toBeVisible();
  await expect(panel.getByText("Regime", { exact: true })).toBeVisible();
  await expect(panel.getByText("Evidence", { exact: true })).toBeVisible();
  await expect(panel.getByText(/Decision context|Signal alignment|Regime fit/i).first()).toBeVisible();
});

test("Pre-score panel shows warning or stable empty-warning state", async ({ page }) => {
  await openLogTrade(page);

  const panel = preScorePanel(page);
  await panel.getByLabel("Pre-score ticker").fill("MSFT");
  const response = page.waitForResponse((item) => item.url().includes("/api/trading/prescore") && item.request().method() === "POST");
  await panel.getByRole("button", { name: "Score Before Trade" }).click();
  await response;

  await expect(panel.getByText(/Warnings|No pre-trade warnings/i).first()).toBeVisible({ timeout: 10_000 });
});

test("Pre-score interactions have no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await openLogTrade(page);

  const panel = preScorePanel(page);
  await panel.getByLabel("Pre-score ticker").fill("AAPL");
  const response = page.waitForResponse((item) => item.url().includes("/api/trading/prescore") && item.request().method() === "POST");
  await panel.getByRole("button", { name: "Score Before Trade" }).click();
  await response;
  await expect(panel.getByText(/PROCEED|REDUCE|SKIP/i).first()).toBeVisible({ timeout: 10_000 });

  expectNoConsoleErrors(errors);
});
