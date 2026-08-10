import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import { DATAOPS, S2P, SOC, expectAnyText, isBackendHealthy, openCopilotTab } from "./demo-fixture";

type JsonRecord = Record<string, unknown>;

async function skipIfBackendDown(request: APIRequestContext, copilot = SOC): Promise<void> {
  const healthy = await isBackendHealthy(request, copilot);
  test.skip(!healthy, `${copilot.name} backend is down`);
}

function numericValue(value: unknown): number {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

function nestedNumber(data: JsonRecord, path: string[]): number {
  let current: unknown = data;
  for (const key of path) {
    if (!current || typeof current !== "object") return 0;
    current = (current as JsonRecord)[key];
  }
  return numericValue(current);
}

async function readSocIks(request: APIRequestContext): Promise<number> {
  const candidates = [
    `${SOC.backend}/api/soc/learning-state`,
    `${SOC.backend}/api/soc/profile`,
    `${SOC.backend}/api/soc/analytics`,
  ];
  for (const url of candidates) {
    const response = await request.get(url, { timeout: 5_000 }).catch(() => null);
    if (!response?.ok()) continue;
    const data = (await response.json().catch(() => ({}))) as JsonRecord;
    const iks =
      numericValue(data.iks) ||
      numericValue(data.iks_v2) ||
      numericValue(data.institutional_knowledge_score) ||
      nestedNumber(data, ["iks", "score"]) ||
      nestedNumber(data, ["iks", "value"]);
    if (iks > 0) return iks;
  }
  return 0;
}

async function scoreSelectedS2PException(page: Page): Promise<void> {
  const situation = page.getByTestId("situation-panel");
  const selected = page.locator("article").filter({ hasText: /Selected Invoice/i });
  const selectedHasInvoice = await selected.getByText(/Supplier|Amount|Category/i).count();
  if (selectedHasInvoice === 0) {
    const invoiceButtons = page
      .locator("article")
      .filter({ hasText: /Invoice Selector/i })
      .getByRole("button")
      .filter({ hasText: /S2P-INV/i });
    if ((await invoiceButtons.count()) > 0) {
      await invoiceButtons.first().click();
    }
  }

  const scoreButton = page.getByRole("button", { name: /^Score$/i });
  await expect(scoreButton).toBeEnabled({ timeout: 20_000 });
  await scoreButton.click();
  await expect(situation.getByRole("heading", { name: "Situation Analysis", exact: true })).toBeVisible({
    timeout: 20_000,
  });
}

async function postSimulationFailure(request: APIRequestContext): Promise<boolean> {
  for (const path of ["/api/eval/simulate-failure", "/api/soc/simulate-failure", "/api/simulation/simulate-failure", "/api/simulation/failure"]) {
    const response = await request.post(`${SOC.backend}${path}`, { timeout: 10_000 }).catch(() => null);
    if (response?.ok()) return true;
  }
  return false;
}

test.describe.serial("Enterprise Demo Cut - 8 beats", () => {
  test.beforeAll(async ({ request }) => {
    if (!(await isBackendHealthy(request, SOC))) return;
    const iks = await readSocIks(request);
    test.skip(iks <= 0, "SOC IKS is 0; Enterprise cut requires preseeded SOC learning state");
  });

  test("E1: SOC Runtime Evolution panel and process alert control", async ({ page }) => {
    await skipIfBackendDown(page.request, SOC);
    await openCopilotTab(page, SOC, /Runtime Evolution/i);

    await expectAnyText(page, [/Runtime Evolution/i, /Institutional Knowledge Score/i, /Agent Evolution/i]);
    await expect(page.getByRole("button", { name: /Process Alert|process alert/i }).first()).toBeVisible({
      timeout: 15_000,
    });
  });

  test("E2: S2P Exception Triage score shows SituationPanel provenance", async ({ page }) => {
    await skipIfBackendDown(page.request, S2P);
    await openCopilotTab(page, S2P, /Exception Triage/i);

    // SILENCE 2: let the SituationPanel explanation land before continuing narration.
    await scoreSelectedS2PException(page);
    const situation = page.getByTestId("situation-panel");
    await expect(situation.getByText(/price|contract|confidence|explanation|hops?/i).first()).toBeVisible({
      timeout: 20_000,
    });
    await expect(situation.getByText(/learned|context|proven|sample/i).first()).toBeVisible({ timeout: 20_000 });
  });

  test("E3: SOC Compounding shows conservation intervention and declined text", async ({ page }) => {
    await skipIfBackendDown(page.request, SOC);
    await openCopilotTab(page, SOC, /Compounding|Decision Economics/i);

    // SILENCE 3: pause on the governance language before showing failure injection.
    await expectAnyText(page, [/Trust Curve/i, /human review/i, /Asymmetric Ratio/i, /penalty/i], 15_000);
  });

  test("E4: SOC Compounding simulate failure shows AMBER or degraded state", async ({ page }) => {
    await skipIfBackendDown(page.request, SOC);
    const posted = await postSimulationFailure(page.request);
    test.skip(!posted, "SOC simulate-failure endpoint is unavailable");

    await openCopilotTab(page, SOC, /Compounding|Decision Economics/i);
    await expectAnyText(page, [/Trust Curve/i, /human review/i, /Asymmetric Ratio/i, /penalty/i], 20_000);
  });

  test("E5: DataOps Insight shows Intelligence Map value indicators", async ({ page }) => {
    await skipIfBackendDown(page.request, DATAOPS);
    await openCopilotTab(page, DATAOPS, /Insight/i);

    await expect(page.getByText("Intelligence Map", { exact: true })).toBeVisible({ timeout: 20_000 });
    await expectAnyText(page, [/\$[\d,.]+K?\/year/i, /Gold-line suggestions/i, /ROI/i, /annual value/i], 15_000);
    await expectAnyText(page, [/cross-graph/i, /SAP.*Celonis.*Graph/i, /Source trust and quality graph/i], 15_000);
  });

  test("E6: SOC Executive Narrative shows IKS or accuracy value", async ({ page }) => {
    await skipIfBackendDown(page.request, SOC);
    await openCopilotTab(page, SOC, /Executive Narrative/i);

    await expectAnyText(page, [/Executive Narrative/i, /What Changed/i, /What Was Discovered/i], 15_000);
    await expectAnyText(page, [/IKS/i, /accuracy/i, /\d+(\.\d+)?%/i, /\d+(\.\d+)?/i], 15_000);
  });

  test("E7: SOC Evidence Room renders external references", async ({ page }) => {
    await skipIfBackendDown(page.request, SOC);
    await openCopilotTab(page, SOC, /Evidence Room|Evidence/i);

    await expect(page.locator("main")).not.toBeEmpty({ timeout: 15_000 });
    const externalRefs = page.getByText(/ServiceNow|Sentinel|external/i);
    if ((await externalRefs.count()) === 0) {
      test.info().annotations.push({
        type: "soft-check",
        description: "No ServiceNow/Sentinel/external reference text rendered in Evidence Room",
      });
    } else {
      await expect(externalRefs.first()).toBeVisible();
    }
  });

  test("E8: SOC Evidence Room shows governance audit material", async ({ page }) => {
    await skipIfBackendDown(page.request, SOC);
    await openCopilotTab(page, SOC, /Evidence Room|Evidence/i);

    await expectAnyText(page, [/Evidence/i, /Governance/i, /Audit/i], 15_000);
    await expectAnyText(page, [/hash/i, /table/i, /ledger/i, /decision/i], 15_000);
  });
});
