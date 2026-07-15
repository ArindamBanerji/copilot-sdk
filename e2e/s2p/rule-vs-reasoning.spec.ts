import { expect, test, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function backendHealthy(page: Page): Promise<boolean> {
  const response = await page.request.get("http://127.0.0.1:8002/health", { timeout: 3000 }).catch(() => null);
  return Boolean(response?.ok());
}

async function openScoredTriage(page: Page) {
  test.skip(!(await backendHealthy(page)), "S2P backend is not running");
  await page.goto("/");
  await clickTab(page, "Exception Triage");
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
  const selected = page.locator("article").filter({ hasText: /Selected Invoice/i });
  await expect(selected).toContainText(/Supplier|Amount|Category/i, { timeout: 20000 });
  await selected.getByRole("button", { name: /^Score$/i }).click();
  await expect(page.getByTestId("rule-vs-reasoning-panel")).toBeVisible({ timeout: 20000 });
}

test("test_contrast_panel_visible_on_triage", async ({ page }) => {
  await openScoredTriage(page);

  await expect(page.getByTestId("rule-vs-reasoning-panel")).toContainText(/Rule vs reasoning/i);
});

test("test_contrast_shows_two_columns", async ({ page }) => {
  await openScoredTriage(page);
  const panel = page.getByTestId("rule-vs-reasoning-panel");

  await expect(panel).toContainText(/Rule-Based/i);
  await expect(panel).toContainText(/Situation-Aware/i);
});

test("test_contrast_rule_shows_reject", async ({ page }) => {
  await openScoredTriage(page);

  await expect(page.getByTestId("rule-vs-reasoning-panel")).toContainText(/REJECT|APPROVE/i);
});
