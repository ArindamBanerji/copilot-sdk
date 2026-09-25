import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8030";
test("DO-02 source-lost-trust", async ({ request }) => {
  const response=await request.get(API+"/api/dataops/trust");
  test.skip(!response.ok(), `Trust endpoint returned ${response.status()}`);
  const body=await response.json();
  expect(body.factors.length).toBeGreaterThan(1);
  expect(body.verified_decisions).toBeGreaterThan(0);
  const values = body.factors.map((factor: any) => factor.dk_weight);
  expect(values.every(Number.isFinite)).toBe(true);
  expect(new Set(values).size).toBeGreaterThan(1);
});




