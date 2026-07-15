import { test, expect } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";

test.beforeEach(async ({ request }) => {
  const response = await request.get("http://127.0.0.1:8010/health", { timeout: 5_000 }).catch(() => null);
  test.skip(!response?.ok(), "Trading backend not running");
});

async function gotoDashboard(page: import("@playwright/test").Page) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await waitForAppShell(page);
  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
}

test("day zero card visible on dashboard", async ({ page }) => {
  await gotoDashboard(page);
  await expect(page.getByTestId("day-zero-card")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("heading", { name: /Instrument Calibrated|Accumulating Evidence|Measured|Measurement State/i })).toBeVisible();
});

test("day zero shows provenance", async ({ page }) => {
  await gotoDashboard(page);
  const card = page.getByTestId("day-zero-card");
  await expect(card.getByText(/Instrument|Accumulating|Learned/i).first()).toBeVisible({ timeout: 20_000 });
});

test("day zero no fake numbers", async ({ page }) => {
  await gotoDashboard(page);
  const card = page.getByTestId("day-zero-card");
  const instrumentVisible = await card.getByRole("heading", { name: /Instrument Calibrated/i }).isVisible().catch(() => false);
  if (instrumentVisible) {
    await expect(card.getByText(/Accuracy:/i)).toHaveCount(0);
    await expect(card.getByText(/IKS/i)).toHaveCount(0);
    await expect(card.getByText(/\d+(\.\d+)?%/)).toHaveCount(0);
  }
});
