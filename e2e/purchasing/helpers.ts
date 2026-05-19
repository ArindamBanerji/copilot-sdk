import { expect } from "../fixtures/copilot-fixture";
import { clickTab } from "../helpers/ui";
import type { Page } from "@playwright/test";

export async function gotoInventory(page: Page) {
  await page.goto("/");
  await clickTab(page, "Inventory");
  await expect(page.getByText("System Improvements")).toBeVisible({ timeout: 10_000 });
}
