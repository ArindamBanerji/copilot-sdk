import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);
}

test("discovery insights endpoint returns array", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/discovery/insights");
  expect(response.ok()).toBeTruthy();
  expect(Array.isArray((await response.json()).insights)).toBeTruthy();
});

test("discovery digest endpoint returns top insights", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/discovery/digest");
  expect(response.ok()).toBeTruthy();
  expect(Array.isArray((await response.json()).digest)).toBeTruthy();
});

test("discovery digest card renders on Analysis tab", async ({ page }) => {
  await gotoAnalysis(page);
  const card = page.locator("section", { hasText: "Cross-Category Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expect(card).toBeVisible();
});

test("discovery card shows insight cards or empty state", async ({ page }) => {
  await gotoAnalysis(page);
  const card = page.locator("section", { hasText: "Cross-Category Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Weekly digest/i, /Not enough decisions/i]);
});

test("discovery card uses kitchen language", async ({ page }) => {
  await gotoAnalysis(page);
  const card = page.locator("section", { hasText: "Cross-Category Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/kitchen pattern/i, /manager checklist/i, /receiving timing/i]);
});

test("discovery flow verifies insights and no jargon", async ({ page }) => {
  await gotoAnalysis(page);
  const card = page.locator("section", { hasText: "Cross-Category Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/protein/i, /produce/i]);
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector|N=/i);
});
