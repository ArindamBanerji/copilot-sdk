import { test, expect, PORTS, apiGet, apiPost, gotoCopilot, gotoTab } from "./demo-fixture";

test.describe.serial("Enterprise Cut (E1-E8)", () => {
  test.beforeEach(async ({ demoReady }) => {
    test.skip(!demoReady, "Demo cut skipped: backends must be healthy and preseeded (IKS > 0)");
  });

  test("E1: SOC alert triage renders with factors", async ({ page }) => {
    await gotoTab(page, "soc", "Alert Triage");
    await expect(page.getByText(/Alert Queue|Alert Triage/i).first()).toBeVisible();
    // The SOC queue is mutable from prior demo activity; reset is idempotent and
    // restores the preseeded pending-alert narrative for this cut.
    await page.getByRole("button", { name: /Reset Alerts/i }).click();
    const alert = page.locator("button").filter({ hasText: /^(SIM-|ALERT-)/ }).first();
    await expect(alert).toBeVisible();
    await alert.click();
    await expect(page.locator("main")).toContainText(/factor|confidence|privileged|asset criticality/i);
  });

  test("E2: SOC situation analysis explains a decision", async () => {
    const explanation = await apiPost(PORTS.soc.backend, "/api/soc/judgment/explain", {
      alert_id: "DEMO-CUT-ALERT",
      category: "credential_access",
      factors: {
        privileged_identity_context: 0.8,
        asset_criticality: 0.7,
        threat_intel_enrichment: 0.6,
        pattern_history: 0.5,
        time_anomaly: 0.4,
        device_trust: 0.7,
      },
    });
    expect(explanation.rationale).toBeTruthy();
    expect(explanation.dominant_factors ?? explanation.factor_contributions).toBeDefined();
    expect(explanation.action).toBeTruthy();
  });

  test("E3: DataOps Dashboard shows pipeline grid and enterprise health", async ({ page }) => {
    await gotoCopilot(page, "dataops");
    await expect(page.getByTestId("enterprise-value-card")).toBeVisible();
    await expect(page.getByTestId("enterprise-system-sap-s-4hana")).toBeVisible();
    await expect(page.getByTestId("enterprise-system-celonis")).toBeVisible();
    const health = await apiGet(PORTS.dataops.backend, "/api/dataops/enterprise-health");
    expect(health.sap).toBeDefined();
    expect(health.celonis).toBeDefined();
  });

  test("E4: DataOps Triage to Insight shows bottleneck and schema impact", async ({ page }) => {
    await gotoCopilot(page, "dataops");
    await expect(page.getByText("Alert Root Causes", { exact: true })).toBeVisible({ timeout: 25_000 });
    // Scope past the shell's Triage tab; this selects an alert row's action.
    const triageButtons = page.locator("section.copilot-card").getByRole("button", { name: "Triage", exact: true });
    if ((await triageButtons.count()) === 0) {
      await page.getByRole("button", { name: "Expand", exact: true }).first().click();
    }
    await expect(triageButtons.first()).toBeVisible();
    await triageButtons.first().click();
    await expect(page.locator("main")).toContainText(/Alert Root Causes|Dependency Tree|factors/i);
    await page.getByRole("button", { name: "Insight", exact: true }).click();
    await expect(page.getByText(/Pipeline Bottleneck|bottleneck|fingerprint/i).first()).toBeVisible();
    await page.getByRole("button", { name: "Evidence", exact: true }).click();
    await expect(page.getByText(/Schema Impact|schema impact/i).first()).toBeVisible();
  });

  test("E5: DataOps Process-Tech Fusion shows the intelligence map and gold lines", async ({ page }) => {
    await gotoTab(page, "dataops", "Insight");
    await expect(page.getByTestId("intelligence-map")).toBeVisible();
    await expect(page.getByTestId("gold-line").first()).toBeVisible();
    await expect(page.getByText(/SAP|Celonis|Graph/i).first()).toBeVisible();
    const map = await apiGet(PORTS.dataops.backend, "/api/di/intelligence-map");
    expect(map.gold_lines).toBeDefined();
    expect(map.edges).toBeDefined();
  });

  test("E6: S2P Preview shows exception queue, conservation, and supplier profile", async ({ page }) => {
    await gotoCopilot(page, "s2p");
    await expect(page.locator("main")).toContainText(/Exception Queue/i);
    await expect(page.locator("main")).toContainText(/Conservation Status/i);
    const queue = await apiGet(PORTS.s2p.backend, "/api/s2p/preview/queue");
    expect(queue.total).toBeGreaterThan(0);
    expect(queue.exceptions ?? queue.invoices).toBeDefined();

    await gotoTab(page, "s2p", "Suppliers");
    await expect(page.locator("main")).toContainText(/supplier|OTIF|profile/i);
  });

  test("E7: S2P Triage reaches score, situation, and rule-vs-reasoning contrast", async ({ page }) => {
    await gotoTab(page, "s2p", "Exception Triage");
    const selected = page.locator("article").filter({ hasText: /Selected Invoice/i });
    await expect(selected).toContainText(/Supplier|Amount|Category/i);

    const scoreButton = selected.getByRole("button", { name: /^Score$/i });
    await expect(scoreButton).toBeEnabled();
    const response = page.waitForResponse(
      (item) => item.url().includes("/score") && item.request().method() === "POST" && item.ok(),
    );
    await scoreButton.click();
    await response;

    await expect(page.getByTestId("situation-panel")).toBeVisible();
    await expect(page.getByTestId("rule-vs-reasoning-panel")).toContainText(/Rule-Based|Situation-Aware/i);
  });

  test("E8: SOC Evidence Room shows hash chain, governance, and evolution events", async ({ page }) => {
    await gotoTab(page, "soc", "Evidence Room");
    await expect(page.locator("main")).toContainText(/Evidence|Governance|hash/i);

    const evidence = await apiGet(PORTS.soc.backend, "/api/soc/evidence-room");
    const hashChain = evidence.hash_chain as Record<string, unknown>;
    expect(hashChain.verified ?? hashChain.status).toBeDefined();
    expect(evidence.audit_trail).toBeDefined();

    const governance = await apiGet(PORTS.soc.backend, "/api/governance/summary");
    expect(governance.sections).toBeDefined();
    const events = await apiGet(PORTS.soc.backend, "/api/evolution/recent-events?limit=5");
    expect(events.events).toBeDefined();
    expect(Array.isArray(events.events)).toBe(true);
  });
});
