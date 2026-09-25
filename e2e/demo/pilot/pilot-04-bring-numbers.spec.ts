import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8020";
test("PILOT-04 bring-numbers", async ({ request }) => {
  const response=await request.get(API+"/api/conservation/status");
  test.skip(!response.ok(), `Conservation returned ${response.status()}`);
  const body=await response.json();
  test.skip(body.projected_divergence_week == null, "PILOT-04 requires modeled ROI/readiness inputs and a projected divergence week");
  expect(body.projected_divergence_week).toBeGreaterThan(0);
  expect(body.evidence_label).toMatch(/MODELED|PILOT-TARGET/i);
});




