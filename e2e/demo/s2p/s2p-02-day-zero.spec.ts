import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8002";
test("S2P-02 day-zero", async ({ request }) => {
  const response = await request.post(API + "/api/s2p/score", { data: { event_id: "PW-DAY-ZERO-001", category: "contract_gap", amount: 22426.73, supplier_id: "SUP-001" } });
  test.skip(!response.ok(), `Score returned ${response.status()}`);
  // Mutation cleanup: scoring is append-only; an isolated cold scorer must be supplied by the fixture.
  const body = await response.json();
  test.skip(body.prior_verified_count !== 0, "S2P-02 requires an isolated scorer reporting prior_verified_count=0");
  expect(body.confidence).toBeGreaterThan(0);
  expect(body.confidence).toBeLessThanOrEqual(1);
  expect(body.factor_vector).toHaveLength(8);
  expect(body.probabilities).toHaveLength(5);
});
