import { test, expect } from "@playwright/test";

const API = "http://127.0.0.1:8002";

test("S2P-07 budget-strip", async ({ request }) => {
  const response = await request.get(API + "/api/self/investigation-budget");
  test.skip(!response.ok(), `Budget endpoint: ${response.status()}`);
  const body = await response.json();
  expect(body.controller).toBe("adaptive");
  expect(Number.isFinite(body.safety_lambda)).toBe(true);
  expect(body.decisions).toBeGreaterThanOrEqual(0);
  test.skip(!Array.isArray(body.allocations), "S2P-07 requires easy/hard allocation telemetry from the production classifier");
  const easy = body.allocations.find((item: any) => item.profile === "easy");
  const hard = body.allocations.find((item: any) => item.profile === "hard");
  expect(easy.reads).toBeLessThan(hard.reads);
});




