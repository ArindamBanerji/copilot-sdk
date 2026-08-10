import { test, expect } from "@playwright/test";

const BASE = "http://localhost:8010";

test("centroid ablation returns correct shape", async ({ request }) => {
  const historyResponse = await request.get(`${BASE}/api/self/centroid-history?limit=1`);
  const history = await historyResponse.json();
  if (history.checkpoints.length > 0 && history.checkpoints[0].checkpoint_id) {
    const checkpointId = history.checkpoints[0].checkpoint_id;
    const response = await request.get(
      `${BASE}/api/self/centroid-history/${encodeURIComponent(checkpointId)}/counterfactual?window=3`,
    );
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.analysis_type).toBe("centroid_ablation");
    expect(body.held_fixed).toContain("dk_weights");
    expect(body.held_fixed).toContain("temperature");
    expect(body).toHaveProperty("decisions_rescored");
    expect(body).toHaveProperty("change_rate");
  }
});

test("centroid ablation 404 on missing checkpoint", async ({ request }) => {
  const response = await request.get(
    `${BASE}/api/self/centroid-history/nonexistent-id/counterfactual`,
  );
  expect(response.status()).toBe(404);
});
