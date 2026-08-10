import { test, expect } from "../fixtures/copilot-fixture";
import { waitForAppShell, waitForScreenReady } from "../helpers/ui";

async function gotoDashboard(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await waitForScreenReady(page);
  await expect(page.getByTestId("trust-card")).toBeVisible({ timeout: 20_000 });
}

test("trust card visible on dashboard", async ({ page }) => {
  await gotoDashboard(page);

  await expect(page.getByText("SC-TRUST")).toBeVisible();
  await expect(page.getByText("Source reliability")).toBeVisible();
});

test("trust card shows 6 factor bars", async ({ page }) => {
  await gotoDashboard(page);

  await expect(page.getByTestId("trust-factor")).toHaveCount(6);
});

test("trust card shows overall score", async ({ page }) => {
  await gotoDashboard(page);

  await expect(page.getByText("overall trust")).toBeVisible();
  await expect(page.getByTestId("trust-card").getByText(/^\d+\.\d+$/)).toBeVisible();
});

test("trust card shows conservation badge", async ({ page }) => {
  await gotoDashboard(page);

  await expect(page.getByTestId("trust-card").getByText(/^Conservation /)).toBeVisible();
});
