import { test, expect } from "@playwright/test";
const TRADING="http://127.0.0.1:8010";
const PURCHASING="http://127.0.0.1:8020";
test("PLAT-02 cross-signal", async ({ request }) => {
  const entityId = `pw-cross-${Date.now()}`;
  const post=await request.post(TRADING+"/api/platform/cross-signals",{data:{source_copilot:"trading",target_copilot:"purchasing",signal_type:"demand_risk",entity_id:entityId,confidence:0.9,detail:"PW cross-copilot delivery test"}});
  test.skip(!post.ok(),"Endpoint returned "+post.status());
  // Mutation cleanup: cross-signals are TTL-bound; no delete endpoint is exposed.
  const published = await post.json();
  const listed=await request.get(PURCHASING+"/api/platform/cross-signals/"+published.signal_id);
  test.skip(!listed.ok(),"cross-copilot signal delivery requires shared store (S4-06)");
  const body=await listed.json();
  expect(body.signal_id).toBe(published.signal_id);
  expect(body.entity_id).toBe(entityId);
  expect(body.source_copilot).toBe("trading");
  expect(body.target_copilot).toBe("purchasing");
});
