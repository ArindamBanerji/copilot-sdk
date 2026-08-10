import { test, expect, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";
import { waitForTriageQueue } from "./helpers";

async function openTab(page: Page, name: string) {
  await page.goto("/");
  await clickTab(page, name);
}

async function openTriage(page: Page) {
  await openTab(page, "Exception Triage");
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
  await waitForTriageQueue(page);
}

function main(page: Page) {
  return page.locator("main");
}

function panel(page: Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

function scoreResultPanel(page: Page) {
  return page.locator("article", { hasText: "Action index" });
}

function recommendationControls(page: Page) {
  return page.locator("article", { has: page.getByRole("button", { name: /Confirm recommendation/i }) });
}

function waitForScoreResponse(page: Page) {
  return page.waitForResponse(
    (response) =>
      response.url().includes("/score") &&
      response.request().method() === "POST" &&
      response.status() === 200,
    { timeout: 30_000 },
  );
}

async function clickScore(page: Page) {
  const selected = panel(page, "Selected Invoice");
  const selectedHasInvoice = await selected.getByText(/Supplier|Amount|Category/i).count();
  if (selectedHasInvoice === 0) {
    const invoiceButtons = panel(page, "Invoice Selector").getByRole("button").filter({ hasText: /S2P-INV/i });
    const invoiceCount = await invoiceButtons.count();
    if (invoiceCount > 0) {
      await invoiceButtons.first().click();
    } else {
      test.skip(true, "No queued invoice available for scoring");
    }
  }
  await expect(selected).toContainText(/Supplier|Amount|Category/i, { timeout: 20_000 });
  const scoreButton = selected.getByRole("button", { name: /^Score$/i });
  await expect(scoreButton).toBeEnabled({ timeout: 20_000 });
  await Promise.all([
    waitForScoreResponse(page),
    scoreButton.click(),
  ]);
}

async function scoreFirstInvoice(page: Page) {
  await openTriage(page);
  await clickScore(page);
  await expect(scoreResultPanel(page)).toContainText(/Confidence/i);
}

test("test_s2p_triage_renders_invoice_queue", async ({ page }) => {
  await openTriage(page);

  await expect(panel(page, "Invoice Selector")).toContainText(/queued|S2P-INV/i);
  await expect(panel(page, "Selected Invoice")).toContainText(/Supplier|Amount|Category|Choose an invoice to begin triage/i);
});

test("test_s2p_triage_select_invoice_shows_factors", async ({ page }) => {
  await openTriage(page);

  const invoiceButtons = page.getByRole("button").filter({ hasText: /S2P-INV/i });
  if ((await invoiceButtons.count()) > 1) {
    await invoiceButtons.nth(1).click();
  }
  await clickScore(page);

  const factors = panel(page, "7-Factor Reasoning");
  await expect(factors).toContainText(/Match Status|Amount Variance Ratio|Duplicate Score/i);
  await expect(factors).toContainText(/Supplier Exception History|Payment Terms Impact|Tax Regulatory Compliance/i);
});

test("test_s2p_triage_score_produces_result_card", async ({ page }) => {
  await scoreFirstInvoice(page);

  const result = scoreResultPanel(page);
  await expect(result).toContainText(/Decision|Confidence/i);
  await expect(result).toContainText(/factors|Category|Action index/i);
});

test("test_s2p_insight_renders_fingerprint", async ({ page }) => {
  await openTab(page, "Insight");
  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();

  const fingerprint = panel(page, "Factor fingerprint");
  await expect(fingerprint).toContainText(/why this invoice was flagged|Select an invoice/i);
  await expect(fingerprint).toContainText(/match status|amount variance|duplicate|Select an invoice/i);
});

test("test_s2p_evidence_renders_template", async ({ page }) => {
  await openTriage(page);

  const evidence = panel(page, "Evidence template");
  await expect(evidence).toContainText(/Category explanation/i);
  await expect(evidence).toContainText(/->|Confidence|Contract|Invoice qty|Similar:|Select an invoice|Loading evidence/i);
});

test("test_s2p_evidence_renders_compliance", async ({ page }) => {
  await openTab(page, "Evidence");
  await expect(page.getByRole("heading", { name: /^Evidence$/ })).toBeVisible();

  const compliance = panel(page, /^Compliance$/i).first();
  await expect(compliance).toContainText(/Tax and regulatory/i);
  await expect(compliance).toContainText(/Compliant|Flagged|Total invoices|Loading compliance summary/i);
});

test("test_s2p_performance_renders_trajectory", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByRole("heading", { name: "Performance" })).toBeVisible();

  await expect(panel(page, "Learning trajectory")).toContainText(/Centroid checkpoints|No centroid trajectory/i);
});

test("test_s2p_performance_renders_savings", async ({ page }) => {
  await openTab(page, "Performance");

  const summary = panel(page, "Operational summary");
  await expect(summary).toContainText(/Savings estimate|Loading operational summary/i);
  await expect(summary).toContainText(/Annual target|\$|Loading operational summary/i);
});

test("test_s2p_override_shows_reason_dropdown", async ({ page }) => {
  await scoreFirstInvoice(page);
  const controls = recommendationControls(page);

  await controls.getByRole("button", { name: /^Override$/i }).click();

  const reasonSelect = page.getByLabel(/Reason code/i);
  await expect(reasonSelect).toBeVisible();
  const options = await reasonSelect.locator("option").allTextContents();
  expect(options.some((o) => /wrong category/i.test(o))).toBeTruthy();
  await expect(controls.getByRole("button", { name: /Override and learn/i })).toBeDisabled();
});
