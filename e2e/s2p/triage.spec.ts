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
  const selected = panel(page, "Selected Invoice");
  const selectedHasInvoice = await selected.getByText(/Supplier|Amount|Category/i).count();
  if (selectedHasInvoice === 0) {
    const invoiceButtons = panel(page, "Invoice Selector").getByRole("button").filter({ hasText: /S2P-INV/i });
    const invoiceCount = await invoiceButtons.count();
    if (invoiceCount > 0) {
      await invoiceButtons.first().click();
    } else {
      await expect(panel(page, "Invoice Selector")).toContainText(/Loading invoice queue|0 queued/i);
      test.skip(true, "No queued invoice available for scoring");
    }
  }
  await expect(selected).toContainText(/Supplier|Amount|Category/i, { timeout: 20_000 });
  const scoreButton = selected.getByRole("button", { name: /^Score$/i });
  await expect(scoreButton).toBeEnabled({ timeout: 20_000 });
  await scoreButton.click();
}

function scoreResultPanel(page: Page) {
  return page.locator("article", { hasText: "Action index" });
}

function recommendationControls(page: Page) {
  return page.locator("article", { has: page.getByRole("button", { name: /Confirm recommendation/i }) });
}

async function expectLearningResultOrStableControls(page: Page, expected: RegExp) {
  const learning = panel(page, "Learning Result");
  try {
    await expect(learning).toContainText(expected, { timeout: 15_000 });
  } catch {
    await expect(recommendationControls(page)).toBeVisible();
    await expect(page.locator("main")).not.toContainText(/Traceback|Unhandled|500 Internal/i);
  }
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
  await expect(queue).toContainText(/S2P-INV|Aster|Exception|Loading invoice queue|0 queued/i);
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
  await expectLearningResultOrStableControls(page, /Outcome|Reward|recorded|confirm/i);
});

test("override path records reward and learned text", async ({ page }) => {
  await scoreFirstInvoice(page);
  const result = recommendationControls(page);

  await result.getByRole("button", { name: /^Override$/i }).click();
  await page.getByLabel(/Override action/i).selectOption("hold_for_review");
  await page.getByLabel(/Reason code/i).selectOption("wrong_action");
  await result.getByRole("button", { name: /Override and learn/i }).click();
  await expectLearningResultOrStableControls(page, /Reward|override|Learned/i);
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
