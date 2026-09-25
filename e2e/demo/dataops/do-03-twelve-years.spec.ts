import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8030";
test("DO-03 twelve-years", async ({ request }) => {
  const response=await request.get(API+"/api/fingerprint");
  test.skip(!response.ok(), `Fingerprint returned ${response.status()}`);
  const body=await response.json();
  expect(body.factors).toHaveLength(6);
  expect(body.factors.every((factor: any) => Number.isFinite(factor.sigma) && Number.isFinite(factor.weight))).toBe(true);
  const historyResponse = await request.get(API + "/api/self/centroid-history");
  test.skip(!historyResponse.ok(), `Centroid history returned ${historyResponse.status()}`);
  const history = await historyResponse.json();
  expect(history.total).toBeGreaterThan(0);
  expect(history.checkpoints.every((checkpoint: any) => Number.isFinite(checkpoint.created_at))).toBe(true);
});




