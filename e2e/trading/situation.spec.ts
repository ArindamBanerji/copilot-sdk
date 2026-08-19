import { expect, test } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

test("situation endpoint exposes regime-conditioned observations", async ({ request }) => {
  const response = await request.get("/api/trading/situation");
  expect(response.ok()).toBeTruthy();
  const body = await response.json();
  expect(["trending", "ranging", "volatile", "calm"]).toContain(body.regime);
  expect(body).toMatchObject({ observation_only: true });
  expect(body.indicators).toEqual(expect.objectContaining({ vix: expect.any(Number), adx: expect.any(Number) }));
  expect(body).toHaveProperty("per_strategy_accuracy_in_regime");
});

test("situation panel renders regime and evidence state", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await expect(page.getByTestId("situation-judgment")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("situation-regime")).toBeVisible();
  await expect(page.getByTestId("situation-evidence-tier")).toBeVisible();
});

test("situation panel remains observation-only", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  const panel = page.getByTestId("situation-judgment");
  await expect(panel).toBeVisible({ timeout: 20_000 });
  await expect(panel).toContainText(/Observation|Insufficient evidence/i);
  await expect(panel).toContainText(/No forward action is inferred/i);
  await expect(panel).not.toContainText(/reduce\s+size|\bavoid\b|\bhold\s+sizing\b/i);
});
