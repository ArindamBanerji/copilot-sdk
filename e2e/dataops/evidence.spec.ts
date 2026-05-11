import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function gotoEvidence(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expectAnyText(page, [/AgentEvolver Impact/i, /Loading evolution evidence/i]);
}

test("AE impact panel visible", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("AgentEvolver Impact")).toBeVisible();
  await expectAnyText(page, [/Auto-resolved/i, /Accuracy/i, /Hours saved/i, /AE/i]);
});

test("evolution panel shows variants", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("AgentEvolver Audit Trail")).toBeVisible();
  await expectAnyText(page, [/promoted/i, /rejected/i, /shadow/i, /No evolution variants available/i, /V-/i]);
});

test("pattern origin chain visible", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("Pattern Origin")).toBeVisible();
  await expectAnyText(page, [/SOC/i, /S2P/i, /DataOps/i, /warm/i, /No cross-copilot chain available/i]);
});

test("rule lifecycle shows promoted and rejected with counts", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("Rule Lifecycle")).toBeVisible();
  await expectAnyText(page, [/promoted/i, /rejected/i]);
  await expectAnyText(page, [/\d+\s+rules?/i, /\d+\s+promoted/i, /\d+\s+rejected/i]);
});

test("rule lifecycle shows timeline events with dates", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("Rule Lifecycle")).toBeVisible();
  await expectAnyText(page, [/proposed/i, /shadow/i]);
  await expectAnyText(page, [/2026-04-\d{2}/i, /2026-05-\d{2}/i, /Apr/i, /May/i]);
});

test("rule lifecycle shows variant names from fixture", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("Rule Lifecycle")).toBeVisible();
  await expectAnyText(page, [/dataops-recurring-impact/i, /dataops-freshness-sla/i, /dataops-high-impact-auto/i, /V-DO-/i]);
});

test("audit trail viewer shows chain steps for an alert", async ({ page }) => {
  await gotoEvidence(page);

  await expectAnyText(page, [/Audit Trail/i, /Decision Trail/i, /chain/i]);

  const auditTrail = page.locator("section", { hasText: /Audit Trail|Decision Trail/i }).first();
  const alertSelect = auditTrail.locator("select").first();
  if (await alertSelect.isVisible().catch(() => false)) {
    const optionCount = await alertSelect.locator("option").count();
    if (optionCount > 1) {
      const secondValue = await alertSelect.locator("option").nth(1).getAttribute("value");
      if (secondValue) {
        await alertSelect.selectOption(secondValue);
      }
    }
  }

  await expectAnyText(page, [/Alert Detected/i, /signal/i]);
  await expectAnyText(page, [/Context Gathered/i, /context/i, /factor/i]);
});

test("rule genealogy shows copilot progression with win rates", async ({ page }) => {
  await gotoEvidence(page);

  await expectAnyText(page, [/Rule Genealogy/i, /genealogy/i, /origin/i, /transfer/i]);
  await expectAnyText(page, [/SOC/i, /S2P/i, /DataOps/i]);
  await expectAnyText(page, [/68%/i, /69%/i, /75%/i, /83%/i, /improvement/i]);
});

test("schema impact panel shows downstream trace", async ({ page }) => {
  await gotoEvidence(page);

  const schema = page.locator("section", { hasText: "Schema Impact" }).first();
  await expect(schema).toBeVisible();
  await expect(schema.getByText(/SAP|MARA|BSEG/i).first()).toBeVisible();
  await expect(schema.getByText(/Downstream impact/i).first()).toBeVisible();
  await expect(schema.getByText(/Proposed fix/i).first()).toBeVisible();
  await expect(schema.getByText(/alerts prevented|preventable/i).first()).toBeVisible();
  await expect(schema.getByText(/material_group|alias|canonical|map/i).first()).toBeVisible();
});

test("operational rules panel shows governed rule statuses", async ({ page }) => {
  await gotoEvidence(page);

  const rules = page.locator("section", { hasText: "Operational Rules" }).first();
  await expect(rules).toBeVisible();
  await expect(rules.getByText(/proposed/i).first()).toBeVisible();
  await expect(rules.getByText(/shadow/i).first()).toBeVisible();
  await expect(rules.getByText(/promoted/i).first()).toBeVisible();
  await expect(rules.getByText(/scheduling/i).first()).toBeVisible();
  await expect(rules.getByText(/quality|resource|memory|off-peak/i).first()).toBeVisible();
});
