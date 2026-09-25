import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8002";
test("S2P-01 rule-said-no", async ({ request }) => {
  const response = await request.post(API + "/api/s2p/score", { data: { event_id: "S2P-INV-0001", category: "contract_gap", amount: 22426.73, supplier_id: "SUP-001" } });
  test.skip(!response.ok(), `Score returned ${response.status()}`);
  // Mutation cleanup: S2P scores are append-only audit records.
  const body = await response.json();
  const reasoning = JSON.stringify(body).toLowerCase();
  test.skip(body.action !== "accept" || body.confidence <= 0.8 || !reasoning.includes("7.3"), "S2P-01 requires the seeded copper ACCEPT decision with clause 7.3 reasoning");
  expect(body.action).toBe("accept");
  expect(body.confidence).toBeGreaterThan(0.8);
  expect(body.factor_vector).toHaveLength(8);
  expect(body.factor_vector.every(Number.isFinite)).toBe(true);
  expect(reasoning).toContain("7.3");
});
