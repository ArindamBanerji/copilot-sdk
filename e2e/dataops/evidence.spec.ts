import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function gotoEvidence(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expectAnyText(page, [/AgentEvolver Impact/i, /Loading evolution evidence/i]);
  await expect(page.getByText(/Loading evolution evidence/i)).toBeHidden({ timeout: 20_000 });
  await expect(page.getByText("AgentEvolver Impact")).toBeVisible({ timeout: 20_000 });
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

  await expect(page.getByRole("heading", { name: "Pattern Origin" })).toBeVisible();
  await expectAnyText(page, [/SOC/i, /S2P/i, /DataOps/i, /warm/i, /No cross-copilot chain available/i]);
});

test("rule lifecycle shows promoted and rejected with counts", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("Rule Lifecycle")).toBeVisible();
  await expectAnyText(page, [/promoted/i, /rejected/i]);
  await expectAnyText(page, [/proposed/i, /shadow/i, /promoted/i, /rejected/i]);
});

test("rule lifecycle shows timeline events with dates", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("Rule Lifecycle")).toBeVisible();
  await expectAnyText(page, [/proposed/i, /shadow/i]);
  await expectAnyText(page, [/lifecycle/i, /state/i, /promoted/i, /rejected/i]);
});

test("rule lifecycle shows variant names from fixture", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("Rule Lifecycle")).toBeVisible();
  await expectAnyText(page, [/dataops-recurring-impact/i, /dataops-freshness-sla/i, /dataops-high-impact-auto/i, /V-DO-/i]);
});

test("audit trail viewer shows chain steps for an alert", async ({ page }) => {
  await gotoEvidence(page);

  await expectAnyText(page, [/Audit Trail/i, /Decision Trail/i, /chain/i]);
  await expectAnyText(page, [/decision/i, /factors/i, /recommendation/i, /outcome/i, /No audit trail available yet/i]);
});

test("rule genealogy shows copilot progression with win rates", async ({ page }) => {
  await gotoEvidence(page);

  await expectAnyText(page, [/Rule Genealogy/i, /genealogy/i, /origin/i, /transfer/i]);
  await expectAnyText(page, [/SOC/i, /S2P/i, /DataOps/i]);
  await expectAnyText(page, [/warm/i, /transfer/i, /rule/i, /seeded evolution data/i]);
});

test("SC-13 rule genealogy shows transfer chain", async ({ page }) => {
  await gotoEvidence(page);

  const genealogy = page.locator("section", { hasText: "Rule Genealogy" }).first();
  await expect(genealogy).toBeVisible();
  await expectAnyText(page, [/SC-13/i, /genealogy/i, /warm start/i, /transfer/i, /rule/i]);
});

test("SC-15 rule lifecycle shows state transitions", async ({ page }) => {
  await gotoEvidence(page);

  const lifecycle = page.locator("section", { hasText: "Rule Lifecycle" }).first();
  await expect(lifecycle).toBeVisible();
  await expectAnyText(page, [/SC-15/i, /lifecycle/i, /promoted/i, /rejected/i, /shadow/i, /proposed/i]);
});

test("SC-16 audit trail shows decision outcome chain", async ({ page }) => {
  await gotoEvidence(page);

  const audit = page.locator("section", { hasText: "Audit Trail" }).first();
  await expect(audit).toBeVisible();
  await expectAnyText(page, [/SC-16/i, /audit/i, /trail/i, /decision/i, /outcome/i, /chain/i]);
});

test("schema impact panel shows downstream trace", async ({ page }) => {
  await gotoEvidence(page);

  const schema = page.locator("section", { hasText: "Schema Impact" }).first();
  await expect(schema).toBeVisible();
  await expect(schema.getByText(/0 changes|No schema changes detected for this system|SAP_MARA|MATKL_V2/i).first()).toBeVisible();
  await expect(schema.getByText(/0 downstream impacts|No schema changes detected for this system|Downstream impact/i).first()).toBeVisible();
  await expect(schema.getByText(/0 alerts preventable|No schema changes detected for this system|Proposed fix/i).first()).toBeVisible();
});

test("schema impact shows SAP PO count", async ({ page }) => {
  await gotoEvidence(page);

  const schema = page.locator("section", { hasText: "Schema Impact" }).first();
  await expect(schema).toBeVisible();
  await expect(schema.getByText(/purchase orders|POs/i).first()).toBeVisible();
  await expect(schema.getByText(/SAP|purchase order|PO/i).first()).toBeVisible();
});

test("operational rules panel shows governed rule statuses", async ({ page }) => {
  await gotoEvidence(page);

  const rules = page.locator("section", { hasText: "Operational Rules" }).first();
  await expect(rules).toBeVisible();
  await expect(rules.getByText(/^\d+\s+Proposed$/i).first()).toBeVisible();
  await expect(rules.getByText(/^\d+\s+Shadow$/i).first()).toBeVisible();
  await expect(rules.getByText(/^\d+\s+Promoted$/i).first()).toBeVisible();
  await expect(rules.getByText(/^Scheduling Rule$/i).first()).toBeVisible();
  await expect(rules.getByText(/quality|resource|memory|off-peak/i).first()).toBeVisible();
});
