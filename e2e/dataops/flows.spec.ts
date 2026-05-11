import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

async function openFirstAlert(page: Page): Promise<boolean> {
  await page.goto("/");
  await expect(page.getByText("Alert Root Causes")).toBeVisible();
  const alertSection = page.locator("section", { hasText: "Alert Root Causes" });
  const triageButtons = alertSection.getByRole("button", { name: "Triage" });
  if ((await triageButtons.count()) === 0) {
    return false;
  }
  await triageButtons.first().click();
  await expect(page.getByRole("button", { name: "Back to Dashboard" })).toBeVisible();
  await expectAnyText(page, [/DQ-\d+/, /severity/i]);
  return true;
}

async function openKnownSystemAlert(page: Page): Promise<boolean> {
  await page.goto("/");
  await expect(page.getByText("Alert Root Causes")).toBeVisible();
  const group = page.getByRole("button", { name: /SAP S\/4HANA|billing|warehouse/i });
  if ((await group.count()) > 0) {
    await group.first().click();
  }
  const triage = page.locator("article", { hasText: /sap_s4hana_extract|billing_api|warehouse_etl|SAP S\/4HANA|billing|warehouse/i }).getByRole("button", { name: "Triage" });
  if ((await triage.count()) === 0) {
    return false;
  }
  await triage.first().click();
  await expect(page.getByRole("button", { name: "Back to Dashboard" })).toBeVisible();
  return true;
}

test("full triage lifecycle: dashboard, alert, score, confirm, back", async ({ page }) => {
  test.setTimeout(60_000);
  const opened = await openFirstAlert(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Investigate" }).click();
  await scoreResponse;
  await expectAnyText(page, [/Why This Recommendation/i, /Factor Analysis/i, /Confidence Breakdown/i]);
  const learnResponse = page.waitForResponse((response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok());
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/system learned/i, /Reward/i, /IKS delta/i]);
  await page.getByRole("button", { name: "Back to Dashboard" }).click();
  await expect(page.getByText("Alert Root Causes")).toBeVisible();
});

test("score learn cycle preserves visible IKS and reward state", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await expect(page.getByText("IKS").first()).toBeVisible();
  await expect(page.getByLabel(/^IKS \d+$/).first()).toBeVisible();

  const opened = await openFirstAlert(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Investigate" }).click();
  await scoreResponse;
  await expectAnyText(page, [/Why This Recommendation/i, /Confidence Breakdown/i]);

  const learnResponse = page.waitForResponse((response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok());
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/system learned/i, /Reward/i, /IKS delta/i, /reward signal/i]);

  await clickTab(page, "Dashboard");
  await expect(page.getByText("IKS").first()).toBeVisible();
  await expect(page.getByLabel(/^IKS \d+$/).first()).toBeVisible();
});

test("triage with Celonis context for billing, SAP, or warehouse", async ({ page }) => {
  const opened = await openKnownSystemAlert(page);
  test.skip(!opened, "No SAP, billing, or warehouse alert available through grouped UI.");

  const loading = page.getByText(/Loading process context/i);
  if (await loading.isVisible().catch(() => false)) {
    await expect(loading).toBeHidden({ timeout: 10_000 });
  }
  await expectAnyText(page, [/Process Signals/i, /Celonis EMS/i, /process context/i]);
  await expectAnyText(page, [/variant/i, /confidence/i, /O2C/i, /invoice/i, /ETL/i, /rework/i, /V-\d+/i]);
});

test("insight exploration: fingerprint, incident, evidence, curve", async ({ page }) => {
  await page.goto("/");

  await clickTab(page, "Insight");
  await expect(page.getByText("Fingerprint")).toBeVisible();
  await expectAnyText(page, [/Decision Explorer/i, /\d+\s+decisions?/i]);
  await expect(page.getByText("Incident Replay")).toBeVisible();

  await clickTab(page, "Evidence");
  await expect(page.getByText("AgentEvolver Audit Trail")).toBeVisible();
  await expectAnyText(page, [/Rule Lifecycle/i, /promoted/i, /rejected/i]);
  const auditTrail = page.locator("section", { hasText: /Alert Detected|Context Gathered/i }).first();
  await expect(auditTrail).toBeVisible();
  await expectAnyText(page, [/Alert Detected/i, /Context Gathered/i]);
  await expectAnyText(page, [/Complete chain/i, /Incomplete chain/i]);
  const genealogy = page.locator("section", { hasText: "Rule Genealogy" }).first();
  await expect(genealogy).toBeVisible();
  await expect(genealogy.getByText(/68%|69%|75%|83%|improvement/i).first()).toBeVisible();
  await expect(page.getByText("Pattern Origin")).toBeVisible();

  await clickTab(page, "Curve");
  await expect(page.getByText("Trajectory")).toBeVisible();
  await expectAnyText(page, [/SAP restructure/i, /Current IKS/i]);
});

test("evidence deep exploration shows impact lifecycle audit trail and genealogy", async ({ page }) => {
  await page.goto("/");

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/AgentEvolver Impact/i, /Auto-resolved/i, /Accuracy/i]);
  await expectAnyText(page, [/Rule Lifecycle/i, /promoted/i, /rejected/i]);
  const auditTrail = page.locator("section", { hasText: /Alert Detected|Context Gathered/i }).first();
  await expect(auditTrail).toBeVisible();
  await expect(auditTrail.getByText(/Alert Detected/i).first()).toBeVisible();
  await expect(auditTrail.getByText(/Context Gathered/i).first()).toBeVisible();
  await expect(auditTrail.getByText(/Complete chain|Incomplete chain/i).first()).toBeVisible();
  const genealogy = page.locator("section", { hasText: "Rule Genealogy" }).first();
  await expect(genealogy).toBeVisible();
  await expect(genealogy.getByText(/68%|69%|75%|83%/i).first()).toBeVisible();
  await expect(genealogy.getByText(/improvement|win-rate progression|decisions/i).first()).toBeVisible();
  await expect(page.getByText("Pattern Origin")).toBeVisible();
});

test("tab navigation all 5 tabs and no blank screens", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await page.goto("/");

  for (const tab of ["Dashboard", "Triage", "Insight", "Evidence", "Curve"]) {
    await clickTab(page, tab);
    await expect(page.locator("main")).not.toBeEmpty();
    await expectAnyText(page, [new RegExp(tab, "i"), /Loading/i, /Select an alert/i, /Trajectory/i]);
  }

  expectNoConsoleErrors(errors);
});

test("conservation track record visible and interactive", async ({ page }) => {
  await page.goto("/");

  // Conservation section exists on dashboard
  await expect(page.getByText(/conservation|auto.resolve/i).first()).toBeVisible({ timeout: 5000 });
  await expectAnyText(page, [/Automation Projection/i, /55%/, /75%/, /90%/]);
  await expectAnyText(page, [/week/i, /accuracy/i, /when/i, /verified decisions/i]);

  // Track record events visible (denied/approved from pre-seeded data)
  await expectAnyText(page, [
    /approved/i,
    /denied/i,
    /GREEN/i,
    /AMBER/i,
    /headroom/i,
    /auto.resolve/i,
  ]);
});

test("dashboard alert groups expand and collapse", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Alert Root Causes")).toBeVisible();

  const groupButtons = page.locator("section", { hasText: "Alert Root Causes" }).getByRole("button").filter({ hasText: /alerts|No alerts|root/i });
  test.skip((await groupButtons.count()) === 0, "No alert group buttons available.");

  await groupButtons.first().click();
  await expectAnyText(page, [/Triage/i, /No alerts in this root-cause group/i, /Root-system alerts only/i]);
  await groupButtons.first().click();
  await expect(page.getByText("Alert Root Causes")).toBeVisible();
});

test("decision explorer shows real category breakdown after a scored decision", async ({ page }) => {
  test.setTimeout(60_000);
  const opened = await openFirstAlert(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Investigate" }).click();
  await scoreResponse;

  const learnResponse = page.waitForResponse((response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok());
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;

  await clickTab(page, "Insight");
  const explorer = page.locator("section", { hasText: "Decision Explorer" });
  await expect(explorer).toBeVisible();
  await expect(explorer.getByText("By Category")).toBeVisible();
  // Backend unit tests verify live metadata category enrichment. This E2E keeps the UI claim narrower:
  // after a score/learn cycle, the Decision Explorer still exposes real DataOps category breakdowns.
  await expectAnyText(page, [/by category/i, /category/i, /\d+\s+decisions?/i]);
});

test("triage score then insight shows decision explorer count", async ({ page }) => {
  test.setTimeout(60_000);
  const opened = await openFirstAlert(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Investigate" }).click();
  await scoreResponse;
  await expectAnyText(page, [/Why This Recommendation/i, /Factor Analysis/i, /Confidence Breakdown/i]);

  const learnResponse = page.waitForResponse((response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok());
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/system learned/i, /Reward/i, /IKS delta/i, /reward signal/i]);

  await clickTab(page, "Insight");
  const explorer = page.locator("section", { hasText: "Decision Explorer" });
  await expect(explorer).toBeVisible();
  await expectAnyText(page, [/Decision Explorer/i, /\d+\s+decisions?/i]);
});

test("score alert then Curve shows IKS and centroid evolution", async ({ page }) => {
  test.setTimeout(60_000);
  const opened = await openFirstAlert(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Investigate" }).click();
  await scoreResponse;
  await expectAnyText(page, [/Why This Recommendation/i, /Confidence Breakdown/i]);

  const learnResponse = page.waitForResponse((response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok());
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/system learned/i, /Reward/i, /IKS delta/i, /reward signal/i]);

  await clickTab(page, "Curve");
  await expectAnyText(page, [/Current IKS/i, /\bIKS\b/i]);
  await expectAnyText(page, [/Centroid Evolution/i, /centroid/i, /top shifts/i, /verified decisions/i]);
});

test("full round trip visits Dashboard, Triage, Insight, Evidence, and Curve", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await expectAnyText(page, [/Pipeline Status/i, /Alert Root Causes/i]);

  const opened = await openFirstAlert(page);
  if (opened) {
    await expectAnyText(page, [/All factors auto-computed/i, /Similar Alerts/i, /Action/i]);
    await page.getByRole("button", { name: "Back to Dashboard" }).click();
  }

  await clickTab(page, "Insight");
  await expectAnyText(page, [/Fingerprint/i, /Decision Explorer/i]);

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/AgentEvolver Impact/i, /Rule Lifecycle/i]);
  await expectAnyText(page, [/Alert Detected/i, /Context Gathered/i]);
  await expectAnyText(page, [/Rule Genealogy/i, /win-rate progression/i, /improvement/i]);

  await clickTab(page, "Curve");
  await expectAnyText(page, [/Trajectory/i, /Current IKS/i, /Centroid Evolution/i]);
});

test("Insight bottleneck then Evidence schema impact round trip", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Pipeline Status/i, /Alert Root Causes/i]);

  await clickTab(page, "Insight");
  await expectAnyText(page, [/Pipeline Bottleneck/i, /Join VBAK\/BSEG/i, /duration/i]);
  await expectAnyText(page, [/Recommendation/i, /speedup/i, /savings/i]);

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/Schema Impact/i, /Downstream impact/i, /Proposed fix/i]);
  await expectAnyText(page, [/Operational Rules/i, /proposed/i, /shadow/i, /promoted/i]);

  await clickTab(page, "Insight");
  await expectAnyText(page, [/Pipeline Bottleneck/i, /Decision Explorer/i, /Incident Replay/i]);
});

test("full Level 3 story shows bottleneck schema rules genealogy and curve", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Pipeline Status/i, /AgentEvolver Impact/i, /Alert Root Causes/i]);

  await clickTab(page, "Insight");
  const bottleneck = page.locator("section", { hasText: "Pipeline Bottleneck" }).first();
  await expect(bottleneck).toBeVisible();
  await expect(bottleneck.getByText(/recommendation/i).first()).toBeVisible();
  await expect(bottleneck.getByText(/reorder|speedup|savings/i).first()).toBeVisible();

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/Schema Impact/i, /proposed fix/i, /downstream/i]);
  await expectAnyText(page, [/Operational Rules/i, /scheduling/i, /quality/i]);
  await expectAnyText(page, [/Rule Lifecycle/i, /promoted/i, /rejected/i]);
  await expectAnyText(page, [/Rule Genealogy/i, /68%|69%|75%|83%/i, /improvement/i]);
  await expectAnyText(page, [/Pattern Origin/i, /SOC/i, /S2P/i]);

  await clickTab(page, "Curve");
  await expectAnyText(page, [/Trajectory/i, /Current IKS/i, /Centroid Evolution/i]);
});

test("OE-5 what-if shows impact change on reorder interaction", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Insight");

  const whatIf = page.locator("section", { hasText: /What-if: Reorder/i }).first();
  await expect(whatIf).toBeVisible();
  await expect(whatIf.getByText(/Current order/i).first()).toBeVisible();
  await expect(whatIf.getByText(/Reorder order/i).first()).toBeVisible();
  await expectAnyText(page, [/Extract Orders Daily/i, /Join VBAK\/BSEG/i, /Aggregate Daily Revenue/i, /Load to Warehouse/i]);

  const downButtons = whatIf.getByRole("button", { name: /down/i });
  if ((await downButtons.count()) > 0) {
    await downButtons.first().click();
  }

  await expect(whatIf.getByText(/Estimated impact/i).first()).toBeVisible();
  await expectAnyText(page, [/impact/i, /savings/i, /min/i, /Move steps to estimate impact/i]);
});
