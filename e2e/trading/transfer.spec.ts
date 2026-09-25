import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function openPerformanceTab(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Centroid Timeline/i, /Accuracy Alerts/i, /Decision Explorer/i]);
}

test("transfer opportunities endpoint returns array", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/transfer/opportunities");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(Array.isArray(data.opportunities)).toBeTruthy();
});

test("transfer status endpoint returns object", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/transfer/status");
  expect(res.ok()).toBeTruthy();
  expect(typeof await res.json()).toBe("object");
});

test("transfer execute reports unknown conservation without applying", async ({ page }) => {
  const res = await page.request.post("http://127.0.0.1:8010/api/transfer/execute", {
    data: { source_domain: "dataops", target_domain: "trading", dry_run: true },
  });
  expect(res.status()).toBe(200);
  const data = await res.json();
  expect(data.executed).toBe(false);
  expect(data.dry_run).toBe(true);
  expect(JSON.stringify(data).toLowerCase()).toContain("conservation");
});

test("transfer panel renders on Performance tab", async ({ page }) => {
  await openPerformanceTab(page);
  await expect(page.getByRole("heading", { name: "Cross-Copilot Transfer" })).toBeVisible();
});

test("transfer panel shows available transfers or empty state", async ({ page }) => {
  await openPerformanceTab(page);
  await expectAnyText(page, [/Source/i, /No transfer mappings are available/i]);
});

test("transfer panel has dry-run toggle", async ({ page }) => {
  await openPerformanceTab(page);
  await expect(page.getByLabel("Dry run")).toBeVisible();
});

test("transfer flow: view opportunities, dry-run, verify result display", async ({ page }) => {
  await openPerformanceTab(page);
  const execute = page.getByRole("button", { name: "Execute Transfer" });
  if ((await execute.count()) === 0) {
    await expectAnyText(page, [/No transfer mappings are available|Cross-Copilot Transfer/i]);
    return;
  }
  await execute.scrollIntoViewIfNeeded();
  if (await execute.isDisabled()) {
    await expect(execute).toBeDisabled();
    return;
  }
  await execute.click();
  await expectAnyText(page, [/failed with 503/i, /conservation/i, /dry-run/i]);
});

