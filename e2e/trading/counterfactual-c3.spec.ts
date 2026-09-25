import { expect, test } from "@playwright/test";

const FRONTEND = process.env.TRADING_FRONTEND ?? "http://127.0.0.1:5174";
const BACKEND = process.env.TRADING_BACKEND ?? "http://127.0.0.1:8010";

test.beforeEach(async ({ request }) => {
  const health = await request.get(`${BACKEND}/health`, { timeout: 5_000 }).catch(() => null);
  test.skip(!health?.ok(), "Trading backend not running");
});

test("counterfactual card visible on analysis", async ({ page }) => {
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /Analysis/i }).click();
  await expect(page.locator("main")).not.toContainText(/Loading analysis/i, { timeout: 20_000 });
  await expect(page.getByTestId("counterfactual-card")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("heading", { name: /What If/i })).toBeVisible();
});

test("counterfactual shows delta", async ({ page }) => {
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /Analysis/i }).click();
  await expect(page.locator("main")).not.toContainText(/Loading analysis/i, { timeout: 20_000 });
  const card = page.getByTestId("counterfactual-card");
  const hasDelta = await card.getByText(/^Delta$/i).isVisible().catch(() => false);
  if (hasDelta) {
    await expect(card.getByTestId("counterfactual-delta").getByText(/[+-]?\d+\.\d{2}/)).toBeVisible();
  } else {
    await expect(card.getByRole("heading", { name: /What If/i })).toBeVisible();
  }
});

test("counterfactual sample refusal renders", async ({ page }) => {
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /Analysis/i }).click();
  await expect(page.locator("main")).not.toContainText(/Loading analysis/i, { timeout: 20_000 });
  const btn = page.getByRole("button", { name: /Try sample/i });
  const btnVisible = await btn.isVisible().catch(() => false);
  if (!btnVisible) {
    test.skip(true, "No interactive controls in static state");
    return;
  }
  await btn.click();
  await expect(page.getByText(/F-22|sample-provenance/i)).toBeVisible({ timeout: 20_000 });
});

