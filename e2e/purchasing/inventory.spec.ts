import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function gotoInventory(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Inventory");
  await expect(page.getByText("System Improvements")).toBeVisible();
}

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
