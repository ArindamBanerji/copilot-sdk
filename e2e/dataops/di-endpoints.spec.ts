import { test, expect } from "../fixtures/copilot-fixture";

const DATAOPS_API = process.env.DATAOPS_API_URL ?? "http://127.0.0.1:8030";

test("DI consumers endpoint returns consumer quality bars", async ({ request }) => {
  const response = await request.get(`${DATAOPS_API}/api/di/sources/sap_s4hana/consumers`);
  expect(response.ok()).toBeTruthy();

  const payload = await response.json();
  expect(payload.source_id).toBe("sap_s4hana");
  expect(payload.consumers.length).toBeGreaterThan(0);
  expect(payload.consumers[0].quality_bar).toBeTruthy();
});

test("DI trust endpoint returns DK trust and column propagation", async ({ request }) => {
  const response = await request.get(`${DATAOPS_API}/api/di/sources/sap_s4hana/trust`);
  expect(response.ok()).toBeTruthy();

  const payload = await response.json();
  expect(payload.trust_score).toBeGreaterThan(0);
  expect(payload.trust_score).toBeLessThanOrEqual(1);
  expect(payload.columns.length).toBeGreaterThan(0);
  expect(["reliable", "moderate", "noisy"]).toContain(payload.trust_label);
});

test("DI products endpoint returns per-product IKS", async ({ request }) => {
  const response = await request.get(`${DATAOPS_API}/api/di/products`);
  expect(response.ok()).toBeTruthy();

  const payload = await response.json();
  expect(payload.products.length).toBeGreaterThan(0);
  expect(payload.products[0].iks).toBeGreaterThanOrEqual(0);
  expect(payload.products[0].conservation_status).toBeTruthy();
});
