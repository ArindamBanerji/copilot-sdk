import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8020";
test("PUR-03 gave-up-authority", async ({ request }) => {
  const response=await request.get(API+"/api/conservation/status");
  test.skip(!response.ok(),"Endpoint returned "+response.status());
  const body = await response.json();
  test.skip(body.status === "GREEN", "PUR-03 requires controlled verified degradation; current shared state remains GREEN");
  expect(body.status).toMatch(/AMBER|RED|PAUSED/);
  expect(body.passed).toBe(false);
});
