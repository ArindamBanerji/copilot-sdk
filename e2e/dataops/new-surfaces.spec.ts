import { expect, test } from "../fixtures/copilot-fixture";
import { gotoTab } from "../helpers/ui";

const DATAOPS_API = "http://127.0.0.1:8030";

test.describe("DataOps new surfaces", () => {
  test("Enterprise Value Card renders SAP, Celonis, and discovery link", async ({ page }) => {
    await gotoTab(page, "Dashboard");
    const card = page.getByTestId("enterprise-value-card");
    await expect(card).toBeVisible();
    await expect(card).toContainText(/Enterprise Systems Integration/i);
    await expect(card).toContainText(/SAP/i);
    await expect(card).toContainText(/Celonis/i);
    await expect(card.getByRole("link", { name: /cross-graph discovery/i })).toHaveAttribute(
      "href",
      /\/api\/discovery\/cross-system/,
    );
  });

  test("Data Products Card renders product and conservation surfaces", async ({ page }) => {
    await gotoTab(page, "Dashboard");
    const card = page.getByTestId("products-card");
    await expect(card).toBeVisible();
    await expect(card).toContainText(/Data Products/i);
    await expect(card.getByTestId("di-product").first()).toBeVisible();
    await expect(card).toContainText(/GREEN|AMBER|RED|bootstrap|learning|mature/i);
  });

  test("Intelligence Map renders on Insight with its legend", async ({ page }) => {
    await gotoTab(page, "Insight");
    await expect(page.getByTestId("intelligence-map").last()).toBeVisible();
    await expect(page.getByTestId("intelligence-map-legend")).toBeVisible();
  });

  test("enterprise health returns SAP and Celonis status payloads", async ({ request }) => {
    const response = await request.get(`${DATAOPS_API}/api/dataops/enterprise-health`);
    expect(response.status()).toBe(200);
    const payload = await response.json();
    expect(payload.sap).toBeDefined();
    expect(payload.celonis).toBeDefined();
    expect(payload.overall).toBeDefined();
    expect(payload.sap.source).toBeDefined();
    expect(payload.celonis.source).toBeDefined();
  });

  test("DI endpoints expose map, acquisition, and product data", async ({ request }) => {
    const map = await request.get(`${DATAOPS_API}/api/di/intelligence-map`);
    expect(map.status()).toBe(200);
    expect((await map.json()).nodes).toBeDefined();

    const acquisition = await request.get(`${DATAOPS_API}/api/di/acquisition-advice`);
    expect(acquisition.status()).toBe(200);
    expect((await acquisition.json()).recommendations).toBeDefined();

    const products = await request.get(`${DATAOPS_API}/api/di/products`);
    expect(products.status()).toBe(200);
    expect((await products.json()).products).toBeDefined();
  });

  test("measurement spine endpoints expose explainable fields", async ({ request }) => {
    const diagnostics = await request.get(`${DATAOPS_API}/api/self/diagnostics`);
    expect(diagnostics.status()).toBe(200);
    const diagnosticPayload = await diagnostics.json();
    expect(diagnosticPayload.epsilon_firm).toBeDefined();
    expect(diagnosticPayload.measurement_state).toBeDefined();

    const conservation = await request.get(`${DATAOPS_API}/api/conservation/status`);
    expect(conservation.status()).toBe(200);
    const conservationPayload = await conservation.json();
    expect(conservationPayload.headroom).toBeDefined();
    expect(typeof conservationPayload.reason).toBe("string");

    const evolution = await request.get(`${DATAOPS_API}/api/self/evolution/summary`);
    expect(evolution.status()).toBe(200);
    expect((await evolution.json()).schema_version).toBe(1);
  });

  test("enterprise-value flow crosses Dashboard to Insight", async ({ page }) => {
    await gotoTab(page, "Dashboard");
    await expect(page.getByTestId("enterprise-value-card")).toBeVisible();
    await gotoTab(page, "Insight");
    await expect(page.getByTestId("intelligence-map").last()).toBeVisible();
  });
});
