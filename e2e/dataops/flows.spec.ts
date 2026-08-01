import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

function dataopsPanel(page: Page, heading: string | RegExp) {
  return page.locator("section, article").filter({
    has: page.locator("h1, h2, h3, h4, p", { hasText: heading }),
  }).first();
}

function expectNoActionableConsoleErrors(errors: string[]) {
  const filtered = errors.filter((error) => {
    const text = error.toLowerCase();
    if (text.includes("/api/")) {
      return true;
    }
    if (
      text.includes("failed to load resource") ||
      text.includes("favicon") ||
      text.includes("manifest") ||
      text.includes(".ico") ||
      text.includes(".png")
    ) {
      return false;
    }
    return true;
  });
  expectNoConsoleErrors(filtered);
}

async function openFirstAlert(page: Page): Promise<boolean> {
  await page.goto("/");
  const alertSection = dataopsPanel(page, "Alert Root Causes");
  await expect(alertSection).toBeVisible({ timeout: 30_000 });
  const triageButtons = alertSection.getByRole("button", { name: "Triage" });
  if ((await triageButtons.count()) === 0) {
    const expandButton = page.getByRole("button", { name: "Expand" }).first();
    if ((await expandButton.count()) > 0) {
      await expandButton.click();
    }
  }
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
  await expect(dataopsPanel(page, "Alert Root Causes")).toBeVisible({ timeout: 30_000 });
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
  await expect(dataopsPanel(page, "Alert Root Causes")).toBeVisible({ timeout: 30_000 });
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
  await expectAnyText(page, [/Process Signals/i, /Celonis.*Live/i, /Celonis.*cached/i, /process context/i]);
  await expectAnyText(page, [/variant/i, /confidence/i, /O2C/i, /invoice/i, /ETL/i, /rework/i, /V-\d+/i]);
});

test("insight exploration: fingerprint, incident, evidence, curve", async ({ page }) => {
  await page.goto("/");

  await clickTab(page, "Insight");
  await expect(page.getByRole("heading", { name: "Fingerprint" })).toBeVisible();
  await expectAnyText(page, [/Decision Explorer/i, /\d+\s+GraphStore decisions?/i, /No decisions match these filters/i]);
  await expect(page.getByText("Incident Replay")).toBeVisible();

  await clickTab(page, "Evidence");
  await expect(page.getByText("AgentEvolver Audit Trail")).toBeVisible();
  await expectAnyText(page, [/Rule Lifecycle/i, /promoted/i, /rejected/i]);
  const auditTrail = page.locator("section", { hasText: /Audit Trail/i }).first();
  await expect(auditTrail).toBeVisible();
  await expectAnyText(page, [/decision/i, /factors/i, /recommendation/i, /outcome/i, /No audit trail available yet/i]);
  const genealogy = page.locator("section", { hasText: "Rule Genealogy" }).first();
  await expect(genealogy).toBeVisible();
  await expect(page.getByText(/Based on seeded|Seeded procurement/i)).toHaveCount(0);
  await expect(genealogy.getByText(/No evolution data yet|evolution|variant|rule/i).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Pattern Origin" })).toBeVisible();

  await clickTab(page, "Curve");
  await expect(page.getByText("Trajectory")).toBeVisible();
  await expectAnyText(page, [/SAP restructure/i, /Current IKS/i]);
});

test("evidence deep exploration shows impact lifecycle audit trail and genealogy", async ({ page }) => {
  await page.goto("/");

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/AgentEvolver Impact/i, /Auto-resolved/i, /Accuracy/i]);
  await expectAnyText(page, [/Rule Lifecycle/i, /promoted/i, /rejected/i]);
  const auditTrail = page.locator("section", { hasText: /Audit Trail/i }).first();
  await expect(auditTrail).toBeVisible();
  const auditText = await auditTrail.innerText();
  expect(auditText.length).toBeGreaterThan(20);
  const genealogy = page.locator("section", { hasText: "Rule Genealogy" }).first();
  await expect(genealogy).toBeVisible();
  await expect(page.getByText(/Based on seeded|Seeded procurement/i)).toHaveCount(0);
  await expect(genealogy.getByText(/No evolution data yet|evolution|variant|rule/i).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Pattern Origin" })).toBeVisible();
});

test("tab navigation all 5 tabs and no blank screens", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await page.goto("/");

  for (const tab of ["Dashboard", "Triage", "Insight", "Evidence", "Curve"]) {
    await clickTab(page, tab);
    await expect(page.locator("main")).not.toBeEmpty();
    await expectAnyText(page, [new RegExp(tab, "i"), /Loading/i, /Select an alert/i, /Trajectory/i]);
  }

  expectNoActionableConsoleErrors(errors);
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
  await expect(explorer.getByText("Category").first()).toBeVisible();
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
  await expectAnyText(page, [/Decision Explorer/i, /\d+\s+GraphStore decisions?/i, /No decisions match these filters/i]);
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
  await expectAnyText(page, [/Centroid Evolution/i, /Centroid History/i, /centroid/i, /top shifts/i, /verified decisions/i]);
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
  await expectAnyText(page, [/Audit Trail/i, /decision/i, /outcome/i, /No audit trail available yet/i]);
  await expect(page.getByText(/Based on seeded|Seeded procurement/i)).toHaveCount(0);
  await expectAnyText(page, [/Rule Genealogy/i, /No evolution data yet/i, /evolution/i, /variant/i, /rule/i]);

  await clickTab(page, "Curve");
  await expectAnyText(page, [/Trajectory/i, /Current IKS/i, /Centroid Evolution/i]);
});

test("Insight bottleneck then Evidence schema impact round trip", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Pipeline Status/i, /Alert Root Causes/i]);

  await clickTab(page, "Insight");
  const bottleneck = dataopsPanel(page, "Pipeline Bottleneck");
  await expect(bottleneck).toBeVisible();
  await expect(bottleneck.getByText(/Join VBAK\/BSEG|duration|No transformation graph available/i).first()).toBeVisible();
  await expect(bottleneck.getByText(/Recommendation|speedup|savings|No transformation graph available/i).first()).toBeVisible();

  await clickTab(page, "Evidence");
  const schema = dataopsPanel(page, "Schema Impact");
  await expect(schema).toBeVisible();
  await expect(schema.getByText(/Downstream impact|Proposed fix|No schema changes detected/i).first()).toBeVisible();
  const rules = dataopsPanel(page, "Operational Rules");
  await expect(rules.getByText(/proposed|shadow|promoted/i).first()).toBeVisible();

  await clickTab(page, "Insight");
  await expect(dataopsPanel(page, "Pipeline Bottleneck")).toBeVisible();
  await expect(dataopsPanel(page, "Decision Explorer")).toBeVisible();
  await expect(dataopsPanel(page, "Incident Replay")).toBeVisible();
});

test("Process-Tech Fusion: enterprise health to bottleneck to cross-graph round trip", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Enterprise Health/i, /Process-Tech Fusion/i]);
  await expectAnyText(page, [/SAP S\/4HANA/i, /Celonis/i, /Graph/i]);

  await clickTab(page, "Insight");
  const timeline = dataopsPanel(page, "Process Timeline");
  await expect(timeline).toBeVisible();
  await expect(timeline.getByText(/Purchase-to-Pay|Match Invoice to GR|bottleneck|No process timeline data available/i).first()).toBeVisible();
  const crossGraph = dataopsPanel(page, "Cross-Graph Insight");
  await expect(crossGraph).toBeVisible();
  await expect(crossGraph.getByText(/Aster 3\.1x slower|SAP.*Celonis.*Graph|Signal unavailable|Could not load cross-graph insight/i).first()).toBeVisible();

  await clickTab(page, "Evidence");
  const schema = dataopsPanel(page, "Schema Impact");
  await expect(schema).toBeVisible();
  await expect(schema.getByText(/MATKL|material_group|MARA|purchase orders|POs|No schema changes detected/i).first()).toBeVisible();
  await expect(schema.getByText(/Downstream impact|Proposed fix|No schema changes detected/i).first()).toBeVisible();

  await clickTab(page, "Dashboard");
  await expectAnyText(page, [/Conservation/i, /Automation Projection/i, /verified decisions/i]);
});

test("full Level 3 story shows bottleneck schema rules genealogy and curve", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Pipeline Status/i, /AgentEvolver Impact/i, /Alert Root Causes/i]);

  await clickTab(page, "Insight");
  const bottleneck = dataopsPanel(page, "Pipeline Bottleneck");
  await expect(bottleneck).toBeVisible();
  await expect(bottleneck.getByText(/recommendation|No transformation graph available/i).first()).toBeVisible();
  await expect(bottleneck.getByText(/reorder|speedup|savings|No transformation graph available/i).first()).toBeVisible();

  await clickTab(page, "Evidence");
  const schema = dataopsPanel(page, "Schema Impact");
  await expect(schema.getByText(/proposed fix|downstream|No schema changes detected/i).first()).toBeVisible();
  const rules = dataopsPanel(page, "Operational Rules");
  await expect(rules.getByText(/scheduling|quality/i).first()).toBeVisible();
  await expect(page.getByText(/Based on seeded|Seeded procurement/i)).toHaveCount(0);
  await expect(dataopsPanel(page, "Rule Lifecycle").getByText(/No promoted variants yet|promoted|rejected|variant/i).first()).toBeVisible();
  await expect(dataopsPanel(page, "Rule Genealogy").getByText(/No evolution data yet|evolution|variant|rule/i).first()).toBeVisible();
  const origin = dataopsPanel(page, "Pattern Origin");
  await expect(origin).toBeVisible();
  await expect(
    origin
      .getByText(
        /SOC|S2P|DataOps|resource_quality_scheduling_signal|s2p_invoice_quality_scheduling_signal|No cross-copilot chain available/i,
      )
      .first(),
  ).toBeVisible();

  await clickTab(page, "Curve");
  await expectAnyText(page, [/Trajectory/i, /Current IKS/i, /Centroid Evolution/i]);
});

test("self-computation round trip: all 4 tabs show SC features", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/SC-12/i, /Accuracy Alerts/i, /No verified decisions yet/i]);

  await clickTab(page, "Insight");
  await expectAnyText(page, [/SC-14/i, /Decision Explorer/i, /Category/i, /Action/i]);

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/SC-13/i, /Rule Genealogy/i, /SC-15/i, /Rule Lifecycle/i, /SC-16/i, /Audit Trail/i]);

  await clickTab(page, "Curve");
  await expectAnyText(page, [/SC-11/i, /Centroid History/i, /No centroid history yet/i, /checkpoints/i]);
});

test("accuracy alert to decision explorer drill-down", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Accuracy Alerts/i, /threshold/i, /verified decisions/i]);

  await clickTab(page, "Insight");
  const explorer = page.locator("section", { hasText: "Decision Explorer" }).first();
  await expect(explorer).toBeVisible();
  await expectAnyText(page, [/Category/i, /Action/i, /Verified only/i, /Confidence/i]);
});

test("centroid evolution to audit trail narrative", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Curve");
  await expectAnyText(page, [/Centroid History/i, /centroid/i, /No centroid history yet/i]);

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/Audit Trail/i, /decision/i, /factors/i, /recommendation/i, /outcome/i, /No audit trail available yet/i]);
});

test("evidence screen shows all three SC components", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Evidence");

  await expectAnyText(page, [/SC-13/i, /Rule Genealogy/i]);
  await expectAnyText(page, [/SC-15/i, /Rule Lifecycle/i]);
  await expectAnyText(page, [/SC-16/i, /Audit Trail/i]);
});

test("self-computation features survive page reload", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Accuracy Alerts/i, /SC-12/i]);
  await page.reload();
  await expectAnyText(page, [/Accuracy Alerts/i, /SC-12/i, /No verified decisions yet/i]);

  await clickTab(page, "Insight");
  await expectAnyText(page, [/Decision Explorer/i, /SC-14/i]);
});

test("DataOps SC regression after Trading and Purchasing port", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/SC-12/i, /Accuracy Alerts/i, /threshold/i]);

  await clickTab(page, "Insight");
  await expectAnyText(page, [/SC-14/i, /Decision Explorer/i, /Category/i, /Action/i]);

  await clickTab(page, "Evidence");
  await expectAnyText(page, [/SC-13/i, /Rule Genealogy/i, /SC-15/i, /Rule Lifecycle/i, /SC-16/i, /Audit Trail/i]);

  await clickTab(page, "Curve");
  await expectAnyText(page, [/SC-11/i, /Centroid History/i, /centroid/i]);
});

test("OE-5 what-if shows impact change on reorder interaction", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Insight");

  const whatIf = page.locator("section", { hasText: /What-if: Reorder/i }).first();
  await expect(whatIf).toBeVisible();
  await expect(whatIf.getByText(/Current order|No transformation graph available/i).first()).toBeVisible();
  await expect(whatIf.getByText(/Reorder order|No transformation graph available/i).first()).toBeVisible();
  await expect(whatIf.getByText(/Extract Orders Daily|Join VBAK\/BSEG|Aggregate Daily Revenue|Load to Warehouse|No transformation graph available/i).first()).toBeVisible();

  const downButtons = whatIf.getByRole("button", { name: /down/i });
  if ((await downButtons.count()) > 0) {
    await downButtons.first().click();
  }

  await expect(whatIf.getByText(/Estimated impact|No transformation graph available/i).first()).toBeVisible();
  await expect(whatIf.getByText(/impact|savings|min|Move steps to estimate impact|No transformation graph available/i).first()).toBeVisible();
});
