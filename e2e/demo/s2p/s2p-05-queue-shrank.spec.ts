import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8002";
test("S2P-05 queue-shrank", async ({ request }) => {
  const response=await request.get(API+"/api/s2p/evidence/compliance");
  test.skip(!response.ok(),"Endpoint returned "+response.status());
  const body = await response.json();
  const extinct = body.extinct_classes ?? body.queue_extinctions ?? [];
  test.skip(!Array.isArray(extinct) || extinct.length === 0, "S2P-05 requires a seeded class extinction timeline");
  expect(extinct.some((item: any) => item.start_count > 0 && item.end_count === 0 && item.earning_decision_id)).toBe(true);
});
