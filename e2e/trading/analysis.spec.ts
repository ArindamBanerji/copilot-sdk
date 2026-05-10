import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Analysis");
  await expect(page.getByText("YOUR TWO SELVES")).toBeVisible();
}

test("contrast card is first and visible", async ({ page }) => {
  await gotoAnalysis(page);

  const firstCard = page.locator("main section, main .copilot-card").first();
  await expect(firstCard).toContainText("YOUR TWO SELVES");
  await expectAnyText(page, [/Aligned/i, /Misaligned/i, /\d+(\.\d+)?%/]);
});

test("profile archetype shows Researcher or profile", async ({ page }) => {
  await gotoAnalysis(page);

  await expectAnyText(page, [/The Researcher/i, /The Sizer/i, /The Technician/i, /The Timer/i, /The Gut Trader/i, /Profile pending/i]);
});

test("fingerprint renders factor names", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(page.getByText("Fingerprint")).toBeVisible();
  await expectAnyText(page, [/Conviction/i, /Research Depth/i, /Technical Signal/i, /Position Size/i, /Time Horizon/i, /Market Regime/i]);
});

test("counterfactual card shows dollar or saved text", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(page.getByText("Counterfactual")).toBeVisible();
  await expectAnyText(page, [/\$\d[\d,]*/, /saved/i, /scenario/i, /No counterfactual/i]);
});
