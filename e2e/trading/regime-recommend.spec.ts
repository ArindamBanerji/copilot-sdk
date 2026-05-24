import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";

function regimePanel(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Market Regime" }) }).first();
}

function detailPanel(page: Page) {
  return regimePanel(page).locator("div", { has: page.getByRole("heading", { name: "Detailed Recommendations" }) }).first();
}

test("Regime detail shows recommendations or unavailable state", async ({ page }) => {
  await page.goto("/");

  const detail = detailPanel(page);
  await expect(detail).toBeVisible({ timeout: 15_000 });
  await expect(
    detail
      .getByText(/Allocation context|Shift suggestion|No detailed regime recommendations available|Detailed regime recommendations unavailable/i)
      .first(),
  ).toBeVisible();
});

test("Regime detail shows regime-neutral context or summary", async ({ page }) => {
  await page.goto("/");

  const detail = detailPanel(page);
  await expect(detail).toBeVisible({ timeout: 15_000 });
  await expect(detail.getByText(/regime-neutral|regime-sensitive|avoid|reduce|increase|hold|Conservation not confirmed|Detailed regime recommendations unavailable|Allocation context/i).first()).toBeVisible();
});

test("Regime detail shows conservation status", async ({ page }) => {
  await page.goto("/");

  const detail = detailPanel(page);
  await expect(detail).toBeVisible({ timeout: 15_000 });
  await expect(detail.getByText(/Conservation confirmed|Conservation not confirmed/i).first()).toBeVisible();
});

test("Regime detail avoids investment-advice wording", async ({ page }) => {
  await page.goto("/");

  const detail = detailPanel(page);
  await expect(detail).toBeVisible({ timeout: 15_000 });
  await expect(detail).not.toContainText(/you should buy|financial advice/i);
});

test("Regime detail has no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await page.goto("/");
  await expect(detailPanel(page)).toBeVisible({ timeout: 15_000 });

  expectNoConsoleErrors(errors);
});

