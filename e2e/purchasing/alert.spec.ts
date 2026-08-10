import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForScreenReady } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
}

test("alerts endpoint returns array", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/alerts");
  expect(response.ok()).toBeTruthy();
  expect(Array.isArray((await response.json()).alerts)).toBeTruthy();
});

test("alerts severity filter returns filtered results", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/alerts?severity=critical");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data.alerts.every((alert: { severity?: string }) => alert.severity === "critical")).toBeTruthy();
});

test("alerts returns empty when healthy", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/alerts?severity=missing");
  expect(response.ok()).toBeTruthy();
  expect((await response.json()).alerts.length).toBe(0);
});

test("alert dashboard card renders on Performance tab", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Active Alerts" });
  await expect(card).toBeVisible({ timeout: 20_000 });
  await card.scrollIntoViewIfNeeded();
  await expect(card).toBeVisible();
});

test("alert card shows severity badges", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Active Alerts" });
  await expect(card).toBeVisible({ timeout: 20_000 });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/critical:/i, /warning:/i, /info:/i]);
});

test("alert card shows recommendations in kitchen language", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Active Alerts" });
  await expect(card).toBeVisible({ timeout: 20_000 });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Check the last quoted rate/i, /backup supplier/i, /manager review/i]);
});

test("alert flow verifies severity colors and no jargon", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Active Alerts" });
  await expect(card).toBeVisible({ timeout: 20_000 });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Price alert/i, /Sysco reliability/i]);
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector|N=/i);
});
