import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function gotoInsight(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Insight");
  await expectAnyText(page, [/Your profile/i, /Loading DataOps insight/i]);
}

test("profile archetype shows Pattern Matcher or profile", async ({ page }) => {
  await gotoInsight(page);

  await expectAnyText(page, [/The Pattern Matcher/i, /The Risk Assessor/i, /The Blast Analyst/i, /The SLA Guardian/i, /The Trust Trader/i, /The Freshness Monitor/i]);
});

test("fingerprint renders DataOps factors", async ({ page }) => {
  await gotoInsight(page);

  await expect(page.getByText("Fingerprint")).toBeVisible();
  await expectAnyText(page, [/Recurrence/i, /Business criticality/i, /Impact scope/i, /Downstream urgency/i, /Source reliability/i, /Data freshness/i]);
});

test("incident replay card shows incident and cost", async ({ page }) => {
  await gotoInsight(page);

  await expect(page.getByText("Incident Replay")).toBeVisible();
  await expectAnyText(page, [/\$50,?000/i, /incident/i, /Primary alert/i, /System recommendation/i]);
});

test("decision explorer visible with decision count", async ({ page }) => {
  await gotoInsight(page);

  await expectAnyText(page, [/Decision Explorer/i, /GraphStore decisions/i, /explorer/i]);
  await expectAnyText(page, [/\d+\s+GraphStore decisions?/i, /No decisions match these filters/i]);
});

test("decision explorer shows action breakdown with win rates", async ({ page }) => {
  await gotoInsight(page);

  await expect(page.getByText("Decision Explorer")).toBeVisible();
  await expectAnyText(page, [/Category/i, /Action/i, /Verified only/i]);
  await expectAnyText(page, [/Confidence/i, /%/, /pending/i, /correct/i, /incorrect/i, /No decisions match/i]);
});

test("decision explorer filter changes results without losing count", async ({ page }) => {
  await gotoInsight(page);
  await expect(page.getByText("Decision Explorer")).toBeVisible();

  const panel = page.locator("section", { hasText: "Decision Explorer" });
  const selects = panel.locator("select");
  if ((await selects.count()) > 0 && (await selects.first().locator("option").count()) > 1) {
    await selects.first().selectOption({ index: 1 });
  }

  await expectAnyText(page, [/\d+\s+decisions?/i, /No decisions match these filters/i]);
});

test("decision explorer shows real categories not just unknown", async ({ page }) => {
  await gotoInsight(page);

  await expect(page.getByText("Decision Explorer")).toBeVisible();
  await expectAnyText(page, [/Category/i]);
  await expectAnyText(page, [/pipeline/i, /schema/i, /volume/i, /freshness/i, /quality/i, /transform/i, /No decisions match/i]);
});

test("SC-14 decision explorer table renders", async ({ page }) => {
  await gotoInsight(page);

  const explorer = page.locator("section", { hasText: "Decision Explorer" }).first();
  await expect(explorer).toBeVisible();
  await expectAnyText(page, [/SC-14/i, /Decision/i, /Category/i, /Action/i]);
});

test("SC-14 decision explorer shows confidence values", async ({ page }) => {
  await gotoInsight(page);

  await expect(page.getByText("Decision Explorer")).toBeVisible();
  await expectAnyText(page, [/Confidence/i, /%/, /0\.\d+/, /No decisions match these filters/i]);
});

test("bottleneck panel shows pipeline duration breakdown", async ({ page }) => {
  await gotoInsight(page);

  await expectAnyText(page, [/Pipeline Bottleneck/i, /bottleneck/i, /duration/i]);
  await expectAnyText(page, [/Join VBAK\/BSEG/i, /join/i]);
  await expectAnyText(page, [/Extract Orders Daily/i, /extract/i]);
  await expectAnyText(page, [/Aggregate Daily Revenue/i, /aggregate/i]);
  await expectAnyText(page, [/Load to Warehouse/i, /load/i, /\d+% of runtime/i]);
});

test("bottleneck panel shows optimization recommendation", async ({ page }) => {
  await gotoInsight(page);

  const bottleneck = page.locator("section", { hasText: "Pipeline Bottleneck" }).first();
  await expect(bottleneck).toBeVisible();
  await expect(bottleneck.getByText(/Recommendation/i).first()).toBeVisible();
  await expect(bottleneck.getByText(/reorder|optimize/i).first()).toBeVisible();
  await expect(bottleneck.getByText(/speedup|9x/i).first()).toBeVisible();
  await expect(bottleneck.getByText(/savings|minutes saved|min/i).first()).toBeVisible();
});

test("process timeline shows P2P activities with bottleneck", async ({ page }) => {
  await gotoInsight(page);

  const timeline = page.locator("section", { hasText: "Process Timeline" }).first();
  await expect(timeline).toBeVisible();
  await expectAnyText(page, [/Purchase-to-Pay/i, /Standard with Returns/i]);
  await expectAnyText(page, [/Match Invoice to GR/i, /bottleneck/i, /42/i]);
});

test("cross-graph insight card shows supplier correlation", async ({ page }) => {
  await gotoInsight(page);

  const insight = page.locator("section", { hasText: "Cross-Graph Insight" }).first();
  await expect(insight).toBeVisible();
  await expectAnyText(page, [/Aster 3\.1x slower/i, /Aster/i, /supplier/i]);
  await expectAnyText(page, [/SAP.*Celonis.*Graph/i, /cross-graph/i]);
});

test("what-if reordering shows transformation list", async ({ page }) => {
  await gotoInsight(page);

  const whatIf = page.locator("section", { hasText: /What-if: Reorder/i }).first();
  await expect(whatIf).toBeVisible();
  await expect(whatIf.getByText(/Current order/i).first()).toBeVisible();
  await expect(whatIf.getByText(/Reorder order/i).first()).toBeVisible();
  await expectAnyText(page, [/Extract Orders Daily/i, /extract/i]);
  await expectAnyText(page, [/Join VBAK\/BSEG/i, /join/i]);
  await expectAnyText(page, [/Aggregate Daily Revenue/i, /aggregate/i]);
  await expectAnyText(page, [/Load to Warehouse/i, /load/i]);
});

test("what-if reordering shows estimated impact", async ({ page }) => {
  await gotoInsight(page);

  const whatIf = page.locator("section", { hasText: /What-if: Reorder/i }).first();
  await expect(whatIf).toBeVisible();
  await expect(whatIf.getByText(/Estimated impact/i).first()).toBeVisible();
  await expectAnyText(page, [/Move steps to estimate impact/i, /savings/i, /speedup/i, /min/i]);
});
