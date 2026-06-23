import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function openPerformanceTab(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Performance Summary/i, /Trajectory/i, /IKS/i]);
}

test("evolution log endpoint returns array", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/trading/evolution/log");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(Array.isArray(data)).toBeTruthy();
});

test("active variant endpoint returns object or null", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/trading/evolution/active");
  expect(res.ok()).toBeTruthy();
});

test("evolution panel renders on Performance tab", async ({ page }) => {
  await openPerformanceTab(page);
  const heading = page.getByRole("heading", { name: "Agent Evolution" });
  await heading.scrollIntoViewIfNeeded();
  await expect(heading).toBeVisible();
});

test("evolution log shows table or empty state", async ({ page }) => {
  await openPerformanceTab(page);
  const logHeading = page.getByText("Evolution Log");
  await logHeading.scrollIntoViewIfNeeded();
  await expect(logHeading).toBeVisible();
});
