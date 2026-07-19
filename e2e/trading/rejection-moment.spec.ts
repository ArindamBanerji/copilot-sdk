import { expect, test } from "@playwright/test";

const FRONTEND = process.env.TRADING_FRONTEND ?? "http://127.0.0.1:5174";
const BACKEND = process.env.TRADING_BACKEND ?? "http://127.0.0.1:8010";

test.beforeEach(async ({ request }) => {
  const health = await request.get(`${BACKEND}/health`, { timeout: 5_000 }).catch((error) => {
    console.debug("Trading health check unavailable", error);
    return null;
  });
  test.skip(!health?.ok(), "Trading backend not running");
});

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto(FRONTEND, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /Performance/i }).click();
  await expect(page.locator("main")).not.toContainText(/Loading performance/i, { timeout: 20_000 });
  const panel = rejectionPanel(page);
  await expect(panel).toBeVisible({ timeout: 20_000 });
  await expect(panel).not.toContainText(/Loading rejection summary/i, { timeout: 20_000 });
}

function rejectionPanel(page: import("@playwright/test").Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Agent Evolution Summary", exact: true }) }).first();
}

test("rejection panel visible on performance", async ({ page }) => {
  await gotoPerformance(page);
});

test("rejection panel shows counts", async ({ page }) => {
  await gotoPerformance(page);
  const panel = rejectionPanel(page);
  await expect(panel.getByText(/^Tested$/i)).toBeVisible();
  await expect(panel.getByText(/^Promoted$/i)).toBeVisible();
  await expect(panel.getByText(/^Rejected$/i)).toBeVisible();
});

test("test_rejection_data_persists", async ({ page }) => {
  await gotoPerformance(page);

  const panel = rejectionPanel(page);
  const text = await panel.innerText({ timeout: 20_000 });
  const match = text.match(/Rejected\s+(\d+)/i);
  const count = match ? Number(match[1]) : 0;
  if (!match) {
    console.debug("Could not parse rejected count from rejection panel", text);
  }
  expect(count).toBeGreaterThan(0);
});

test("test_rejection_shows_conservation_reason", async ({ page }) => {
  await gotoPerformance(page);

  const panel = rejectionPanel(page);
  await expect(panel).toContainText(/conservation|correctness|variance/i, { timeout: 20_000 });
});
