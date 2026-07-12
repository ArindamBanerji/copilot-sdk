import { test, expect } from "@playwright/test";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

test.beforeEach(async ({ request }) => {
  const response = await request.get("http://localhost:8010/health", { timeout: 5_000 }).catch(() => null);
  test.skip(!response?.ok(), "Trading backend not running");
});

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: /Counterfactual|What if/i }).first()).toBeVisible({ timeout: 20_000 });
}

test("counterfactual card visible", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByRole("heading", { name: /counterfactual|what if/i }).first()).toBeVisible();
});

test("counterfactual shows delta", async ({ page }) => {
  await gotoAnalysis(page);
  const card = page.locator("section").filter({ has: page.getByRole("heading", { name: /counterfactual|what if/i }) }).first();
  await expect(card).toBeVisible();
  await expect(card.getByText(/\$[1-9]|\b[1-9]\d*%|\b[1-9]\d*\b/i).first()).toBeVisible();
  await expect(card.getByText(/No counterfactual/i)).toHaveCount(0);
});

test("counterfactual no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoAnalysis(page);
  expectNoConsoleErrors(errors.filter((error) => /counterfactual/i.test(error)));
});
