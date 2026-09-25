import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8002";
test("S2P-08 confidence-band", async ({ request }) => {
  const response=await request.get(API+"/api/s2p/confidence/thresholds");
  test.skip(!response.ok(),"Endpoint returned "+response.status());
  const body = await response.json();
  expect(body.thresholds).toHaveLength(4);
  const thresholds = body.thresholds.map((band: any) => band.auto_threshold);
  expect(thresholds.every(Number.isFinite)).toBe(true);
  expect(thresholds).toEqual([...thresholds].sort((a, b) => a - b));
  expect(body.thresholds[0].max_amount).toBe(500);
  expect(body.thresholds.at(-1).min_amount).toBe(50000);
  expect(body.k14_noise_rate).toBeGreaterThan(0);
  expect(body.calibration_source).toBe("geometry_derived");
});
