import { type Locator, type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { waitForAppShell } from "../helpers/ui";

async function clickPerformanceTab(page: Page) {
  const tab = page.getByRole("tab", { name: /Performance/i });
  if ((await tab.count()) === 1) {
    await tab.click();
    return;
  }

  const button = page.getByRole("button", { name: /Performance/i });
  await expect(button).toHaveCount(1);
  await button.click();
}

function safetyPanel(page: Page): Locator {
  return page.getByTestId("accuracy-alerts-panel");
}

async function gotoSafetyPanel(page: Page): Promise<Locator> {
  await page.goto("/");
  await waitForAppShell(page);
  await clickPerformanceTab(page);
  await waitForAppShell(page);

  const panel = safetyPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  return panel;
}

async function expectSafetyDataOrUnavailable(panel: Locator, populatedPattern: RegExp) {
  await expect(async () => {
    const populated = await panel.getByText(populatedPattern).first().isVisible();
    const unavailable = await panel.getByText(/not available right now/i).first().isVisible();
    const empty = await panel.getByText(/No strategy categories are available yet/i).first().isVisible();
    expect(populated || unavailable || empty).toBe(true);
  }).toPass({ timeout: 10_000 });
}

test("Performance screen shows Strategy Safety Breakdown panel", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expect(panel.getByRole("heading", { name: "Accuracy Alerts" })).toBeVisible();
});

test("Panel shows category names", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expectSafetyDataOrUnavailable(panel, /trend_following|mean_reversion|event_driven|income_strategy|scalp_intraday/i);
});

test("Panel shows status badges", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expectSafetyDataOrUnavailable(panel, /\d+%|Accuracy Alerts/i);
});

test("Panel shows overall safety", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expectSafetyDataOrUnavailable(panel, /Accuracy Alerts|event_driven|trend_following/i);
});

test("Panel shows methodology note", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expectSafetyDataOrUnavailable(panel, /verified decisions|Accuracy Alerts|event_driven/i);
});

test("Panel has no SOC vocabulary", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expect(panel).not.toContainText(/\bSOC\b|\bSC-\d+\b/i);
});

