import { expect, type Page } from "@playwright/test";

export async function waitForTriageQueue(page: Page, timeout = 15_000) {
  await expect(
    page.locator("article").filter({ hasText: /Invoice Selector/i }),
  ).toContainText(/S2P-INV|No invoice exceptions/i, { timeout });
}
