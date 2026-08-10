import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForScreenReady } from "../helpers/ui";

const DATAOPS_API = "http://127.0.0.1:8030";

test("centroid history response includes quality field", async ({ request }) => {
  const response = await request.get(`${DATAOPS_API}/api/self/centroid-history?limit=1`);
  expect(response.status()).toBe(200);

  const body = await response.json();
  expect(body).toHaveProperty("checkpoints");
  expect(body).toHaveProperty("total");
  if (body.checkpoints.length > 0) {
    const checkpoint = body.checkpoints[0];
    expect(checkpoint).toHaveProperty("quality");
    if (checkpoint.quality !== null) {
      expect(checkpoint.quality).toHaveProperty("rolling_accuracy");
      expect(checkpoint.quality).toHaveProperty("policy_version");
    }
  }
});

test("checkpoint created_at is numeric epoch", async ({ request }) => {
  const response = await request.get(`${DATAOPS_API}/api/self/centroid-history?limit=1`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  if (body.checkpoints.length > 0) {
    expect(typeof body.checkpoints[0].created_at).toBe("number");
  }
});

test("centroid timeline loads without browser errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await page.goto("/");
  await clickTab(page, "Insight");
  await waitForScreenReady(page);
  await expect(page.getByTestId("centroid-timeline")).toBeVisible();
  expectNoConsoleErrors(errors.filter((error) => !/favicon|manifest/i.test(error)));
});

test("centroid ablation returns the contract shape when a V2 checkpoint exists", async ({ request }) => {
  const historyResponse = await request.get(`${DATAOPS_API}/api/self/centroid-history?limit=50`);
  expect(historyResponse.status()).toBe(200);
  const history = await historyResponse.json();
  const checkpoint = history.checkpoints.find((item: { checkpoint_id?: string }) => item.checkpoint_id);

  test.skip(!checkpoint, "No V2 checkpoint is available in the live DataOps fixture");
  const response = await request.get(
    `${DATAOPS_API}/api/self/centroid-history/${encodeURIComponent(checkpoint.checkpoint_id)}/counterfactual?window=5`,
  );
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.analysis_type).toBe("centroid_ablation");
  expect(body.held_fixed).toContain("dk_weights");
  expect(body.held_fixed).toContain("temperature");
  expect(body).toHaveProperty("decisions_rescored");
  expect(body).toHaveProperty("change_rate");
});

test("centroid ablation returns 404 for a missing checkpoint", async ({ request }) => {
  const response = await request.get(
    `${DATAOPS_API}/api/self/centroid-history/nonexistent/counterfactual`,
  );
  expect(response.status()).toBe(404);
});
