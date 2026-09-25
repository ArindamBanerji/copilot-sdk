import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8010";
test("PLAT-06 where-not", async ({ request }) => {
  const response=await request.get(API+"/api/platform/domain-applicability");
  test.skip(!response.ok(),"Endpoint returned "+response.status());
  const body=await response.json();
  expect(body.domains).toHaveLength(5);
  expect(new Set(body.domains.map((domain: any) => domain.name)).size).toBe(5);
  expect(body.domains.every((domain: any) => Number.isFinite(domain.conditional_fraction) && Number.isFinite(domain.chain_length))).toBe(true);
  expect(body.domains.every((domain: any) => domain.metric_tier === "EXPLORATORY")).toBe(true);
});
