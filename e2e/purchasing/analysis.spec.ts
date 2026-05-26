import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expect(page.getByText("YOUR TWO SELVES")).toBeVisible();
}

test("contrast card visible and first", async ({ page }) => {
  await gotoAnalysis(page);

  const firstSection = page.locator("main section").first();
  await expect(firstSection).toContainText("YOUR TWO SELVES");
  await expectAnyText(page, [/Aligned/i, /Misaligned/i, /\d+(\.\d+)?%/]);
});

test("profile archetype shows Historian or profile", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(page.getByText("Your Profile")).toBeVisible();
  await expectAnyText(page, [/THE HISTORIAN/i, /THE PLANNER/i, /THE SCHEDULER/i, /THE EVENT MANAGER/i, /THE WEATHER WATCHER/i, /THE LOGISTICS PRO/i]);
});

test("fingerprint renders factors", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(page.getByRole("heading", { name: /fingerprint/i })).toBeVisible();
  await expectAnyText(page, [/Expected demand/i, /Day of week/i, /Weather/i, /Events/i, /Historical waste/i, /Supplier lead time/i]);
});

test("category accuracy shows categories", async ({ page }) => {
  await gotoAnalysis(page);

  await expect(page.getByText("Category accuracy")).toBeVisible();
  await expectAnyText(page, [/protein/i, /produce/i, /dairy/i, /dry goods/i, /beverages/i, /category/i, /accuracy/i]);
});

test("AE rule application card visible", async ({ page }) => {
  await gotoAnalysis(page);

  await expectAnyText(page, [/Counterfactual/i, /Apply AE Friday produce rule/i, /Applying proven AE rules/i]);
  await expectAnyText(page, [/Orders adjusted/i, /Dollars saved/i]);
});

test("SC-14 decision explorer renders on analysis", async ({ page }) => {
  await gotoAnalysis(page);

  await expectAnyText(page, [/SC-14/i, /Decision Explorer/i, /Purchasing decision history/i]);
  await expectAnyText(page, [/Category/i, /Action/i, /Confidence/i, /verified only/i]);
});
