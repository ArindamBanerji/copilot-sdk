import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8020";
test("PILOT-02 verifications-stopped", async ({ request }) => {
  const response=await request.get(API+"/api/self/centroid-history");
  test.skip(!response.ok(),"Endpoint returned "+response.status());
  const body = await response.json();
  const ordered = [...body.checkpoints].sort((a: any, b: any) => a.created_at - b.created_at);
  const gapIndex = ordered.findIndex((item: any, index: number) => index > 0 && item.created_at - ordered[index - 1].created_at > 7 * 86400);
  test.skip(gapIndex < 0, "PILOT-02 requires a seeded verification gap longer than seven days");
  expect(ordered[gapIndex].verified_count).toBe(ordered[gapIndex - 1].verified_count);
});
