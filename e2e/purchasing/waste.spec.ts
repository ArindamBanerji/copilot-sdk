import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForScreenReady } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
  await expectAnyText(page, [/Performance/i, /Cost impact/i]);
}

test("waste analysis endpoint returns item profiles", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/waste/analysis");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(Array.isArray(data)).toBeTruthy();
});

test("waste endpoint returns dollar impact", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/waste/summary");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(typeof data.weekly_waste_cost).toBe("number");
});

test("waste alert card renders with dollar impact header", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText("Waste Intelligence")).toBeVisible();
  await expectAnyText(page, [/Weekly waste cost/i, /No waste data recorded yet/i]);
});

test("waste card shows benchmark comparison bars", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/Kitchen benchmark/i, /No waste data recorded yet/i]);
});

test("waste card shows recommendations in kitchen language", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/pre-portioned/i, /Reduce par/i, /Keep current prep plan/i, /No waste data recorded yet/i]);
});

test("waste flow verifies top items and no jargon", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/Item/i, /Recommendation/i, /No waste data recorded yet/i]);
  const card = page.locator("section", { hasText: "Waste Intelligence" });
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector|N=/i);
});
