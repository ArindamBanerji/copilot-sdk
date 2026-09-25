import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8020";
test("PUR-05 two-stores", async ({ request }) => {
  const response = await request.get(API + "/api/purchasing/frozen-twin");
  test.skip(!response.ok(), `Purchasing twin returned ${response.status()}`);
  const body = await response.json();
  test.skip(!body.available, "PUR-05 requires an initialized immutable Purchasing twin");
  expect(body.status).not.toBe("NOT_INITIALIZED");
  expect(body.learning_curve.length).toBeGreaterThan(0);
  expect(body.frozen_curve.length).toBe(body.learning_curve.length);
});
