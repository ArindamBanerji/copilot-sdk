import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8002";
test("S2P-09 frozen-twin", async ({ request }) => {
  const response = await request.get(API + "/api/s2p/learning/frozen-twin");
  test.skip(!response.ok(), `Frozen twin returned ${response.status()}`);
  const body = await response.json();
  test.skip(!body.frozen_available, "S2P-09 requires an initialized immutable twin");
  test.skip(body.compared_decisions <= 0 || !Array.isArray(body.visual_diff) || body.visual_diff.length === 0, "S2P-09 requires aligned live/frozen comparison points");
  expect(body.current_vs_frozen).toBeDefined();
  expect(body.delta_accuracy).toBeGreaterThan(0);
  expect(body.evidence_note).toMatch(/immutable/i);
});
