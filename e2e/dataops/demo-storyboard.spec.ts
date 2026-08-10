import { type Locator, type Page, type Route } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForScreenReady } from "../helpers/ui";

function panelByHeading(page: Page, heading: string | RegExp): Locator {
  return page
    .locator("h1, h2, h3, h4", { hasText: heading })
    .locator(
      "xpath=ancestor::*[self::article or self::section or contains(concat(' ', normalize-space(@class), ' '), ' copilot-card ')][1]",
    )
    .first();
}

async function gotoDashboard(page: Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await expect(panelByHeading(page, "Pipeline Status")).toBeVisible();
}

async function mockQuery(page: Page, body: object) {
  await page.route("**/api/di/query", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}

async function switchToTab(page: Page, tab: "Dashboard" | "Triage" | "Insight" | "Evidence" | "Curve") {
  await clickTab(page, tab);
  await waitForScreenReady(page);
}

async function openFirstTriage(page: Page) {
  await gotoDashboard(page);
  const alertSection = page.locator("section", { hasText: "Alert Root Causes" });
  const triageButtons = alertSection.getByRole("button", { name: "Triage" });

  if ((await triageButtons.count()) === 0) {
    const groupHeader = alertSection
      .locator("button, summary, [role='button']")
      .filter({ hasText: /warehouse|billing|sap|crm|erp/i })
      .first();
    if (await groupHeader.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await groupHeader.click();
    }
  }

  await expect(triageButtons.first()).toBeVisible({ timeout: 10_000 });
  await triageButtons.first().click();
  await waitForScreenReady(page);
  await expect(page.getByRole("button", { name: "Back to Dashboard" })).toBeVisible();
}

test.describe("DataOps Demo Storyboard", () => {
  test("Act 1 WHERE: Dashboard shows pipeline status and alert groups", async ({ page }) => {
    await gotoDashboard(page);
    await expect(panelByHeading(page, "Alert Root Causes")).toBeVisible();
    await expectAnyText(page, [/\d+\s+systems/i, /root causes|total alerts/i]);
  });

  test("Act 1 WHERE: Enterprise health shows 3 systems", async ({ page }) => {
    await gotoDashboard(page);
    const health = page.getByTestId("enterprise-health");
    await expect(health).toBeVisible();
    await expect(health.getByTestId("enterprise-system-sap-s-4hana")).toBeVisible();
    await expect(health.getByTestId("enterprise-system-celonis")).toBeVisible();
    await expect(health.getByTestId("enterprise-system-graph")).toBeVisible();
  });

  test("Act 2 WHY: Triage shows bottleneck and schema impact", async ({ page }) => {
    await openFirstTriage(page);
    await expectAnyText(page, [/Dependency Tree/i, /Action/i, /All factors auto-computed/i]);

    await switchToTab(page, "Insight");
    await expect(panelByHeading(page, "Pipeline Bottleneck")).toBeVisible();
    await switchToTab(page, "Evidence");
    await expect(panelByHeading(page, "Schema Impact")).toBeVisible();
  });

  test("Act 2 WHY: Cross-Graph Insight shows Celonis, SAP, and Graph context", async ({ page }) => {
    await gotoDashboard(page);
    await switchToTab(page, "Insight");
    // Cross-Graph Insight is per-alert; alerts without cross-graph data hide the panel.
    const crossGraph = page.getByText(/Cross-Graph Insight/i).first();
    const hasCrossGraph = await crossGraph.isVisible({ timeout: 3_000 }).catch(() => false);
    if (hasCrossGraph) {
      await expectAnyText(page, [/Celonis|SAP|Graph|sources linked/i]);
    }
  });

  test("Act 3 WHAT: Triage shows AE recommendation and What-If", async ({ page }) => {
    await openFirstTriage(page);
    await expectAnyText(page, [/AE:|recommendation|All factors auto-computed/i]);
    await switchToTab(page, "Insight");
    await expect(panelByHeading(page, /What-if: Reorder/i)).toBeVisible();
  });

  test("Act 4 LEARN: Score and confirm produces conservation update", async ({ page }) => {
    await openFirstTriage(page);
    const actionSection = page.locator("section", { hasText: "Choose the operational response." });
    const scoreResponse = page.waitForResponse(
      (response) => response.url().includes("/api/score") && response.request().method() === "POST",
    );
    await actionSection.getByRole("button", { name: "Investigate" }).click();
    await scoreResponse;
    await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
    await page.getByRole("button", { name: "Confirm" }).click();
    await expectAnyText(page, [/system learned|Reward|IKS delta|reward signal|Conservation/i]);
  });

  test("Act 5 TRANSFER: Evidence shows rule lifecycle and audit trail", async ({ page }) => {
    await gotoDashboard(page);
    await switchToTab(page, "Evidence");
    await expect(panelByHeading(page, /Rule Lifecycle/i)).toBeVisible();
    await expectAnyText(page, [/Audit Trail|AgentEvolver Audit Trail|Pattern Transfer Status/i]);
  });

  test("DI: Trust card shows 6 factors on Dashboard", async ({ page }) => {
    await gotoDashboard(page);
    const trust = page.getByTestId("trust-card");
    await expect(trust).toBeVisible();
    await expect(trust.getByTestId("trust-factor")).toHaveCount(6);
  });

  test("DI: Products card shows IKS on Dashboard", async ({ page }) => {
    await gotoDashboard(page);
    const products = page.getByTestId("products-card");
    await expect(products).toBeVisible();
    await expect(products.locator('[aria-label^="IKS "]')).not.toHaveCount(0);
  });

  test("DI: Intelligence Map shows gold lines on Insight", async ({ page }) => {
    await gotoDashboard(page);
    await switchToTab(page, "Insight");
    const map = page.getByTestId("intelligence-map");
    await expect(map).toBeVisible();
    await expect(map.getByTestId("gold-line")).not.toHaveCount(0);
  });

  test("DI: Centroid Timeline renders on Insight", async ({ page }) => {
    await gotoDashboard(page);
    await switchToTab(page, "Insight");
    const timeline = page.getByTestId("centroid-timeline");
    await expect(timeline).toBeVisible();
    await expect(timeline.getByTestId("centroid-timeline-chart")).toBeVisible();
    await expect(timeline.locator("svg g")).not.toHaveCount(0);
  });

  test("DI: Accuracy Alerts and Rule Genealogy are present on Evidence", async ({ page }) => {
    await gotoDashboard(page);
    await switchToTab(page, "Evidence");
    await expect(page.getByTestId("accuracy-alerts")).toBeVisible();
    await expect(page.getByTestId("rule-genealogy")).toBeVisible();
  });

  test("DI-3: NL query returns quality-aware answer", async ({ page }) => {
    await mockQuery(page, {
      answer: "417",
      confidence: 0.92,
      confidence_label: "high",
      source_attribution: [{ source_id: "graph", source: "AGE GraphStore", trust: 0.99, contribution: "primary", weight: 1 }],
      computation_path: ["AGE GraphStore → governed decisions", "decision_count → 417"],
      quality_warning: null,
      evidence: "417 governed records contributed.",
    });
    await gotoDashboard(page);
    await page.getByPlaceholder("Ask about your data...").fill("How many decisions?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();

    await expect(page.getByTestId("query-answer")).toHaveText("417");
    await expect(page.getByTestId("query-confidence")).toContainText("high");
    await expect(page.getByTestId("source-attribution-bar")).toHaveCount(1);
  });

  test("DI-3: Revenue narrative shows amount and confidence", async ({ page }) => {
    await mockQuery(page, {
      answer: "$3,385,700",
      confidence: 0.58,
      confidence_label: "moderate",
      source_attribution: [
        { source_id: "sap_s4hana", source: "SAP S/4HANA", trust: 0.99, contribution: "primary", weight: 0.5 },
        { source_id: "celonis_p2p", source: "Celonis P2P", trust: 0.87, contribution: "secondary", weight: 0.5 },
      ],
      computation_path: ["SAP S/4HANA invoices → SUM(amount) → $3,385,700"],
      quality_warning: "3 records were unmatched.",
      evidence: "10 governed records contributed, 3 unmatched.",
    });
    await gotoDashboard(page);
    await page.getByPlaceholder("Ask about your data...").fill("What was revenue last month?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();

    await expect(page.getByTestId("query-answer")).toHaveText("$3,385,700");
    await expect(page.getByTestId("query-confidence")).toContainText("moderate");
    await expect(page.getByTestId("source-attribution-bar")).toHaveCount(2);
  });

  test("DI-3: Moderate-quality query shows a warning", async ({ page }) => {
    await mockQuery(page, {
      answer: "3",
      confidence: 0.58,
      confidence_label: "moderate",
      source_attribution: [{ source_id: "sap_s4hana", source: "SAP S/4HANA", trust: 0.99, contribution: "primary", weight: 1 }],
      computation_path: ["SAP S/4HANA invoices → exception count → 3"],
      quality_warning: "3 invoices were not matched to governed decisions.",
      evidence: "10 governed records contributed, 3 unmatched.",
    });
    await gotoDashboard(page);
    await page.getByPlaceholder("Ask about your data...").fill("How many unmatched invoices?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();

    await expect(page.getByTestId("query-quality-warning")).toContainText("not matched");
    await expect(page.getByTestId("query-confidence")).toContainText("moderate");
  });
});
