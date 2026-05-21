import { type Locator, type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

function panelByHeading(page: Page, heading: string | RegExp): Locator {
  return page
    .locator("h1, h2, h3, h4", { hasText: heading })
    .locator("xpath=ancestor::*[self::article or self::section or contains(concat(' ', normalize-space(@class), ' '), ' copilot-card ')][1]");
}

async function gotoDashboard(page: Page) {
  await page.goto("/");
  await expect(panelByHeading(page, "Pipeline Status")).toBeVisible();
}

async function gotoInsight(page: Page) {
  await page.goto("/");
  await clickTab(page, "Insight");
  await expectAnyText(page, [/Pipeline Bottleneck/i, /Loading DataOps insight/i]);
}

async function gotoEvidence(page: Page) {
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expectAnyText(page, [/AgentEvolver Impact/i, /Loading evolution evidence/i]);
}

test("Act 1 WHERE: Dashboard shows pipeline systems and alert groups", async ({ page }) => {
  await gotoDashboard(page);

  const pipeline = panelByHeading(page, "Pipeline Status");
  await expect(pipeline).toBeVisible();
  await expect(pipeline.getByText(/systems/i)).toBeVisible();
  await expectAnyText(page, [/SAP S\/4HANA/i, /Warehouse ETL/i, /Payment Gateway/i]);

  const alerts = panelByHeading(page, "Alert Root Causes");
  await expect(alerts).toBeVisible();
  await expect(alerts.getByText(/root causes|total alerts/i)).toBeVisible();
});

test("Act 2 WHY: Insight shows bottleneck and schema impact", async ({ page }) => {
  await gotoInsight(page);

  const bottleneck = panelByHeading(page, "Pipeline Bottleneck");
  await expect(bottleneck).toBeVisible();
  await expect(bottleneck.getByText(/duration|runtime|bottleneck/i)).toBeVisible();
  await expect(bottleneck.getByText(/Join VBAK\/BSEG|join/i)).toBeVisible();

  await clickTab(page, "Evidence");
  const schema = panelByHeading(page, "Schema Impact");
  await expect(schema).toBeVisible();
  await expect(schema.getByText(/Downstream impact/i)).toBeVisible();
  await expect(schema.getByText(/Proposed fix/i)).toBeVisible();
});

test("Act 3 WHAT: Insight shows what-if and recommendation", async ({ page }) => {
  await gotoInsight(page);

  const whatIf = panelByHeading(page, /What-if: Reorder/i);
  await expect(whatIf).toBeVisible();
  await expect(whatIf.getByText(/Current order/i)).toBeVisible();
  await expect(whatIf.getByText(/Reorder order/i)).toBeVisible();
  await expect(whatIf.getByText(/Estimated impact|savings|speedup/i)).toBeVisible();
});

test("Act 4 LEARN: Dashboard shows conservation and IKS evidence", async ({ page }) => {
  await gotoDashboard(page);

  const conservation = panelByHeading(page, /^Conservation$/i);
  await expect(conservation).toBeVisible();
  await expect(conservation.getByText(/threshold|theta|min|penalty/i)).toBeVisible();
  await expect(page.locator('[aria-label^="IKS "]')).not.toHaveCount(0);
  await expectAnyText(page, [/accuracy/i, /verified decisions/i, /decision/i]);
});

test("Act 5 TRANSFER: Evidence shows Pattern Transfer Status", async ({ page }) => {
  await gotoEvidence(page);

  const transfer = panelByHeading(page, "Pattern Transfer Status");
  await expect(transfer).toBeVisible();
  await expect(transfer.getByText(/Total transfers/i)).toBeVisible();
  await expect(transfer.getByText(/Cumulative savings/i)).toBeVisible();
  await expect(transfer.getByText(/Confidence/i)).toBeVisible();
});

test("Act 5 TRANSFER: transfer panel shows all three statuses", async ({ page }) => {
  await gotoEvidence(page);

  const transfer = panelByHeading(page, "Pattern Transfer Status");
  await expect(transfer).toBeVisible();
  const summary = transfer.locator("div").filter({ hasText: /Total transfers/i }).filter({ hasText: /Cumulative savings/i });
  await expect(summary.getByText(/Active/i)).toBeVisible();
  await expect(summary.getByText(/Monitoring/i)).toBeVisible();

  const activeCard = transfer.locator("section").filter({ hasText: /TRF-001/i });
  const monitoringCard = transfer.locator("section").filter({ hasText: /TRF-002/i });
  const pendingCard = transfer.locator("section").filter({ hasText: /TRF-003/i });
  await expect(activeCard.getByText(/^Active$/i)).toBeVisible();
  await expect(monitoringCard.getByText(/^Monitoring$/i)).toBeVisible();
  await expect(pendingCard.getByText(/^Pending Verification$/i)).toBeVisible();
});

test("Full 5-act story traverses all screens without console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoDashboard(page);
  await expect(panelByHeading(page, "Pipeline Status")).toBeVisible();
  await expect(panelByHeading(page, "Alert Root Causes")).toBeVisible();

  await clickTab(page, "Insight");
  await expect(panelByHeading(page, "Pipeline Bottleneck")).toBeVisible();
  await expect(panelByHeading(page, /What-if: Reorder/i)).toBeVisible();

  await clickTab(page, "Dashboard");
  await expect(panelByHeading(page, /^Conservation$/i)).toBeVisible();
  await expect(page.locator('[aria-label^="IKS "]')).not.toHaveCount(0);

  await clickTab(page, "Evidence");
  await expect(panelByHeading(page, "Schema Impact")).toBeVisible();
  await expect(panelByHeading(page, "Pattern Transfer Status")).toBeVisible();

  expectNoConsoleErrors(errors);
});

test("Transfer panel has no SOC vocabulary", async ({ page }) => {
  await gotoEvidence(page);

  const transfer = panelByHeading(page, "Pattern Transfer Status");
  await expect(transfer).toBeVisible();
  await expect(transfer.getByText(/DataOps|Pattern Transfer Status|transfer/i)).toBeVisible();

  const panelText = await transfer.innerText();
  expect(panelText).not.toMatch(/\bSOC\b|security operations|security alert/i);
});
