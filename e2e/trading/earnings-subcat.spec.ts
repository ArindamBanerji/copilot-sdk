import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

async function openJournal(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Journal");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Trade Journal" })).toBeVisible();
}

function categoryAnalytics(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Category Analytics" }) }).first();
}

async function routeJournalAnalytics(page: Page, withEventDriven: boolean) {
  await page.route("**/api/trading/journal/trades?**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        trades: [],
        count: 0,
        total: 0,
        filters_applied: {},
        aggregate: { total_trades: 0, win_rate: null, avg_pnl: null, total_pnl: 0, avg_confidence: null },
      }),
    });
  });
  await page.route("**/api/trading/analytics?**", async (route) => {
    const url = new URL(route.request().url());
    const groupBy = url.searchParams.get("group_by");
    if (groupBy === "subcategory") {
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          group_by: "subcategory",
          total: withEventDriven ? 3 : 0,
          groups: withEventDriven
            ? [
                { key: "directional", count: 2, total_trades: 2, win_rate: 0.5, avg_pnl: 125, total_pnl: 250 },
                { key: "volatility", count: 1, total_trades: 1, win_rate: 1, avg_pnl: 300, total_pnl: 300 },
              ]
            : [],
        }),
      });
      return;
    }
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        group_by: "category",
        total: withEventDriven ? 3 : 0,
        groups: withEventDriven
          ? [{ key: "event_driven", count: 3, total_trades: 3, win_rate: 0.667, avg_pnl: 183.33, total_pnl: 550 }]
          : [],
      }),
    });
  });
}

test("Journal analytics shows event-driven subcategory split", async ({ page }) => {
  await routeJournalAnalytics(page, true);
  await openJournal(page);

  const analytics = categoryAnalytics(page);
  await expect(analytics).toBeVisible();
  await expect(analytics.getByText("Event Driven", { exact: true })).toBeVisible();
  await expect(analytics.getByText("Event Driven Split")).toBeVisible();
  await expect(analytics.getByText("Directional")).toBeVisible();
  await expect(analytics.getByText(/2 trades, 50\.0% win rate/i)).toBeVisible();
  await expect(analytics.getByText("Volatility")).toBeVisible();
  await expect(analytics.getByText(/1 trades, 100\.0% win rate/i)).toBeVisible();
});

test("Journal analytics handles no event-driven trades", async ({ page }) => {
  await routeJournalAnalytics(page, false);
  await openJournal(page);

  const analytics = categoryAnalytics(page);
  await expect(analytics).toBeVisible();
  await expect(analytics.getByText("No category analytics available for the current filters.")).toBeVisible();
  await expect(analytics.getByText("Event Driven Split")).toHaveCount(0);
});

test("Journal subcategory panel has no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await routeJournalAnalytics(page, true);
  await openJournal(page);
  await expect(categoryAnalytics(page).getByText("Event Driven Split")).toBeVisible();

  expectNoConsoleErrors(errors);
});

test("Journal subcategory panel has no SOC vocabulary", async ({ page }) => {
  await routeJournalAnalytics(page, true);
  await openJournal(page);

  await expect(categoryAnalytics(page)).not.toContainText(/\bSOC\b|\bSC-\d+\b/i);
});

test("earnings insight card renders on Journal Analytics", async ({ page }) => {
  await routeJournalAnalytics(page, true);
  await openJournal(page);

  await expect(page.getByRole("heading", { name: "Earnings Style Analysis" })).toBeVisible();
});

test("earnings insight shows directional vs volatility split", async ({ page }) => {
  await routeJournalAnalytics(page, true);
  await openJournal(page);

  const card = page.locator("section", { has: page.getByRole("heading", { name: "Earnings Style Analysis" }) });
  await expect(card.getByText("Directional", { exact: true })).toBeVisible();
  await expect(card.getByText("Volatility", { exact: true })).toBeVisible();
  await expect(card.getByText("Single-leg calls/puts")).toBeVisible();
  await expect(card.getByText("Straddles/strangles")).toBeVisible();
});

test("earnings insight shows dominant style callout", async ({ page }) => {
  await routeJournalAnalytics(page, true);
  await openJournal(page);

  const card = page.locator("section", { has: page.getByRole("heading", { name: "Earnings Style Analysis" }) });
  await expect(card).toContainText("You are an earnings DIRECTIONAL trader.");
  await expect(card).toContainText("directional: 50.0%");
  await expect(card).toContainText("Volatility: 100.0%");
});
