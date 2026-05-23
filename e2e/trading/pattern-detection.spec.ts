import { type Locator, type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";

async function clickAnalysisTab(page: Page) {
  const tab = page.getByRole("tab", { name: /Analysis/i });
  if ((await tab.count()) === 1) {
    await tab.click();
    return;
  }

  const button = page.getByRole("button", { name: /Analysis/i });
  await expect(button).toHaveCount(1);
  await button.click();
}

function patternPanel(page: Page): Locator {
  return page.locator("section.copilot-card").filter({
    has: page.getByText("Behavioral Pattern Detection"),
  });
}

async function gotoPatternPanel(page: Page): Promise<Locator> {
  await page.goto("/");
  await clickAnalysisTab(page);

  const panel = patternPanel(page);
  await expect(panel).toBeVisible();
  return panel;
}

async function expectPatternDataOrNoData(panel: Locator, populatedPattern: RegExp) {
  const populated = panel.filter({ hasText: populatedPattern });
  const noData = panel.filter({ hasText: /Import trades to detect patterns/i });
  const unavailable = panel.filter({ hasText: /Pattern detection unavailable|not available right now/i });
  await expect(populated.or(noData).or(unavailable)).toBeVisible();
}

test("Analysis screen shows Behavioral Pattern Detection panel", async ({ page }) => {
  const panel = await gotoPatternPanel(page);

  await expect(panel.getByText("Behavioral Pattern Detection")).toBeVisible();
});

test("Panel shows empty state or detected patterns", async ({ page }) => {
  const panel = await gotoPatternPanel(page);

  await expectPatternDataOrNoData(panel, /High severity|Medium severity|Low severity|Affected trades/i);
});

test("Panel shows pattern count or no-data message", async ({ page }) => {
  const panel = await gotoPatternPanel(page);

  await expectPatternDataOrNoData(panel, /\bpatterns\b|\btrades\b/i);
});

test("Panel shows recommendations when patterns exist", async ({ page }) => {
  const panel = await gotoPatternPanel(page);

  await expectPatternDataOrNoData(panel, /cooldown|cap size|require|pause|fixed or reduced size|recommendation/i);
});

test("Panel has no SOC vocabulary", async ({ page }) => {
  const panel = await gotoPatternPanel(page);

  await expect(panel).not.toContainText(/\bSOC\b|\bSC-\d+\b/i);
});
