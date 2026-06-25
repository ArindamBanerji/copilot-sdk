import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
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
  const card = page.locator("section", { hasText: "Chain Learning" });
  await card.scrollIntoViewIfNeeded();
  await expect(card).toBeVisible();
});

test("chain card shows source and target locations", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Chain Learning" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Chicago/i, /Miami/i]);
});

test("chain card shows estimated accuracy and provenance", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Chain Learning" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/Estimated day-one accuracy/i, /Sample/i]);
});

test("chain flow checks conservation explanation", async ({ page }) => {
  await gotoPerformance(page);
  const card = page.locator("section", { hasText: "Chain Learning" });
  await card.scrollIntoViewIfNeeded();
  await expectAnyText(page, [/verify them locally/i, /learning is GREEN/i]);
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector/i);
});
