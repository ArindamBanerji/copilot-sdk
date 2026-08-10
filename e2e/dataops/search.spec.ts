import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForScreenReady } from "../helpers/ui";

async function gotoInsight(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Insight");
  await waitForScreenReady(page);
  await expect(page.getByTestId("search-panel")).toBeVisible();
}

test("test_search_panel_visible_on_insight", async ({ page }) => {
  await gotoInsight(page);
  await expect(page.getByText("Find trusted data assets")).toBeVisible();
});

test("test_search_input_accepts_text", async ({ page }) => {
  await gotoInsight(page);
  const input = page.getByTestId("search-input");
  await input.fill("orders");
  await expect(input).toHaveValue("orders");
});

test("test_search_results_show_quality_badges", async ({ page }) => {
  await gotoInsight(page);
  await expect(page.getByTestId("quality-badge").first()).toBeVisible();
});

test("test_search_filters_reduce_results", async ({ page }) => {
  await gotoInsight(page);
  const panel = page.getByTestId("search-panel");
  await panel.getByTestId("search-input").fill("orders");
  await expect.poll(() => panel.getByTestId("search-result").count()).toBeGreaterThan(0);
  const initial = await panel.getByTestId("search-result").count();
  await panel.getByTestId("search-trust-filter").selectOption("1");
  await expect.poll(() => panel.getByTestId("search-result").count()).toBeLessThan(initial);
});
