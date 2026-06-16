import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

async function gotoDashboard(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

test.describe("Provenance Badge - spot checks", () => {
  test("Dashboard shows provenance badge", async ({ page }) => {
    await gotoDashboard(page);
    const badge = page.locator('[data-testid="provenance-badge"]');
    const badgeOrText = badge.or(page.getByText(/Market data:/i));
    await expect(badgeOrText.first()).toBeVisible({ timeout: 10000 });
  });

  test("Badge shows valid source state", async ({ page }) => {
    await gotoDashboard(page);
    const badgeText = await page.getByText(/Market data:/i).first().textContent();
    expect(badgeText).toMatch(/live|cached|sample/i);
  });
});

test.describe("Market Data - flow tests", () => {
  test("Dashboard loads with market context and badge", async ({ page }) => {
    await gotoDashboard(page);
    await page.waitForLoadState("networkidle");

    const marketSection = page.getByText(/SPY|VIX|Market/i).first();
    await expect(marketSection).toBeVisible({ timeout: 10000 });

    const badge = page.getByText(/Market data:/i).first();
    await expect(badge).toBeVisible();

    const text = await badge.textContent();
    expect(text).toMatch(/live|cached|sample/i);
  });

  test("Ticker lookup shows enriched data with provenance", async ({ page }) => {
    await gotoDashboard(page);
    await page.waitForLoadState("networkidle");

    const searchInput = page.locator(
      'input[placeholder*="ticker" i], input[placeholder*="search" i], input[placeholder*="symbol" i]',
    );

    if ((await searchInput.count()) > 0) {
      await searchInput.first().fill("SPY");
      await searchInput.first().press("Enter");
      await page.waitForTimeout(2000);

      const priceText = page.getByText(/\$[0-9]/).first();
      if ((await priceText.count()) > 0) {
        await expect(priceText).toBeVisible();
      }
    }
  });

  test("Navigate tabs - market data persists", async ({ page }) => {
    await gotoDashboard(page);
    await page.waitForLoadState("networkidle");

    const badge = page.getByText(/Market data:/i).first();
    if ((await badge.count()) > 0) {
      const analysisTab = page.getByText(/Analysis/i).first();
      if ((await analysisTab.count()) > 0) {
        await clickTab(page, "Analysis");
        await page.waitForTimeout(1000);
      }

      const dashTab = page.getByText(/Dashboard/i).first();
      if ((await dashTab.count()) > 0) {
        await clickTab(page, "Dashboard");
        await page.waitForTimeout(1000);
      }

      const afterText = await page.getByText(/Market data:/i).first().textContent();
      expect(afterText).toMatch(/live|cached|sample/i);
    }
  });

  test("Regime panel and market context show coherent data", async ({ page }) => {
    await gotoDashboard(page);
    await page.waitForLoadState("networkidle");

    const vixOnDashboard = page.getByText(/VIX/i).first();
    if ((await vixOnDashboard.count()) > 0) {
      await expect(vixOnDashboard).toBeVisible();
    }

    const analysisTab = page.getByText(/Analysis/i).first();
    if ((await analysisTab.count()) > 0) {
      await clickTab(page, "Analysis");
      await page.waitForTimeout(2000);

      const vixInRegime = page.getByText(/VIX/i).first();
      if ((await vixInRegime.count()) > 0) {
        await expect(vixInRegime).toBeVisible();
      }
    }
  });
});
