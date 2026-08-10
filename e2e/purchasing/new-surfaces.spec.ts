import { expect, test } from "../fixtures/copilot-fixture";

const PURCHASING_API = "http://127.0.0.1:8020";

test.describe("Purchasing endpoint parity", () => {
  test("diagnostics returns the measurement spine", async ({ request }) => {
    const response = await request.get(`${PURCHASING_API}/api/self/diagnostics`);
    expect(response.status()).toBe(200);
    const payload = await response.json();
    expect(payload.epsilon_firm).toBeDefined();
    expect(payload.measurement_state).toBeDefined();
  });

  test("conservation is explainable", async ({ request }) => {
    const response = await request.get(`${PURCHASING_API}/api/conservation/status`);
    expect(response.status()).toBe(200);
    const payload = await response.json();
    expect(payload.status).toBeDefined();
    expect(payload.headroom).toBeDefined();
    expect(typeof payload.reason).toBe("string");
  });

  test("evolution, transfers, and centroid history are accessible", async ({ request }) => {
    const evolution = await request.get(`${PURCHASING_API}/api/self/evolution/summary`);
    expect(evolution.status()).toBe(200);
    expect((await evolution.json()).schema_version).toBe(1);

    const transfers = await request.get(`${PURCHASING_API}/api/self/transfers`);
    expect(transfers.status()).toBe(200);

    const history = await request.get(`${PURCHASING_API}/api/self/centroid-history?limit=1`);
    expect(history.status()).toBe(200);
  });
});
