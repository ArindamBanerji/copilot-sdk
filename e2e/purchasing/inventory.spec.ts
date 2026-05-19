import { test, expect } from "../fixtures/copilot-fixture";
import { expectAnyText } from "../helpers/ui";
import { gotoInventory } from "./helpers";

test("items grouped by category", async ({ page }) => {
  await gotoInventory(page);

  await expect(page.getByText("Category summary")).toBeVisible();
  await expect(page.getByText("Waste pattern by category")).toBeVisible();
  await expectAnyText(page, [/protein/i, /produce/i, /dairy/i, /dry goods/i, /beverages/i]);
});

test("evolution panel shows variants", async ({ page }) => {
  await gotoInventory(page);

  await expect(page.getByText("System Improvements")).toBeVisible();
  await expectAnyText(page, [/promoted/i, /rejected/i, /shadow/i, /No evolution variants available/i, /V-PUR-/i]);
});

test("SC genealogy and lifecycle are backed by evolution data or empty states", async ({ page }) => {
  await gotoInventory(page);

  await expectAnyText(page, [/SC-13/i, /Rule Genealogy/i, /No evolution data yet/i, /V-PUR-/i, /Evolution variant/i]);
  await expectAnyText(page, [/SC-15/i, /Rule Lifecycle/i, /No evolution data yet/i, /promoted/i, /rejected/i, /shadow/i]);
});
