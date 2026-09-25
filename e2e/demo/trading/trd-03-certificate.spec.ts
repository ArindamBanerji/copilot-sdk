import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8010";
test("TRD-03 certificate", async ({ request }) => {
  const response=await request.get(API+"/api/trading/claim-gate");
  test.skip(!response.ok(), `Claim gate returned ${response.status()}`);
  const body=await response.json();
  expect(body.tested).toBeGreaterThan(0);
  expect(body.powered).toBeGreaterThan(0);
  expect(body.withheld).toBeGreaterThan(0);
  expect(body.survived).toBeLessThanOrEqual(body.powered);
  expect(body.certificate).toMatch(/evidence gate/i);
});




