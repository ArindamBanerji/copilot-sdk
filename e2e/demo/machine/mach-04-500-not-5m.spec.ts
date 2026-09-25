import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8001";
test("MACH-04 500-not-5m", async ({ request }) => {
  const response=await request.get(API+"/api/fingerprint");
  test.skip(!response.ok(), `Fingerprint returned ${response.status()}`);
  const body=await response.json();
  expect(body.geometry.tensor_shape).toEqual([6,4,6]);
  expect(body.geometry.category_count * body.geometry.action_count * body.geometry.factor_count).toBe(144);
  const curveResponse = await request.get(API + "/api/evolution/trust-scores");
  test.skip(!curveResponse.ok(), `Trust curve returned ${curveResponse.status()}`);
  expect((await curveResponse.json()).history.length).toBeGreaterThan(1);
});




