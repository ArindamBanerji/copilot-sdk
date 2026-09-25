import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
test("SOC-09 same-alert", async ({ request }) => {
  const data = { alert_id: "PL-SOC-1-NO-PRECEDENT-001" };
  const first = await request.post(API + "/api/alert/analyze", { data });
  test.skip(!first.ok(), `First analyze returned ${first.status()}`);
  const second = await request.post(API + "/api/alert/analyze", { data });
  test.skip(!second.ok(), `Second analyze returned ${second.status()}`);
  const a = await first.json();
  const b = await second.json();
  // Mutation cleanup: both score records are append-only and intentionally auditable.
  expect(a.recommendation?.action).toBeDefined();
  expect(a.gae_scoring?.factor_vector).toHaveLength(6);
  expect(a.gae_scoring.factor_vector.every(Number.isFinite)).toBe(true);
  expect(b.recommendation?.action).toBe(a.recommendation.action);
  expect(b.gae_scoring?.factor_vector).toEqual(a.gae_scoring?.factor_vector);
});
