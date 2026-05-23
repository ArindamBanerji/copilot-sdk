import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Analysis");
  await expect(page.getByText("YOUR TWO SELVES")).toBeVisible();
}

test("contrast card is first and visible", async ({ page }) => {
  await gotoAnalysis(page);

  const contrastCard = page.locator("main .copilot-card").filter({
    has: page.getByText("YOUR TWO SELVES"),
  }).first();
  await expect(contrastCard).toBeVisible();
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

test("analysis shows edge and noise sections", async ({ page }) => {
  await gotoAnalysis(page);

  await expectAnyText(page, [/YOUR EDGE/i, /YOUR NOISE/i, /clean/i, /noisy/i, /moderate/i]);
});

test("analysis shows behavioral subsections", async ({ page }) => {
  await gotoAnalysis(page);

  await expectAnyText(page, [/Day of Week/i, /Research Impact/i, /Regime Analysis/i, /Risk Management/i]);
});

test("SC-14 decision explorer renders on analysis", async ({ page }) => {
  await gotoAnalysis(page);

  await expectAnyText(page, [/SC-14/i, /Decision Explorer/i]);
  await expectAnyText(page, [/Category/i, /Action/i, /Confidence/i, /verified only/i]);
});

test("SC-13 and SC-16 analysis evidence panels render", async ({ page }) => {
  await gotoAnalysis(page);

  await expectAnyText(page, [/SC-13/i, /Rule Genealogy/i, /No evolution data yet/i, /Evolution variant/i, /Lifecycle event/i]);
  await expectAnyText(page, [/SC-15/i, /Rule Lifecycle/i, /No evolution data yet/i, /promoted/i, /rejected/i, /shadow/i]);
  await expectAnyText(page, [/SC-16/i, /Audit Trail/i, /decision/i, /outcome/i, /No audit trail available yet/i]);
});
