import { test, expect } from "../fixtures/copilot-fixture";
import { gotoTab } from "../helpers/ui";

const API = "http://127.0.0.1:8020";

test.describe("Purchasing sweep — point tests", () => {
  test("Dashboard exposes seven-factor trust context", async ({ page }) => {
    await gotoTab(page, "Dashboard");
    await expect(page.getByText(/Price memory|price_memory_index/i).first()).toBeVisible();
  });

  test("Analysis mounts trust and counterfactual surfaces", async ({ page }) => {
    await gotoTab(page, "Analysis");
    await expect(page.getByText(/Trust radar|trust weights/i).first()).toBeVisible();
    await expect(page.getByText(/Counterfactual|No counterfactual available/i).first()).toBeVisible();
  });

  test("Inventory and Performance tabs expose operational panels", async ({ page }) => {
    await gotoTab(page, "Inventory");
    await expect(page.getByText(/Waste pattern|supplier|delivery/i).first()).toBeVisible();
    await gotoTab(page, "Performance");
    await expect(page.getByText(/orders to learn|measurable|performance/i).first()).toBeVisible();
  });

  test("shared endpoints expose diagnostics, conservation, evolution, and history", async ({ request }) => {
    const diagnostics = await request.get(`${API}/api/self/diagnostics`);
    const conservation = await request.get(`${API}/api/conservation/status`);
    const evolution = await request.get(`${API}/api/self/evolution/summary`);
    const history = await request.get(`${API}/api/self/centroid-history?limit=5`);
    expect(diagnostics.status()).toBe(200);
    expect(conservation.status()).toBe(200);
    expect(evolution.status()).toBe(200);
    expect(history.status()).toBe(200);
    expect((await diagnostics.json()).epsilon_firm).toBeDefined();
    expect((await conservation.json()).reason).toBeDefined();
    expect((await evolution.json()).schema_version).toBe(1);
    expect((await history.json()).checkpoints).toBeDefined();
  });

  test("trust traps, rollback, replay, and health cache are reachable", async ({ request }) => {
    expect((await request.get(`${API}/api/self/trust-traps`)).status()).toBe(200);
    expect([200, 400, 404, 422]).toContain(
      (await request.post(`${API}/api/self/rollback`, { data: { checkpoint_id: "missing" } })).status(),
    );
    expect([200, 400, 404, 422]).toContain(
      (await request.post(`${API}/api/self/replay-score`, { data: { checkpoint_id: "missing", factors: {} } })).status(),
    );
    const health = await request.get(`${API}/health`);
    expect(health.status()).toBe(200);
    const payload = await health.json();
    expect(payload.cache_hits).toBeDefined();
    expect(payload.cache_size).toBeDefined();
  });
});

test.describe("Purchasing sweep — demo flows", () => {
  test("dashboard → order → analysis learning path remains navigable", async ({ page }) => {
    await gotoTab(page, "Dashboard");
    await expect(page.getByText(/Today's decisions|items need attention/i).first()).toBeVisible();
    await gotoTab(page, "Order");
    await expect(page.getByText(/Score the next purchase/i)).toBeVisible();
    await gotoTab(page, "Analysis");
    await expect(page.getByText(/Trust radar|counterfactual|fingerprint/i).first()).toBeVisible();
  });

  test("inventory → performance operational story", async ({ page }) => {
    await gotoTab(page, "Inventory");
    await expect(page.getByText(/Waste pattern|stockout|supplier/i).first()).toBeVisible();
    await gotoTab(page, "Performance");
    await expect(page.getByText(/measurable|orders to learn|waste/i).first()).toBeVisible();
  });

  test("all Purchasing tabs remain navigable", async ({ page }) => {
    for (const tab of ["Dashboard", "Order", "Analysis", "Inventory", "Performance"]) {
      await gotoTab(page, tab);
      await expect(page.locator("body")).not.toContainText(/Unhandled error|TypeError|Application error/i);
    }
  });
});
