import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
}

test("multi-unit dashboard endpoint returns locations", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/multi-unit/dashboard");
  expect(response.ok()).toBeTruthy();
  expect((await response.json()).locations.length).toBeGreaterThan(0);
});

test("transfer opportunities endpoint returns array", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/multi-unit/transfer-opportunities");
  expect(response.ok()).toBeTruthy();
  expect(Array.isArray((await response.json()).opportunities)).toBeTruthy();
});

test("group dashboard card renders on Performance tab", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Chain Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expect(card).toBeVisible();
});

test("group card shows per-location scorecards", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Chain Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Chicago/i, /Miami/i, /Austin/i]);
});

test("group card shows transfer opportunity or empty", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Chain Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Transfer opportunity/i, /No transfer opportunity/i]);
});

test("group flow verifies locations and kitchen language", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Chain Intelligence" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Your Chicago team's experience helps Miami/i, /Purchasing power/i]);
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector|N=/i);
});
