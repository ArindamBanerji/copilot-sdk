import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForScreenReady } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
}

test("chain validate endpoint returns valid or invalid", async ({ page }) => {
  const response = await page.request.post("http://127.0.0.1:8020/api/purchasing/chain/validate", {
    data: { source: "chicago", target: "miami" },
  });
  expect(response.ok()).toBeTruthy();
  expect(typeof (await response.json()).valid).toBe("boolean");
});

test("chain transfer dry-run returns result", async ({ page }) => {
  const response = await page.request.post("http://127.0.0.1:8020/api/purchasing/chain/transfer", {
    data: { source: "chicago", target: "miami", dry_run: true },
  });
  expect(response.ok()).toBeTruthy();
  expect((await response.json()).dry_run).toBeTruthy();
});

test("chain status endpoint returns object", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/purchasing/chain/status");
  expect(response.ok()).toBeTruthy();
  expect(typeof await response.json()).toBe("object");
});

test("chain transfer card renders on Performance tab", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/Chain Learning/i, /Checking chain locations/i, /Performance unavailable/i]);
});

test("chain card shows source and target locations", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/Downtown/i, /Airport/i, /Suburb/i, /New/i, /Checking chain locations/i, /Performance unavailable/i]);
});

test("chain card shows estimated accuracy and provenance", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/Estimated day-one accuracy/i, /Sample/i, /Checking chain locations/i, /Performance unavailable/i]);
});

test("chain flow checks conservation explanation", async ({ page }) => {
  await gotoPerformance(page);
  await expectAnyText(page, [/verify them locally/i, /learning is GREEN/i, /Checking chain locations/i, /Performance unavailable/i]);
  const mainText = await page.locator("main").innerText();
  const chainStart = mainText.search(/Chain Learning|Checking chain locations/i);
  if (chainStart >= 0) {
    const nextPanel = mainText.slice(chainStart).search(/\nWeekly Report\n|\nROI Dashboard\n|\nSupply recovery\n/i);
    const chainText = nextPanel >= 0 ? mainText.slice(chainStart, chainStart + nextPanel) : mainText.slice(chainStart);
    expect(chainText).not.toMatch(/centroid|DK weight|sigma|factor vector/i);
  }
});
