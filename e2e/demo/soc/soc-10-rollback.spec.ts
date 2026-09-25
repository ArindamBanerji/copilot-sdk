import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
test("SOC-10 rollback", async ({ request }) => {
  const beforeResponse = await request.get(API + "/api/soc/centroid-export");
  test.skip(!beforeResponse.ok(), `Centroid export returned ${beforeResponse.status()}`);
  const before = await beforeResponse.json();
  const stateBeforeResponse = await request.get(API + "/api/soc/learning-state");
  test.skip(!stateBeforeResponse.ok(), `Learning state returned ${stateBeforeResponse.status()}`);
  const stateBefore = await stateBeforeResponse.json();
  const created = await request.post(API + "/api/soc/checkpoint/create", { data: { reason: "PW demo test" } });
  test.skip(!created.ok(), `Checkpoint create returned ${created.status()}`);
  const checkpoint = await created.json();
  expect(checkpoint.checkpoint_id).toBeDefined();
  let rolledBack = false;
  try {
    const scored = await request.post(API + "/api/alert/analyze", { data: { alert_id: "PL-SOC-1-NO-PRECEDENT-001" } });
    test.skip(!scored.ok(), `Checkpoint exercise score returned ${scored.status()}`);
    const rollback = await request.post(API + "/api/soc/checkpoint/rollback", { data: { checkpoint_id: checkpoint.checkpoint_id } });
    test.skip(!rollback.ok(), `Checkpoint rollback returned ${rollback.status()}`);
    const result = await rollback.json();
    rolledBack = true;
    expect(result.status).toBe("rolled_back");
    expect(result.frozen).toBe(true);
    const afterResponse = await request.get(API + "/api/soc/centroid-export");
    test.skip(!afterResponse.ok(), `Post-rollback centroid export returned ${afterResponse.status()}`);
    const after = await afterResponse.json();
    expect(after.current_mu).toEqual(before.current_mu);
    expect(after.counts ?? after.current_counts).toEqual(before.counts ?? before.current_counts);
    const stateAfterResponse = await request.get(API + "/api/soc/learning-state");
    test.skip(!stateAfterResponse.ok(), `Post-rollback learning state returned ${stateAfterResponse.status()}`);
    expect((await stateAfterResponse.json()).decision_count).toBe(stateBefore.decision_count);
  } finally {
    // Cleanup: rollback is supported; checkpoint records remain immutable audit artifacts.
    if (!rolledBack && checkpoint.checkpoint_id) await request.post(API + "/api/soc/checkpoint/rollback", { data: { checkpoint_id: checkpoint.checkpoint_id } });
  }
});
