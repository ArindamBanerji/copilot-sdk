import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
test("SOC-08 frozen-twin", async ({ request }) => {
  const response = await request.get(API + "/api/learning/frozen-twin");
  test.skip(!response.ok(), `Frozen twin returned ${response.status()}`);
  const body = await response.json();
  expect(Number.isFinite(body.frozen_snapshot_time)).toBe(true);
  expect(Number.isFinite(body.frozen_iks)).toBe(true);
  expect(Number.isFinite(body.current_iks)).toBe(true);
  expect(body.evidence_label).toMatch(/model|pilot|synthetic/i);
  expect(Array.isArray(body.comparison_points)).toBe(true);
  test.skip(body.comparison_points.length === 0, "SOC-08 requires replayable post-freeze verified decisions");
  const points = body.comparison_points;
  for (const point of points) {
    expect(point.decision_id).toBeTruthy();
    expect(point.verified_at_epoch).toBeGreaterThan(body.frozen_snapshot_time);
    expect(Number.isFinite(point.frozen.confidence)).toBe(true);
    expect(Number.isFinite(point.live.confidence)).toBe(true);
    expect(point.confidence_delta).toBeCloseTo(point.live.confidence - point.frozen.confidence, 10);
  }
  // Measured confidence change on identical stored inputs, not raw accuracy
  // or IKS improvement. Include negative points in the aggregate.
  const mean = points.reduce((sum: number, point: { confidence_delta: number }) => sum + point.confidence_delta, 0) / points.length;
  expect(body.compared_decisions).toBe(points.length);
  expect(body.mean_confidence_delta).toBeCloseTo(mean, 10);
  expect(mean).toBeGreaterThan(0);
});
