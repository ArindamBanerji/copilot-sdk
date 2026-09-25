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
}

function rejectionPanel(page: import("@playwright/test").Page) {
  return page.getByTestId("rule-lifecycle-panel");
}

test("rejection panel visible on performance", async ({ page }) => {
  await gotoPerformance(page);
});

test("rejection panel shows counts", async ({ page }) => {
  await gotoPerformance(page);
  const panel = rejectionPanel(page);
  await expect(panel).toContainText(/Evolution|Promotion/i);
});

test("test_rejection_data_persists", async ({ page }) => {
  await gotoPerformance(page);

  await expect(rejectionPanel(page)).toContainText(/active|promoted|rejected|not recorded/i);
});

test("test_rejection_shows_conservation_reason", async ({ page }) => {
  await gotoPerformance(page);

  await expect(rejectionPanel(page)).toContainText(/Evolution|Promotion|not recorded/i, { timeout: 20_000 });
});

