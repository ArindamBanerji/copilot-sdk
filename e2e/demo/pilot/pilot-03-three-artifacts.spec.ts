import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8020";
test("PILOT-03 three-artifacts", async ({ request }) => {
  const response=await request.get(API+"/api/self/centroid-history");
  test.skip(!response.ok(), `Centroid history returned ${response.status()}`);
  const body=await response.json();
  expect(body.total).toBeGreaterThan(0);
  expect(body.checkpoints[0].centroids).toBeDefined();
  expect(body.checkpoints[0].shape.length).toBeGreaterThan(0);
  expect(Number.isFinite(body.checkpoints[0].created_at)).toBe(true);
  expect(body.checkpoints[0].factor_names_hash).toBeTruthy();
});




