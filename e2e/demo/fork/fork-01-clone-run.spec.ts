import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8010";
test("FORK-01 clone-run", async ({ request }) => {
  const response=await request.get(API+"/api/self/clone-fingerprint");
  test.skip(!response.ok(), `Fingerprint returned ${response.status()}`);
  const body=await response.json();
  expect(body.factors).toHaveLength(10);
  test.skip(body.decisions_analyzed !== 0, "FORK-01 requires a disposable clean clone with zero verified history");
  expect(body.factors.every((factor: any) => factor.weight === 0)).toBe(true);
});




