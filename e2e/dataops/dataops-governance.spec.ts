import { test, expect } from "@playwright/test";

test.describe("DataOps evidence governance", () => {
  test("DE-PW-01: evidence labels are exposed", async ({ request }) => {
    const response = await request.get("/api/dataops/claims?context=demo");
    expect(response.ok()).toBeTruthy();
    const payload = await response.json();
    expect(payload.claims[0]).toHaveProperty("label");
  });

  test("DE-PW-02: abstention card contract is explicit", async ({ request }) => {
    const response = await request.get("/api/dataops/abstention-check?source_id=unknown");
    expect(response.ok()).toBeTruthy();
    await expect(response).toBeOK();
    expect((await response.json()).should_abstain).toBe(true);
  });

  test("DE-PW-03: holdout status panel contract is available", async ({ request }) => {
    const response = await request.get("/api/dataops/holdout/status");
    expect(response.ok()).toBeTruthy();
    expect((await response.json()).holdout_days).toBe(30);
  });
});
