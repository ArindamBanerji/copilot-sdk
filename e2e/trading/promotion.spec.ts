import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

async function gotoPerformance(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(page.getByText("Performance Summary")).toBeVisible({ timeout: 15_000 });
}

function promotionPanel(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Strategy Promotion" }) }).first();
}

test("Promotion panel is visible on Performance", async ({ page }) => {
  await gotoPerformance(page);

  const panel = promotionPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel.getByText("Tier readiness")).toBeVisible();
});

test("Promotion panel shows tiers or empty state", async ({ page }) => {
  await gotoPerformance(page);

  const panel = promotionPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  const strategyRows = panel.locator("article");
  if ((await strategyRows.count()) > 0) {
    await expect(strategyRows.first().getByText(/paper|small live|full live/i).first()).toBeVisible();
    await expect(strategyRows.first().getByText(/verified/i).first()).toBeVisible();
    await expect(strategyRows.first().getByText(/win rate/i).first()).toBeVisible();
  } else {
    await expect(panel.getByText(/Loading promotion tiers|Score trades to begin tier tracking|Promotion data is unavailable/i).first()).toBeVisible();
  }
});

test("Promotion panel shows history or no events", async ({ page }) => {
  await gotoPerformance(page);

  const panel = promotionPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  await expect(panel.getByRole("heading", { name: "Promotion History" })).toBeVisible();
  await expect(
    panel.getByText(/No promotion events yet|promote|demote|paper to small live|small live to full live/i).first(),
  ).toBeVisible();
});

test("Promotion panel has no SOC vocabulary", async ({ page }) => {
  await gotoPerformance(page);

  await expect(promotionPanel(page)).not.toContainText(/\bSOC\b|\bSC-\d+\b/i);
});

test("Promotion panel has no console errors", async ({ page }) => {
  await gotoPerformance(page);
  await expect(promotionPanel(page)).toBeVisible({ timeout: 15_000 });
  const errors = collectConsoleErrors(page);
  await page.waitForTimeout(500);

  expectNoConsoleErrors(errors);
});

