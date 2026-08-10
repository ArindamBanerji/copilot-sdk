import { test, expect } from "@playwright/test";

const COPILOTS = [
  { name: "Trading", port: 8010 },
  { name: "Purchasing", port: 8020 },
  { name: "DataOps", port: 8030 },
  { name: "S2P", port: 8002 },
] as const;

for (const { name, port } of COPILOTS) {
  test.describe(`${name} endpoint parity`, () => {
    test(`${name}: health is live`, async ({ request }) => {
      const response = await request.get(`http://127.0.0.1:${port}/health`);
      expect(response.status()).toBe(200);
    });

    test(`${name}: diagnostics exposes measurement spine`, async ({ request }) => {
      const response = await request.get(`http://127.0.0.1:${port}/api/self/diagnostics`);
      expect(response.status()).toBe(200);
      const payload = await response.json();
      expect(payload.centroid_distance_to_canonical).toBeDefined();
      expect(payload.epsilon_firm).toBeDefined();
      expect(payload.measurement_state).toBeDefined();
    });

    test(`${name}: conservation is explainable`, async ({ request }) => {
      const response = await request.get(`http://127.0.0.1:${port}/api/conservation/status`);
      expect(response.status()).toBe(200);
      const payload = await response.json();
      expect(payload.status).toBeDefined();
      expect(payload.reason).toBeDefined();
      expect(payload.headroom).toBeDefined();
    });

    test(`${name}: evolution schema is version 1`, async ({ request }) => {
      const response = await request.get(`http://127.0.0.1:${port}/api/self/evolution/summary`);
      expect(response.status()).toBe(200);
      expect((await response.json()).schema_version).toBe(1);
    });

    test(`${name}: centroid history is readable`, async ({ request }) => {
      const response = await request.get(`http://127.0.0.1:${port}/api/self/centroid-history?limit=5`);
      expect(response.status()).toBe(200);
      expect((await response.json()).checkpoints).toBeDefined();
    });
  });
}
