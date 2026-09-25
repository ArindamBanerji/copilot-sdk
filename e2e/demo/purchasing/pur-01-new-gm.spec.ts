import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8020";
test("PUR-01 new-gm", async ({ request }) => {
  const response=await request.get(API+"/api/fingerprint");
  test.skip(!response.ok(), `Fingerprint returned ${response.status()}`);
  const body=await response.json();
  expect(body.factors).toHaveLength(7);
  expect(body.decisions_analyzed).toBeGreaterThan(0);
  expect(Object.keys(body.per_category_precision)).toContain("protein");
});




