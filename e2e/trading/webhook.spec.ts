import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

async function gotoPerformance(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(page.getByText("Performance Summary")).toBeVisible({ timeout: 15_000 });
}

function signalCard(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Signal Integration" }) }).first();
}

test("webhook config endpoint returns object", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/trading/webhook/config");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(typeof data).toBe("object");
});

test("webhook history endpoint returns array", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/trading/webhook/history");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(Array.isArray(data)).toBeTruthy();
});

test("signal integration card renders on Performance tab", async ({ page }) => {
  await gotoPerformance(page);
  await expect(signalCard(page)).toBeVisible({ timeout: 15_000 });
});

test("signal card shows alert count or empty state", async ({ page }) => {
  await gotoPerformance(page);
  await expect(signalCard(page).getByText(/alerts received|No signals received yet/i).first()).toBeVisible({
    timeout: 15_000,
  });
});

test("signal card shows accuracy by speed when data exists", async ({ page }) => {
  await page.route("**/api/trading/webhook/history", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify([
        {
          signal_id: "sig-1",
          ticker: "AAPL",
          signal_type: "breakout",
          received_at: "2026-06-23T12:00:00Z",
          time_to_trade_seconds: 240,
          is_correct: true,
          scored: { recommended_action: "strong_execution" },
        },
      ]),
    });
  });
  await gotoPerformance(page);
  const card = signalCard(page);
  await expect(card.getByText("Accuracy by speed")).toBeVisible({ timeout: 15_000 });
  await expect(card.getByText(/Fast entry/i)).toBeVisible();
  await expect(card.getByText(/100% accuracy/)).toBeVisible();
});
