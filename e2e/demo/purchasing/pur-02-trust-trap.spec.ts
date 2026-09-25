import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8020";
test("PUR-02 trust-trap", async ({ request }) => {
  const response=await request.get(API+"/api/fingerprint");
  test.skip(!response.ok(), `Fingerprint returned ${response.status()}`);
  const body=await response.json();
  expect(body.factors).toHaveLength(7);
  expect(body.factors.every((factor: any) => Number.isFinite(factor.sigma) && Number.isFinite(factor.weight))).toBe(true);
  const noisiest = [...body.factors].sort((a: any, b: any) => b.sigma - a.sigma)[0];
  const mostTrusted = [...body.factors].sort((a: any, b: any) => b.weight - a.weight)[0];
  expect(noisiest.sigma).toBeGreaterThan(mostTrusted.sigma);
  expect(noisiest.weight).toBeLessThan(mostTrusted.weight);
});




