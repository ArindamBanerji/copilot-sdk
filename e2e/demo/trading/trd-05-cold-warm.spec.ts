import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8010";
test("TRD-05 cold-warm", async ({ request }) => {
  const response = await request.get(API + "/api/trading/entrant-comparison");
  test.skip(!response.ok(), `Entrant comparison returned ${response.status()}`);
  const body = await response.json();
  expect(body.incumbent).toBeDefined();
  expect(body.entrant).toBeDefined();
  expect(body.gap).toBeDefined();
  expect(body.gap.accuracy_pp).toBeGreaterThan(0);
  expect(body.incumbent.accuracy).toBeGreaterThan(body.entrant.accuracy);
  expect(body.incumbent.verified_decisions).toBeGreaterThan(body.entrant.verified_decisions);
  expect(body.gap.note).toMatch(/verified decisions/i);
});
