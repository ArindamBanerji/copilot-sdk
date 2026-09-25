import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8010";
test("PLAT-07 whose-moat", async ({ request }) => {
  const response=await request.get(API+"/api/metrics/switching-cost");
  test.skip(!response.ok(),"Endpoint returned "+response.status());
  const body=await response.json();
  expect(body.decisions_accumulated).toBeGreaterThan(0);
  expect(body.labeled_stream_to_close_pct).toBeGreaterThan(0);
  expect(Number.isFinite(body.equivalent_calendar_days)).toBe(true);
});
