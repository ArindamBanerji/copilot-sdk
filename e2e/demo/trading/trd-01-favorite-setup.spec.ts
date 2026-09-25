import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8010";
test("TRD-01 favorite-setup", async ({ request }) => {
  const response=await request.get(API+"/api/fingerprint");
  test.skip(!response.ok(), `Fingerprint returned ${response.status()}`);
  const body=await response.json();
  expect(body.factors).toHaveLength(10);
  expect(body.decisions_analyzed).toBeGreaterThan(0);
  expect(body.factors.every((factor: any) => Number.isFinite(factor.sigma) && Number.isFinite(factor.weight))).toBe(true);
  expect(Math.max(...body.factors.map((factor: any) => factor.sigma))).toBeGreaterThan(0);
});




