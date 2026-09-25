import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
test("SOC-04 paused-itself", async ({ request }) => {
  const beforeResponse = await request.get(API + "/api/conservation/status");
  test.skip(!beforeResponse.ok(), `Baseline conservation returned ${beforeResponse.status()}`);
  const before = await beforeResponse.json();
  const response = await request.post(API + "/api/eval/simulate-failure", { data: { event_id: "PW-SOC-04", category: "demo", alert_id: "PW-SOC-04", source_id: "sap_s4hana", perturbation_type: "degrade", magnitude: 0.1, decisions: 3 } });
  test.skip(!response.ok(), `Failure simulation returned ${response.status()}`);
  // Mutation cleanup: simulate-failure restores its scorer snapshot before returning.
  const result = await response.json();
  expect(result.simulated).toBe(true);
  expect(result.provenance).toBe("simulated");
  expect(result.conservation_status).toMatch(/AMBER|RED|PAUSED/);
  expect(result.eval_gate?.overall_passed).toBe(false);
  expect(result.execution?.status).toBe("blocked");
  const afterResponse = await request.get(API + "/api/conservation/status");
  test.skip(!afterResponse.ok(), `Post-simulation conservation returned ${afterResponse.status()}`);
  const after = await afterResponse.json();
  expect(after.status).toBe(before.status);
  expect(after.signal).toBe(before.signal);
});
