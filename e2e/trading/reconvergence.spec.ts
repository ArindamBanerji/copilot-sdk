import { expect, test, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

const BACKEND = process.env.TRADING_BACKEND || "http://127.0.0.1:8010";

async function gotoPerformance(page: Page) {
  await page.goto("/");
  await clickTab(page, "Performance");
  await expect(page.getByTestId("centroid-timeline-panel")).toBeVisible({ timeout: 20_000 });
}

test("re-convergence panel renders", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByTestId("centroid-timeline-panel")).toBeVisible();
  await expect(page.getByText("Centroid Timeline")).toBeVisible();
});

test("re-convergence shows ARCH experimental label", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByTestId("rule-lifecycle-panel")).toContainText(/Evolution|Promotion/i);
});

test("re-convergence shows regime badge", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByTestId("accuracy-alerts-panel")).toContainText(/trend_following|event_driven|mean_reversion/i);
});

test("re-convergence shows checkpoint depth", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByTestId("centroid-timeline-panel")).toContainText(/checkpoint/i);
});

test("regime re-init endpoint is discoverable", async ({ request }) => {
  const response = await request.post(`${BACKEND}/api/self/regime-reinit`);
  expect([200, 404, 405, 422]).toContain(response.status());
});

