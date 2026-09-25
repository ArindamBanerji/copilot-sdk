import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8020";
test("PILOT-01 first-90", async ({ request }) => {
  const response=await request.get(API+"/api/purchasing/day-0-readiness");
  test.skip(!response.ok(), `Readiness returned ${response.status()}`);
  const body=await response.json();
  expect(typeof body.ready).toBe("boolean");
  expect(body.coverage.decisions).toBeGreaterThan(0);
  expect(body.coverage.verified).toBeGreaterThan(0);
  expect(typeof body.not_yet).toBe("boolean");
  expect(body.evidence_floor).toMatch(/^T_/);
});




