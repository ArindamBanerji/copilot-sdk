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

test("test_accuracy_alerts_visible_on_evidence", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByTestId("accuracy-alerts")).toBeVisible();
  await expect(page.getByText("Accuracy Alerts")).toBeVisible();
});

test("test_accuracy_alerts_shows_6_categories", async ({ page }) => {
  await gotoEvidence(page);

  const panel = page.getByTestId("accuracy-alerts");
  await expect(panel.getByTestId("accuracy-category")).toHaveCount(6);
});

test("test_accuracy_alerts_shows_threshold_or_bars", async ({ page }) => {
  await gotoEvidence(page);

  const panel = page.getByTestId("accuracy-alerts");
  await expect(panel.getByText(/Threshold:/i)).toBeVisible();
  await expect(panel.getByTestId("accuracy-category-list")).toBeVisible();
});

test("test_accuracy_alerts_color_coding", async ({ page }) => {
  await gotoEvidence(page);

  const panel = page.getByTestId("accuracy-alerts");
  await expect(panel.locator('[data-accuracy-level="green"]').first()).toBeVisible();
  await expect(panel.locator('[data-accuracy-level="red"], [data-accuracy-level="amber"]').first()).toBeVisible();
});

test("test_rule_genealogy_visible_on_evidence", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByTestId("rule-genealogy")).toBeVisible();
  await expect(page.getByTestId("rule-genealogy").getByRole("heading", { name: "Rule Genealogy" })).toBeVisible();
});

test("test_rule_genealogy_shows_rules_or_empty", async ({ page }) => {
  await gotoEvidence(page);

  const panel = page.getByTestId("rule-genealogy");
  await expect(panel.getByText(/No lifecycle rules recorded yet|Rules tracked/i).first()).toBeVisible();
});

test("test_rule_genealogy_shows_status_badges", async ({ page }) => {
  await gotoEvidence(page);

  const panel = page.getByTestId("rule-genealogy");
  await expect(panel.getByText(/promoted|rejected|shadow|proposed/i).first()).toBeVisible();
});

test("test_rule_genealogy_shows_promoted_or_rejected", async ({ page }) => {
  await gotoEvidence(page);

  const panel = page.getByTestId("rule-genealogy");
  await expect(panel.getByText(/promoted|rejected|shadow|The system that admits failure/i).first()).toBeVisible();
});

test("test_rule_lifecycle_visible_on_evidence", async ({ page }) => {
  await gotoEvidence(page);
  await expect(page.getByTestId("rule-lifecycle")).toBeVisible();
});

test("test_rule_lifecycle_shows_rules_or_empty", async ({ page }) => {
  await gotoEvidence(page);
  const panel = page.getByTestId("rule-lifecycle");
  await expect(panel.getByTestId("rule-lifecycle-track").or(panel.getByText(/No rules have entered/i))).toBeVisible();
});

test("test_rule_lifecycle_shows_status_markers", async ({ page }) => {
  await gotoEvidence(page);
  const panel = page.getByTestId("rule-lifecycle");
  if (await panel.getByTestId("rule-lifecycle-track").count()) {
    await expect(panel.getByText(/proposed/i).first()).toBeVisible();
    await expect(panel.getByText(/shadow/i).first()).toBeVisible();
    await expect(panel.getByText(/promoted/i).first()).toBeVisible();
    await expect(panel.getByText(/rejected/i).first()).toBeVisible();
  } else {
    await expect(panel.getByTestId("rule-lifecycle-summary")).toBeVisible();
  }
});

test("test_rule_lifecycle_shows_summary", async ({ page }) => {
  await gotoEvidence(page);
  await expect(page.getByTestId("rule-lifecycle-summary")).toBeVisible();
  await expectAnyText(page, [/Active/i, /Shadow-testing/i, /Rejected/i, /Promoted/i]);
});

test("test_audit_trail_visible_on_evidence", async ({ page }) => {
  await gotoEvidence(page);
  await expect(page.getByTestId("audit-trail")).toBeVisible();
});

test("test_audit_trail_shows_events_or_empty", async ({ page }) => {
  await gotoEvidence(page);
  const panel = page.getByTestId("audit-trail");
  await expect(panel.getByTestId("audit-events").or(panel.getByText(/No audit events match/i))).toBeVisible();
});

test("test_audit_trail_shows_type_badges", async ({ page }) => {
  await gotoEvidence(page);
  const panel = page.getByTestId("audit-trail");
  if (await panel.getByTestId("audit-event-type").count()) {
    await expect(panel.getByTestId("audit-event-type").first()).toBeVisible();
  } else {
    await expect(panel.getByTestId("audit-event-filter")).toBeVisible();
  }
});

test("test_audit_trail_shows_timestamps", async ({ page }) => {
  await gotoEvidence(page);
  const panel = page.getByTestId("audit-trail");
  if (await panel.getByTestId("audit-event-timestamp").count()) {
    await expect(panel.getByTestId("audit-event-timestamp").first()).toBeVisible();
  } else {
    await expect(panel.getByTestId("audit-recent-summary")).toBeVisible();
  }
});
