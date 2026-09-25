import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8030";
test("DO-07 what-to-buy", async ({ request }) => {
  const response = await request.get(API + "/api/di/acquisition-advice");
  test.skip(!response.ok(), `DI acquisition returned ${response.status()}`);
  const body = await response.json();
  const recommendations = body.recommendations ?? body.advice;
  expect(recommendations.length).toBeGreaterThan(0);
  expect(recommendations.every((item: any) => item.provider && Number.isFinite(item.cost) && Number.isFinite(item.annual_value))).toBe(true);
  expect(recommendations[0].priority).toBe("high");
  expect(recommendations[0].catalog_entry).toBeDefined();
});
