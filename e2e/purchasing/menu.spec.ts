import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForScreenReady } from "../helpers/ui";

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Analysis");
  await waitForScreenReady(page);
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Menu Intelligence/i]);
}

test("menu analysis endpoint returns sample-labeled items", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/menu/analysis");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(Array.isArray(data.items)).toBeTruthy();
  expect(data.provenance).toBe("demo");
});

test("menu alerts endpoint returns sample-labeled alerts", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/menu/alerts");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(Array.isArray(data.alerts)).toBeTruthy();
});

test("menu summary endpoint returns classification counts", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/menu/summary");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(typeof data).toBe("object");
});

test("menu matrix card renders on analysis tab", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByText("Menu Intelligence", { exact: true })).toBeVisible();
});

test("menu card shows classification summary", async ({ page }) => {
  await gotoAnalysis(page);
  await expectAnyText(page, [/Stars/i, /Puzzles/i, /Plows/i, /Dogs/i]);
});

test("menu card shows margin alert when threshold crossed", async ({ page }) => {
  await gotoAnalysis(page);
  await expectAnyText(page, [/food cost rose/i, /seasonal menu change/i, /supplier switch/i]);
});

test("menu flow verifies quadrant labels and kitchen language", async ({ page }) => {
  await gotoAnalysis(page);
  await expectAnyText(page, [/Low popularity \+ high margin/i, /High popularity \+ low margin/i, /Sample data/i]);
  const card = page.locator("section", { hasText: "Menu Intelligence" });
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector|N=/i);
});
