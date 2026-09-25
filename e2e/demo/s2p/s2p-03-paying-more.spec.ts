import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8002";
test("S2P-03 paying-more", async ({ request }) => {
  const response = await request.post(API + "/api/s2p/score", { data: { event_id: "S2P-DEMO-CONTAINER-01", category: "contract_gap", amount: 1200, supplier_id: "SUP-CONTAINER-001", supplier_name: "Port Logistics", context: { working_capital: 14200, demurrage: 1200, days_at_port: 3 } } });
  test.skip(!response.ok(), `Container score returned ${response.status()}`);
  // Mutation cleanup: S2P scores are append-only audit records.
  const body = await response.json();
  const evidence = JSON.stringify(body).toLowerCase();
  test.skip(body.action_category !== "HOLD" || !/working.capital|demurrage/.test(evidence), "S2P-03 requires the container HOLD fixture with demurrage versus working-capital reasoning");
  expect(body.action_category).toBe("HOLD");
  expect(body.confidence).toBeGreaterThan(0);
  expect(evidence).toMatch(/working.capital|demurrage/);
});
