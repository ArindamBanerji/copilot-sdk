import { test, expect } from "../fixtures/copilot-fixture";
import { gotoTab } from "../helpers/ui";

const API = "http://127.0.0.1:8030";

test.describe("DataOps sweep — point tests", () => {
  test("Dashboard mounts enterprise value and data products cards", async ({ page }) => {
    await gotoTab(page, "Dashboard");
    await expect(page.getByTestId("enterprise-value-card")).toBeVisible();
    await expect(page.getByTestId("enterprise-value-card")).toContainText(/SAP|Celonis/i);
    await expect(page.getByTestId("products-card")).toBeVisible();
  });

  test("Insight mounts intelligence map with gold-line legend", async ({ page }) => {
    await gotoTab(page, "Insight");
    await expect(page.getByTestId("intelligence-map").last()).toBeVisible();
    await expect(page.getByTestId("intelligence-map-legend")).toBeVisible();
  });

  test("Evidence mounts lifecycle and audit surfaces", async ({ page }) => {
    await gotoTab(page, "Evidence");
    await expect(page.getByTestId("rule-lifecycle")).toBeVisible();
    await expect(page.getByTestId("audit-trail")).toBeVisible();
  });

  test("enterprise health exposes SAP and Celonis provenance", async ({ request }) => {
    const response = await request.get(`${API}/api/dataops/enterprise-health`);
    expect(response.status()).toBe(200);
    const payload = await response.json();
    expect(payload.sap).toBeDefined();
    expect(payload.celonis).toBeDefined();
    expect(payload.sap.source).toBeDefined();
    expect(payload.celonis.source).toBeDefined();
  });

  test("DI endpoints expose map, acquisition, products, sources, and combinations", async ({ request }) => {
    for (const path of [
      "/api/di/intelligence-map",
      "/api/di/acquisition-advice",
      "/api/di/products",
      "/api/di/sources/sap_s4hana/trust",
      "/api/di/sources/sap_s4hana/consumers",
    ]) {
      const response = await request.get(`${API}${path}`);
      expect(response.status(), path).toBe(200);
    }
  });

  test("health exposes hot-path cache telemetry", async ({ request }) => {
    const response = await request.get(`${API}/health`);
    expect(response.status()).toBe(200);
    const payload = await response.json();
    expect(payload.cache_hits).toBeDefined();
    expect(payload.cache_misses).toBeDefined();
    expect(payload.cache_size).toBeDefined();
  });

  test("trust traps, rollback, and replay surfaces are reachable", async ({ request }) => {
    expect((await request.get(`${API}/api/self/trust-traps`)).status()).toBe(200);
    expect([200, 400, 404, 422]).toContain(
      (await request.post(`${API}/api/self/rollback`, { data: { checkpoint_id: "missing" } })).status(),
    );
    expect([200, 400, 404, 422]).toContain(
      (await request.post(`${API}/api/self/replay-score`, { data: { checkpoint_id: "missing", factors: {} } })).status(),
    );
  });
});

test.describe("DataOps sweep — demo flows", () => {
  test("E5 fusion: Dashboard SAP/Celonis → Insight intelligence map", async ({ page }) => {
    await gotoTab(page, "Dashboard");
    await expect(page.getByTestId("enterprise-value-card")).toBeVisible();
    await gotoTab(page, "Insight");
    await expect(page.getByTestId("intelligence-map").last()).toBeVisible();
    await expect(page.getByTestId("gold-line").first()).toBeVisible();
  });

  test("DI-GOLD: Insight → suggested gold lines → dollar values", async ({ page }) => {
    await gotoTab(page, "Insight");
    const map = page.getByTestId("intelligence-map").last();
    await expect(map).toBeVisible();
    await expect(map.getByTestId("gold-line").first()).toBeVisible();
    await expect(map.getByTestId("gold-line-label").first()).toHaveText(/\$[\d,.]+K?/i);
  });

  test("DI-TRUST to DI-PRODUCT: Dashboard trust and products → Insight source profile", async ({ page }) => {
    await gotoTab(page, "Dashboard");
    await expect(page.getByTestId("trust-card")).toBeVisible();
    await expect(page.getByTestId("products-card")).toBeVisible();
    await gotoTab(page, "Insight");
    await expect(page.getByTestId("source-profile-panel")).toBeVisible();
  });

  test("DI-PROOF: perturb → inspect → revert", async ({ page, request }) => {
    await gotoTab(page, "Dashboard");
    const perturb = await request.post(`${API}/api/di/perturb`, { data: { source_id: "sap_s4hana" } });
    expect([200, 400, 422]).toContain(perturb.status());
    const revert = await request.post(`${API}/api/di/revert`);
    expect([200, 400, 404, 422]).toContain(revert.status());
    await gotoTab(page, "Insight");
    await expect(page.getByTestId("intelligence-map").last()).toBeVisible();
  });

  test("measurement spine: diagnostics → conservation → evolution", async ({ request }) => {
    const diagnostics = await request.get(`${API}/api/self/diagnostics`);
    const conservation = await request.get(`${API}/api/conservation/status`);
    const evolution = await request.get(`${API}/api/self/evolution/summary`);
    expect(diagnostics.status()).toBe(200);
    expect(conservation.status()).toBe(200);
    expect(evolution.status()).toBe(200);
    expect((await diagnostics.json()).measurement_state).toBeDefined();
    expect((await conservation.json()).reason).toBeDefined();
    expect((await evolution.json()).schema_version).toBe(1);
  });

  test("all DataOps tabs remain navigable", async ({ page }) => {
    for (const tab of ["Dashboard", "Triage", "Insight", "Evidence", "Curve"]) {
      await gotoTab(page, tab);
      await expect(page.locator("body")).not.toContainText(/Unhandled error|TypeError|Application error/i);
    }
  });
});
