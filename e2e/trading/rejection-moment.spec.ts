import { expect, test } from "@playwright/test";

const FRONTEND = process.env.TRADING_FRONTEND ?? "http://127.0.0.1:5174";
const BACKEND = process.env.TRADING_BACKEND ?? "http://127.0.0.1:8010";

test.beforeEach(async ({ request }) => {
  const health = await request.get(`${BACKEND}/health`, { timeout: 5_000 }).catch(() => null);
  test.skip(!health?.ok(), "Trading backend not running");
});

test("rejection panel visible on performance", async ({ page }) => {
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /Performance/i }).click();
  await expect(page.locator("main")).not.toContainText(/Loading performance/i, { timeout: 20_000 });
  await expect(page.getByRole("heading", { name: "Agent Evolution Summary", exact: true })).toBeVisible({
    timeout: 20_000,
  });
});

test("rejection panel shows counts", async ({ page }) => {
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /Performance/i }).click();
  await expect(page.locator("main")).not.toContainText(/Loading performance/i, { timeout: 20_000 });
  await expect(page.getByRole("heading", { name: "Agent Evolution Summary", exact: true })).toBeVisible({
    timeout: 20_000,
  });
  await expect(page.getByText(/Tested/i)).toBeVisible();
  await expect(page.getByText(/Promoted/i)).toBeVisible();
  await expect(page.getByText(/Rejected/i)).toBeVisible();
});
