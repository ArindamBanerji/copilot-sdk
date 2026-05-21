import { test, expect, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function openTriage(page: Page) {
  await page.goto("/");
  await clickTab(page, "Exception Triage");
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
}

function panel(page: Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

async function clickScore(page: Page) {
  await panel(page, "Selected Invoice").getByRole("button", { name: /^Score$/i }).click();
}

function scoreResultPanel(page: Page) {
  return page.locator("article", { hasText: "Action index" });
}

function recommendationControls(page: Page) {
  return page.locator("article", { has: page.getByRole("button", { name: /Confirm recommendation/i }) });
}

async function scoreFirstInvoice(page: Page) {
  await openTriage(page);
  await expect(panel(page, "Invoice Selector")).toContainText(/S2P-INV|queued/i);
  await clickScore(page);
  await expect(scoreResultPanel(page)).toContainText(/Recommendation|Confidence/i);
}

test("invoice list loads from queue", async ({ page }) => {
  await openTriage(page);
  const queue = panel(page, "Invoice Selector");

  await expect(queue).toContainText(/invoice queue|queued/i);
  await expect(queue).toContainText(/S2P-INV|Aster|Exception/i);
});

test("score button exists and scoring shows recommendation with confidence", async ({ page }) => {
  await scoreFirstInvoice(page);
  const result = scoreResultPanel(page);

  await expect(result).toContainText(/auto approve|hold for review|escalate to buyer|flag leakage|refer to specialist/i);
  await expect(result).toContainText(/Confidence|%/i);
});

test("factor breakdown shows S2P factors", async ({ page }) => {
  await scoreFirstInvoice(page);
  const factors = panel(page, /7-Factor Reasoning|Factor Reasoning/i);

  await expect(factors).toContainText(/Match Status|Amount Variance Ratio|Duplicate Score/i);
  await expect(factors).toContainText(/Supplier Exception History|Payment Terms Impact|Commodity Index Correlation|Tax Regulatory Compliance/i);
});

test("process context shows bottleneck when available", async ({ page }) => {
  await scoreFirstInvoice(page);
  const process = panel(page, /Process Context/i);

  await expect(process).toContainText(/Celonis/i);
  await expect(process).toContainText(/Bottleneck activity|Match Invoice|bottleneck|42/i);
});

test("confirm button records reward or confirmed result", async ({ page }) => {
  await scoreFirstInvoice(page);

  await recommendationControls(page).getByRole("button", { name: /Confirm recommendation/i }).click();
  await expect(panel(page, "Learning Result")).toContainText(/Outcome|Reward|recorded|confirm/i, { timeout: 15_000 });
});

test("override path records reward and learned text", async ({ page }) => {
  await scoreFirstInvoice(page);
  const result = recommendationControls(page);

  await result.getByRole("button", { name: /^Override$/i }).click();
  await page.getByLabel(/Override action/i).selectOption("hold_for_review");
  await page.getByLabel(/Reason code/i).selectOption("wrong_action");
  await result.getByRole("button", { name: /Override and learn/i }).click();
  await expect(panel(page, "Learning Result")).toContainText(/Reward|override|Learned/i, { timeout: 15_000 });
});

test("conservation status visible after learn", async ({ page }) => {
  await scoreFirstInvoice(page);
  await recommendationControls(page).getByRole("button", { name: /Confirm recommendation/i }).click();

  const projection = panel(page, "Conservation Projection");
  await expect(projection).toContainText(/conservation/i);
  await expect(projection).toContainText(/Verified|accuracy|penalty 5:1|Status/i);
});

test("S2P actions are canonical and SOC actions are absent", async ({ page }) => {
  await scoreFirstInvoice(page);

  await expect(scoreResultPanel(page)).toContainText(/auto approve|hold for review|escalate to buyer|flag leakage|refer to specialist/i);
  const main = page.locator("main");
  await expect(main).not.toContainText(/suppress/i);
  await expect(main).not.toContainText(/refer to analyst/i);
  await expect(main).not.toContainText(/escalate to analyst/i);
});
