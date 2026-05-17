import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Analysis");
  await expect(page.getByText("YOUR TWO SELVES")).toBeVisible();
}

test("SC genealogy shows live data or empty state", async ({ page }) => {
  await gotoAnalysis(page);

  const genealogy = page.locator("section", { hasText: /Rule Genealogy/i }).first();
  await expect(genealogy).toBeVisible();
  await expect(genealogy.getByText(/SC-13/i)).toBeVisible();
  await expectAnyText(page, [/No evolution data yet/i, /Evolution variant/i, /Lifecycle event/i, /step \d+/i]);
});

test("SC lifecycle shows live data or empty state", async ({ page }) => {
  await gotoAnalysis(page);

  const lifecycle = page.locator("section", { hasText: /Rule Lifecycle/i }).first();
  await expect(lifecycle).toBeVisible();
  await expect(lifecycle.getByText(/SC-15/i)).toBeVisible();
  await expectAnyText(page, [/No evolution data yet/i, /promoted/i, /rejected/i, /shadow/i, /proposed/i, /Evolution variant/i]);
});

test("SC screens do not emit console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoAnalysis(page);

  await expectAnyText(page, [/SC-13/i, /Rule Genealogy/i]);
  await expectAnyText(page, [/SC-15/i, /Rule Lifecycle/i]);
  await page.waitForTimeout(500);
  expectNoConsoleErrors(errors);
});
