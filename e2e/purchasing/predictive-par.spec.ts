import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForScreenReady } from "../helpers/ui";

async function gotoInventory(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Inventory");
  await waitForScreenReady(page);
}

test("par predict endpoint returns adjusted par", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/par/predict?item=salmon&category=protein&date=2026-06-26");
  expect(response.ok()).toBeTruthy();
  expect(Number((await response.json()).adjusted_par)).toBeGreaterThan(0);
});

test("par predict-week endpoint returns 7-day forecast", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/par/predict-week");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(Array.isArray(data.items)).toBeTruthy();
  expect(data.items.length).toBeGreaterThanOrEqual(7);
});

test("predictive par card renders on Inventory tab", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Smart Par Levels" });
  await card.scrollIntoViewIfNeeded();
  await expect(card).toBeVisible();
});

test("par card shows two-tier table or empty state", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Smart Par Levels" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Tue-Thu par/i, /Connect POS/i]);
});

test("par card shows dollar impact", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Smart Par Levels" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/\$180\/week/i, /Weekly waste reduction/i]);
});

test("par flow verifies kitchen language", async ({ page }) => {
  await gotoInventory(page);
  const card = page.locator("section", { hasText: "Smart Par Levels" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Friday needs/i, /Slow days/i]);
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector/i);
});
