import { test, expect, type Page } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

async function openTab(page: Page, name: string) {
  await page.goto("/");
  await clickTab(page, name);
}

async function openTriage(page: Page) {
  await openTab(page, "Exception Triage");
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
}

async function scoreFirstInvoice(page: Page) {
  await openTriage(page);
  await expectAnyText(page, [/Invoice Selector/i, /queued/i, /S2P-INV/i]);
  await page.getByRole("button", { name: /^Score$/i }).first().click();
  await expectAnyText(page, [/Recommendation/i, /Confidence/i]);
}

test("test_s2p_triage_renders_invoice_queue", async ({ page }) => {
  await openTriage(page);

  await expectAnyText(page, [/Invoice Selector/i, /queued/i, /S2P-INV/i]);
  await expectAnyText(page, [/Selected Invoice/i, /Supplier/i, /Amount/i, /Category/i]);
});

test("test_s2p_triage_select_invoice_shows_factors", async ({ page }) => {
  await openTriage(page);

  const invoiceButtons = page.getByRole("button").filter({ hasText: /S2P-INV/i });
  if ((await invoiceButtons.count()) > 1) {
    await invoiceButtons.nth(1).click();
  }
  await page.getByRole("button", { name: /^Score$/i }).first().click();

  await expectAnyText(page, [/7-Factor Reasoning/i]);
  await expectAnyText(page, [/Match Status/i, /Amount Variance Ratio/i, /Duplicate Score/i]);
  await expectAnyText(page, [/Supplier Exception History/i, /Payment Terms Impact/i, /Tax Regulatory Compliance/i]);
});

test("test_s2p_triage_score_produces_result_card", async ({ page }) => {
  await scoreFirstInvoice(page);

  await expectAnyText(page, [/Recommendation/i, /Decision/i, /Confidence/i]);
  await expectAnyText(page, [/factors/i, /Category/i, /Action index/i]);
});

test("test_s2p_insight_renders_fingerprint", async ({ page }) => {
  await openTab(page, "Insight");
  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();

  await expectAnyText(page, [/Factor fingerprint/i, /why this invoice was flagged/i]);
  await expectAnyText(page, [/match status/i, /amount variance/i, /duplicate/i]);
});

test("test_s2p_evidence_renders_template", async ({ page }) => {
  await openTriage(page);

  await expectAnyText(page, [/Evidence template/i, /Category explanation/i]);
  await expectAnyText(page, [/->/i, /Confidence/i, /Contract/i, /Invoice qty/i, /Similar:/i]);
});

test("test_s2p_evidence_renders_compliance", async ({ page }) => {
  await openTab(page, "Evidence");
  await expect(page.getByRole("heading", { name: "Evidence", exact: true })).toBeVisible();

  await expectAnyText(page, [/Compliance/i, /Tax and regulatory/i]);
  await expectAnyText(page, [/Compliant/i, /Flagged/i, /Total invoices/i]);
});

test("test_s2p_performance_renders_trajectory", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByRole("heading", { name: "Performance" })).toBeVisible();

  await expectAnyText(page, [/Learning trajectory/i, /Centroid checkpoints/i, /No centroid trajectory/i]);
});

test("test_s2p_performance_renders_savings", async ({ page }) => {
  await openTab(page, "Performance");

  await expectAnyText(page, [/Operational summary/i, /Savings estimate/i]);
  await expectAnyText(page, [/Annual target/i, /\$/i]);
});

test("test_s2p_override_shows_reason_dropdown", async ({ page }) => {
  await scoreFirstInvoice(page);

  await page.getByRole("button", { name: /^Override$/i }).first().click();

  await expect(page.getByLabel(/Reason code/i)).toBeVisible();
  await expectAnyText(page, [/Wrong category assigned/i, /Wrong action recommended/i, /Missing relevant context/i]);
  await expect(page.getByRole("button", { name: /Override and learn/i })).toBeDisabled();
});
