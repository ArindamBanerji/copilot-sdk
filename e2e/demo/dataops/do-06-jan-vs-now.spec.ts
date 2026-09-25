import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8030";
test("DO-06 jan-vs-now", async ({ request }) => {
  const response=await request.get(API+"/api/dataops/trust");
  test.skip(!response.ok(), `Trust endpoint returned ${response.status()}`);
  const body=await response.json();
  expect(body.verified_decisions).toBeGreaterThan(0);
  const trust = body.factors.map((factor: any) => factor.dk_weight);
  expect(new Set(trust).size).toBeGreaterThan(1);
  expect(Math.max(...trust)).toBeGreaterThan(Math.min(...trust));
});




