import { test, expect, type Page } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

async function openTriage(page: Page) {
  await page.goto("/");
  await clickTab(page, "Exception Triage");
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
}

async function scoreFirstInvoice(page: Page) {
  await openTriage(page);
  await expectAnyText(page, [/Invoice Selector/i, /S2P-INV/i, /queued/i]);
  await page.getByRole("button", { name: /^Score$/i }).first().click();
  await expectAnyText(page, [/Recommendation/i, /Confidence/i]);
}

test("invoice list loads from queue", async ({ page }) => {
  await openTriage(page);

  await expectAnyText(page, [/Invoice Selector/i, /invoice queue/i, /queued/i]);
  await expectAnyText(page, [/S2P-INV/i, /Aster/i, /Exception/i]);
});

test("score button exists and scoring shows recommendation with confidence", async ({ page }) => {
  await scoreFirstInvoice(page);

  await expectAnyText(page, [
    /auto approve/i,
    /hold for review/i,
    /escalate to buyer/i,
    /flag leakage/i,
    /refer to specialist/i,
  ]);
  await expectAnyText(page, [/Confidence/i, /%/i]);
});

test("factor breakdown shows S2P factors", async ({ page }) => {
  await scoreFirstInvoice(page);

  await expectAnyText(page, [/7-Factor Reasoning/i, /Factor Reasoning/i]);
  await expectAnyText(page, [/Match Status/i, /Amount Variance Ratio/i, /Duplicate Score/i]);
  await expectAnyText(page, [/Supplier Exception History/i, /Payment Terms Impact/i, /Commodity Index Correlation/i, /Tax Regulatory Compliance/i]);
});

test("process context shows bottleneck when available", async ({ page }) => {
  await scoreFirstInvoice(page);

  await expectAnyText(page, [/Process Context/i, /Celonis/i]);
  await expectAnyText(page, [/Bottleneck activity/i, /Match Invoice/i, /bottleneck/i, /42/i]);
});

test("confirm button records reward or confirmed result", async ({ page }) => {
  await scoreFirstInvoice(page);

  await page.getByRole("button", { name: /Confirm recommendation/i }).first().click();
  await expectAnyText(page, [/Learning Result/i, /Reward/i, /recorded/i, /confirm/i]);
  await expectAnyText(page, [/\+[0-9]/, /Reward raw/i, /Learned/i]);
});

test("override path records reward and learned text", async ({ page }) => {
  await scoreFirstInvoice(page);

  await page.getByRole("button", { name: /^Override$/i }).first().click();
  await page.getByLabel(/Override action/i).selectOption("hold_for_review");
  await page.getByLabel(/Reason code/i).selectOption("wrong_action");
  await page.getByRole("button", { name: /Override and learn/i }).first().click();
  await expectAnyText(page, [/Learning Result/i, /Reward/i, /override/i, /Learned/i]);
});

test("conservation status visible after learn", async ({ page }) => {
  await scoreFirstInvoice(page);
  await page.getByRole("button", { name: /Confirm recommendation/i }).first().click();

  await expectAnyText(page, [/Conservation Projection/i, /conservation/i]);
  await expectAnyText(page, [/Verified/i, /accuracy/i, /penalty 5:1/i, /Status/i]);
});

test("S2P actions are canonical and SOC actions are absent", async ({ page }) => {
  await scoreFirstInvoice(page);

  await expectAnyText(page, [/auto approve/i, /hold for review/i, /escalate to buyer/i, /flag leakage/i, /refer to specialist/i]);
  await expect(page.getByText(/suppress/i)).toHaveCount(0);
  await expect(page.getByText(/refer to analyst/i)).toHaveCount(0);
  await expect(page.getByText(/escalate to analyst/i)).toHaveCount(0);
});
