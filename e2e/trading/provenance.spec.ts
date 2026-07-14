import { test, expect } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";

test.beforeEach(async ({ request }) => {
  const response = await request.get("http://127.0.0.1:8010/health", { timeout: 5_000 }).catch(() => null);
  test.skip(!response?.ok(), "Trading backend not running");
});

async function gotoTab(page: import("@playwright/test").Page, name: string) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, name);
  await waitForAppShell(page);
}

async function expectProvenanceText(page: import("@playwright/test").Page) {
  await expect(page.getByText(/learned|sample|proven|external|cached|market data/i).first()).toBeVisible({ timeout: 20_000 });
}

test("provenance badge on analysis", async ({ page }) => {
  await gotoTab(page, "Analysis");
  await expectProvenanceText(page);
});

test("provenance badge on performance", async ({ page }) => {
  await gotoTab(page, "Performance");
  await expectProvenanceText(page);
});

test("provenance badge shows tier", async ({ page }) => {
  await gotoTab(page, "Analysis");
  const tier = page.getByText(/learned|sample|proven|external|cached/i).first();
  await expect(tier).toBeVisible({ timeout: 20_000 });
});
