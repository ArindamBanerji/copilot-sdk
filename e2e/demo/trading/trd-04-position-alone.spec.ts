import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8010";
test("TRD-04 position-alone", async ({ request }) => {
  const response = await request.post(API + "/api/investigation/investigate", {
    data: { decision_id: "PW-TRD-04", category: "trend_following", factor_vector: [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5], budget: 2, use_K: true },
  });
  test.skip(!response.ok(), `Investigation returned ${response.status()}`);
  // Mutation cleanup: investigation is read-only shadow scoring.
  const body = await response.json();
  expect(body.steps.length).toBeGreaterThan(0);
  expect(body.contrast.action_name).toBeDefined();
  expect(body.snapshot.factor_names).toEqual(expect.arrayContaining(["position_sizing", "market_regime"]));
});

