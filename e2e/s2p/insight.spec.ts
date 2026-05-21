import { test, expect, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function openInsight(page: Page) {
  await page.goto("/");
  await clickTab(page, "Insight");
  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
}

function panel(page: Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

test("factor fingerprint shows seven S2P factors", async ({ page }) => {
  await openInsight(page);
  const fingerprint = panel(page, "Factor fingerprint");

  await expect(fingerprint).toContainText(/why this invoice was flagged/i);
  await expect(fingerprint).toContainText(/match status|match_status/i);
  await expect(fingerprint).toContainText(/amount variance|amount_variance/i);
  await expect(fingerprint).toContainText(/duplicate|supplier exception/i);
  await expect(fingerprint).toContainText(/payment terms|commodity|tax regulatory/i);
});

test("similar invoices list renders with distances", async ({ page }) => {
  await openInsight(page);
  const similar = panel(page, "Similar invoices");

  await expect(similar).toContainText(/Nearest exceptions/i);
  await expect(similar).toContainText(/distance|S2P-INV|INV-S2P/i);
});

test("cross-graph shows supplier and commodity impact correlation", async ({ page }) => {
  await openInsight(page);
  const crossGraph = panel(page, "Supplier exceptions align with process delay");

  await expect(crossGraph).toContainText(/Cross-graph signal|cross graph/i);
  await expect(crossGraph).toContainText(/supplier|commodity|impact|correlation|Aster/i);
});

test("process signals show Celonis bottleneck data", async ({ page }) => {
  await openInsight(page);
  const process = panel(page, "Process signals");

  await expect(process).toContainText(/Celonis|Purchase-to-Pay/i);
  await expect(process).toContainText(/bottleneck|variant|recommendation|Match Invoice/i);
});
