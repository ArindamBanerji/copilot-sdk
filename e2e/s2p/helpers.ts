import { expect, type Locator, type Page } from "@playwright/test";

// The live queue is graph-backed; loading 313 pending records can exceed the
// former fixture-backed 15-second UI budget.
export async function waitForTriageQueue(page: Page, timeout = 90_000) {
  await expect(
    page.locator("article").filter({ hasText: /Invoice Selector/i }),
  ).toContainText(/S2P-INV|STRESS-CONC-S2P|INV-|queued|No invoice exceptions/i, { timeout });
}

export function waitForS2PScoreResponse(page: Page, timeout = 90_000) {
  return page.waitForResponse(
    (response) =>
      response.url().includes("/score") &&
      response.request().method() === "POST" &&
      response.status() === 200,
    { timeout },
  );
}

export function s2pScoreResult(page: Page) {
  return page.locator("article", { hasText: /Action index|Recommendation/i }).first();
}

export async function clickAndWaitForS2PScore(page: Page, scoreButton: Locator) {
  await Promise.all([
    waitForS2PScoreResponse(page),
    scoreButton.click(),
  ]);
  await expect(s2pScoreResult(page)).toBeVisible({ timeout: 30_000 });
}
