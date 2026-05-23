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

function trustPanel(page: Page): Locator {
  return page.locator("section.copilot-card").filter({
    has: page.getByText("Signal Trust Analysis"),
  });
}

async function gotoTrustPanel(page: Page): Promise<Locator> {
  await page.goto("/");
  await clickAnalysisTab(page);

  const panel = trustPanel(page);
  await expect(panel).toBeVisible();
  return panel;
}

async function expectTrustDataOrNoData(panel: Locator, populatedPattern: RegExp) {
  const populated = panel.getByText(populatedPattern);
  await expect(populated.first()).toBeVisible();
}

test("Analysis screen shows Signal Trust Analysis panel", async ({ page }) => {
  const panel = await gotoTrustPanel(page);

  await expect(panel.getByText("Signal Trust Analysis")).toBeVisible();
});

test("Trust panel describes its purpose", async ({ page }) => {
  const panel = await gotoTrustPanel(page);

  await expect(panel.getByText(/Which of your signals are stable across your outcomes/i)).toBeVisible();
  await expect(panel.getByText(/Variance and noise across imported trades/i)).toBeVisible();
});

test("Trust panel shows factor names", async ({ page }) => {
  const panel = await gotoTrustPanel(page);

  await expectTrustDataOrNoData(panel, /Conviction|Technical Signal|Market Regime|Signal Confidence/i);
});

test("Trust panel shows sigma values or no-data state", async ({ page }) => {
  const panel = await gotoTrustPanel(page);

  await expectTrustDataOrNoData(panel, /sigma\s+\d/i);
});

test("Trust panel shows trust labels or no-data state", async ({ page }) => {
  const panel = await gotoTrustPanel(page);

  await expectTrustDataOrNoData(panel, /highly trusted|trusted|moderate|noisy|very noisy|not computed|insufficient data/i);
});

test("Trust panel handles optional hero insight", async ({ page }) => {
  const panel = await gotoTrustPanel(page);

  const heroInsight = panel.getByText(/Noisiest:|Steadiest:/i);
  const factorRows = panel.getByText(/variance\s+\d/i);
  await expect(factorRows.first()).toBeVisible();

  if ((await heroInsight.count()) > 0) {
    await expect(heroInsight.first()).toBeVisible();
  }
});

test("Trust panel has no SOC vocabulary", async ({ page }) => {
  const panel = await gotoTrustPanel(page);

  await expect(panel).not.toContainText(/\bSOC\b|\bSC-\d+\b/i);
});
