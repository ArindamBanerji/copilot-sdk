import { test, expect, type Page } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

async function openInsight(page: Page) {
  await page.goto("/");
  await clickTab(page, "Insight");
  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
}

test("factor fingerprint shows seven S2P factors", async ({ page }) => {
  await openInsight(page);

  await expectAnyText(page, [/Factor fingerprint/i, /why this invoice was flagged/i]);
  await expectAnyText(page, [/match status/i, /match_status/i]);
  await expectAnyText(page, [/amount variance/i, /amount_variance/i]);
  await expectAnyText(page, [/duplicate/i, /supplier exception/i]);
  await expectAnyText(page, [/payment terms/i, /commodity/i, /tax regulatory/i]);
});

test("similar invoices list renders with distances", async ({ page }) => {
  await openInsight(page);

  await expectAnyText(page, [/Similar invoices/i, /Nearest exceptions/i]);
  await expectAnyText(page, [/distance/i, /S2P-INV/i, /INV-S2P/i]);
});

test("cross-graph shows supplier and commodity impact correlation", async ({ page }) => {
  await openInsight(page);

  await expectAnyText(page, [/Cross-graph signal/i, /cross graph/i]);
  await expectAnyText(page, [/supplier/i, /commodity/i, /impact/i, /correlation/i, /Aster/i]);
});

test("process signals show Celonis bottleneck data", async ({ page }) => {
  await openInsight(page);

  await expectAnyText(page, [/Process signals/i, /Celonis/i, /Purchase-to-Pay/i]);
  await expectAnyText(page, [/bottleneck/i, /variant/i, /recommendation/i, /Match Invoice/i]);
});
