import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function gotoInventory(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Inventory");
  await waitForAppShell(page);
}

test("delivery today endpoint returns schedule", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/delivery/today");
  expect(response.ok()).toBeTruthy();
  expect("deliveries" in await response.json()).toBeTruthy();
});

test("delivery consolidation endpoint returns suggestions", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/delivery/consolidation");
  expect(response.ok()).toBeTruthy();
  expect("suggestions" in await response.json()).toBeTruthy();
});

test("delivery schedule card renders on Inventory tab", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Delivery Schedule" });
  await card.scrollIntoViewIfNeeded();
  await expect(card).toBeVisible();
});

test("delivery card shows supplier time windows or empty state", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Delivery Schedule" });
  await card.scrollIntoViewIfNeeded();
  await expect(card.getByText(/Time window|No deliveries scheduled/i).first()).toBeVisible();
});

test("delivery card shows consolidation callout and provenance", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Delivery Schedule" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Combine/i, /Sample/i]);
});

test("delivery flow checks schedule table and kitchen language", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Delivery Schedule" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Supplier/i, /Time window/i, /receiving/i]);
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector/i);
});
