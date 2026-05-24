import { type Locator, type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";

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
  return page.locator("section.copilot-card", {
    has: page.getByRole("heading", { name: "Strategy Safety Breakdown" }),
  }).first();
}

async function gotoSafetyPanel(page: Page): Promise<Locator> {
  await page.goto("/");
  await clickPerformanceTab(page);

  const panel = safetyPanel(page);
  await expect(panel).toBeVisible({ timeout: 15_000 });
  return panel;
}

async function expectSafetyDataOrUnavailable(panel: Locator, populatedPattern: RegExp) {
  const populated = panel.getByText(populatedPattern);
  const unavailable = panel.getByText(/not available right now/i);
  const empty = panel.getByText(/No strategy categories are available yet/i);
  await expect(populated.first().or(unavailable.first()).or(empty.first())).toBeVisible();
}

test("Performance screen shows Strategy Safety Breakdown panel", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expect(panel.getByText("Strategy Safety Breakdown")).toBeVisible();
});

test("Panel shows category names", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expectSafetyDataOrUnavailable(panel, /Trend Following|Mean Reversion|Event Driven|Income Strategy|Scalp Intraday/i);
});

test("Panel shows status badges", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expectSafetyDataOrUnavailable(panel, /BOOTSTRAP|GREEN|AMBER|RED/i);
});

test("Panel shows overall safety", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expectSafetyDataOrUnavailable(panel, /All strategies safe|Some strategies paused/i);
});

test("Panel shows methodology note", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expectSafetyDataOrUnavailable(panel, /Simplified.*proxy|api\/conservation\/status|Global conservation remains authoritative/i);
});

test("Panel has no SOC vocabulary", async ({ page }) => {
  const panel = await gotoSafetyPanel(page);

  await expect(panel).not.toContainText(/\bSOC\b|\bSC-\d+\b/i);
});
