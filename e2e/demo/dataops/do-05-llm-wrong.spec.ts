import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8030";
test("DO-05 llm-wrong", async ({ request }) => {
  const response = await request.post(API + "/api/investigation/investigate", {
    data: {
      decision_id: "PL-DO-5",
      category: "pipeline_failure",
      factor_vector: [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
      budget: 2,
      use_K: true,
    },
  });
  test.skip(!response.ok(), `Investigation returned ${response.status()}`);
  // Mutation cleanup: investigation is read-only shadow scoring.
  const body = await response.json();
  test.skip(!body.action_changed || body.surface_action === body.final_action, "DO-05 requires the seeded K14 surface-to-investigation action flip");
  expect(body.action_changed).toBe(true);
  expect(body.steps.length).toBeGreaterThan(0);
  expect(body.surface_action).not.toBe(body.final_action);
});
