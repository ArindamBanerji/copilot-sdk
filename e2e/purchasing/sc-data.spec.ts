import { test, expect } from "../fixtures/copilot-fixture";
import { collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";
import { gotoInventory } from "./helpers";

test("SC genealogy shows live data or empty state", async ({ page }) => {
  await gotoInventory(page);

  const genealogy = page.locator("section", { hasText: /Rule Genealogy/i }).first();
  await expect(genealogy).toBeVisible();
  await expect(genealogy.getByText(/SC-13/i)).toBeVisible();
  await expectAnyText(page, [/No evolution data yet/i, /V-PUR-/i, /Evolution variant/i, /Rule genealogy event/i, /step \d+/i]);
});

test("SC lifecycle shows live data or empty state", async ({ page }) => {
  await gotoInventory(page);

  const lifecycle = page.locator("section", { hasText: /Rule Lifecycle/i }).first();
  await expect(lifecycle).toBeVisible();
  await expect(lifecycle.getByText(/SC-15/i)).toBeVisible();
  await expectAnyText(page, [/No evolution data yet/i, /V-PUR-/i, /promoted/i, /rejected/i, /shadow/i, /proposed/i]);
});

test("SC screens do not emit console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoInventory(page);

  await expectAnyText(page, [/SC-13/i, /Rule Genealogy/i]);
  await expectAnyText(page, [/SC-15/i, /Rule Lifecycle/i]);
  expectNoConsoleErrors(errors);
});
