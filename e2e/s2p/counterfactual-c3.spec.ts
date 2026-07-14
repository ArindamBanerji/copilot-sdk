import { expect, test } from "@playwright/test";

const FRONTEND = process.env.S2P_FRONTEND ?? "http://127.0.0.1:5177";
const BACKEND = process.env.S2P_BACKEND ?? "http://127.0.0.1:8002";

test.beforeEach(async ({ request }) => {
  const health = await request.get(`${BACKEND}/health`, { timeout: 5_000 }).catch(() => null);
  test.skip(!health?.ok(), "S2P backend not running");
});

test("counterfactual card visible on s2p", async ({ page }) => {
  await page.goto(FRONTEND);
  await page.getByRole("button", { name: "Exception Triage" }).click();
  await expect(page.getByTestId("counterfactual-card")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("heading", { name: /What If/i })).toBeVisible();
});
