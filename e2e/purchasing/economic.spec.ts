import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
}

test("economic model endpoint returns projected and actual", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/economic/model");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(typeof data.projected_savings).toBe("number");
  expect(typeof data.actual_savings).toBe("number");
});

test("roi summary endpoint returns readable text", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/economic/roi-summary");
  expect(response.ok()).toBeTruthy();
  expect((await response.json()).summary).toContain("Year 1");
});

test("economic dashboard card renders on Performance tab", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "ROI Dashboard" });
  await card.scrollIntoViewIfNeeded();
  await expect(card).toBeVisible();
});

test("economic card shows attainment percentage", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "ROI Dashboard" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Attainment/i, /%/]);
});

test("economic card shows sources breakdown", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "ROI Dashboard" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Waste Reduction/i, /Price Optimization/i, /Supplier Consolidation/i]);
});

test("economic flow verifies ROI and kitchen language", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "ROI Dashboard" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Year 1/i, /At \$499\/month/i, /This week/i]);
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector|N=/i);
});
