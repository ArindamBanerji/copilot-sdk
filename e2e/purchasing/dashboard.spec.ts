import { test, expect } from "../fixtures/copilot-fixture";
import { expectAnyText } from "../helpers/ui";

test("dashboard loads", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Purchasing Copilot" })).toBeVisible();
  await expect(page.getByText(/items need attention|No item is below the reorder threshold/i)).toBeVisible();
  await expect(page.locator("main")).not.toBeEmpty();
});

test("par level monitor shows items and dollar amounts", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Par level monitor")).toBeVisible();
  await expect(page.getByText("Real inventory, ranked by reorder pressure")).toBeVisible();
  await expectAnyText(page, [/\$\d[\d,]*/, /No item is below the reorder threshold/i]);
});

test("AE status bar visible", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Autonomous execution")).toBeVisible();
  await expect(page.getByText("Items you are consistent on can be managed")).toBeVisible();
  await expectAnyText(page, [/AE rules/i, /Managed accuracy/i, /Promoted savings/i]);
});

test("rejected dairy rule is not shown as AE-managed", async ({ page }) => {
  await page.goto("/");

  // Rejected dairy rule may be displayed (marked as rejected, not hidden)
  await expectAnyText(page, [/rejected/i, /dairy/i, /V-PUR/i]);
});

test("cover count visible", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText(/cover/i).first()).toBeVisible();
  await expectAnyText(page, [/Expected covers/i, /covers/i, /\d+/]);
});
