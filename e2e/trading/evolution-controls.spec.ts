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

test("evolution proposals endpoint returns array", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/trading/evolution/proposals");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(Array.isArray(data.proposals)).toBeTruthy();
  expect(data.provenance).toBe("demo");
});

test("evolution active endpoint returns object", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/trading/evolution/active");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(data === null || typeof data === "object").toBeTruthy();
});

test("evolution log endpoint returns array", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/trading/evolution/log");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(Array.isArray(data)).toBeTruthy();
});

test("evolution controls panel renders on Performance tab", async ({ page }) => {
  await openPerformanceTab(page);
  const heading = page.getByRole("heading", { name: "Parameter Evolution" });
  await heading.scrollIntoViewIfNeeded();
  await expect(heading).toBeVisible();
});

test("hard bounds section visible", async ({ page }) => {
  await openPerformanceTab(page);
  const heading = page.getByRole("heading", { name: "Hard Bounds Reference" });
  await heading.scrollIntoViewIfNeeded();
  await expect(heading).toBeVisible();
});
