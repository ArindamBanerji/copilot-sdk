import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForScreenReady } from "../helpers/ui";

async function gotoInventory(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Inventory");
  await waitForScreenReady(page);
}

test("event plan endpoint returns category quantities", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/events/plan?guests=80&cuisine=mixed");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(Array.isArray(data.categories)).toBeTruthy();
});

test("event history endpoint returns array", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/events/history");
  expect(response.ok()).toBeTruthy();
  expect(Array.isArray(await response.json())).toBeTruthy();
});

test("event planner card renders on Inventory tab", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Event Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expect(card).toBeVisible();
});

test("event card shows guest count and plan table", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Event Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/80 guests/i, /Category/i, /Quantity/i]);
});

test("event card shows similar events callout or empty state", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Event Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/similar events/i, /No events planned/i]);
});

test("event flow verifies plan table and kitchen language", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Event Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/protein/i, /lbs/i, /\$1,200/i]);
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector/i);
});
