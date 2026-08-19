import { expect, test } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

test("volatility scenario endpoints expose evidence labels", async ({ request }) => {
  for (const path of ["sharpe", "vrp", "rich-cheap", "dispersion", "tail-bets"]) {
    const response = await request.get(`/api/trading/volatility/${path}`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty("evidence_tier");
    expect(body).toMatchObject({ observation_only: true });
  }
});

test("volatility scenario panel renders on Performance", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await expect(page.getByTestId("volatility-scenario-panel")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("volatility-scenario-evidence")).toBeVisible();
});

test("volatility scenario panel is observation-only", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  const panel = page.getByTestId("volatility-scenario-panel");
  await expect(panel).toBeVisible({ timeout: 20_000 });
  await expect(panel).toContainText(/Observation|loading/i);
  await expect(panel).toContainText(/No forward action is inferred/i);
  await expect(panel).not.toContainText(/recommend|buy|sell|reduce|increase|hold/i);
});
