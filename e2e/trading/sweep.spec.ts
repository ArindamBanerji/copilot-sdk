import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

const API = "http://127.0.0.1:8010";

async function openTab(page: import("@playwright/test").Page, name: string) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, name);
  await waitForAppShell(page);
}

test.describe("Trading sweep — point tests", () => {
  test("Analysis mounts regime and counterfactual surfaces", async ({ page }) => {
    await openTab(page, "Analysis");
    await expect(page.getByTestId("regime-panel")).toBeVisible();
    await expect(page.getByTestId("regime-hurst")).toBeVisible();
    await expect(page.getByRole("heading", { name: /counterfactual|what if/i }).first()).toBeVisible();
  });

  test("Analysis mounts volatility attribution", async ({ page }) => {
    await openTab(page, "Analysis");
    await expect(page.getByTestId("regime-vrp-card")).toBeVisible();
  });

  test("Performance mounts re-convergence and regime analytics", async ({ page }) => {
    await openTab(page, "Performance");
    await expect(page.getByTestId("reconvergence-panel")).toBeVisible();
    await expect(page.getByTestId("reconvergence-depth")).toContainText(/checkpoint/i);
    await expect(page.getByTestId("regime-analytics-panel")).toBeVisible();
  });

  test("Performance mounts rejection moment with reason surface", async ({ page }) => {
    await openTab(page, "Performance");
    const panel = page.getByTestId("rejection-moment-panel");
    await expect(panel).toBeVisible();
    await expect(panel).toContainText(/promot|reject|tested|unavailable/i);
  });

  test("Dashboard mounts Day Zero measurement state", async ({ page }) => {
    await openTab(page, "Dashboard");
    await expect(page.getByText(/INSTRUMENT_VALIDATED|ACCUMULATING|MEASURED|measurement/i).first()).toBeVisible();
  });

  test("situation endpoints expose the regime diagnostic set", async ({ request }) => {
    for (const path of [
      "/api/trading/situation/regime",
      "/api/trading/situation/conditioned-stats",
      "/api/trading/situation/abstention",
      "/api/trading/situation/sharpe-adjustment",
      "/api/trading/situation/regime-rejections",
    ]) {
      const response = await request.get(`${API}${path}`);
      expect(response.status(), path).toBe(200);
    }
  });

  test("trust, rollback, replay, and re-init endpoints are reachable", async ({ request }) => {
    expect((await request.get(`${API}/api/self/trust-traps`)).status()).toBe(200);
    expect([200, 400, 404, 422]).toContain(
      (await request.post(`${API}/api/self/rollback`, { data: { checkpoint_id: "missing" } })).status(),
    );
    expect([200, 400, 404, 422]).toContain(
      (await request.post(`${API}/api/self/replay-score`, { data: { checkpoint_id: "missing", factors: {} } })).status(),
    );
    expect([200, 400, 404, 422]).toContain(
      (await request.post(`${API}/api/self/regime-reinit`, { data: { regime_tag: "trending", strategy: "A" } })).status(),
    );
  });

  test("health exposes hot-path cache telemetry", async ({ request }) => {
    const response = await request.get(`${API}/health`);
    expect(response.status()).toBe(200);
    const payload = await response.json();
    expect(payload.cache_hits).toBeDefined();
    expect(payload.cache_misses).toBeDefined();
    expect(payload.cache_size).toBeDefined();
  });
});

test.describe("Trading sweep — demo flows", () => {
  test("cold mirror: Dashboard → Analysis → regime trust context", async ({ page }) => {
    await openTab(page, "Dashboard");
    await expect(page.getByText(/trust|fingerprint|measurement/i).first()).toBeVisible();
    await clickTab(page, "Analysis");
    await expect(page.getByTestId("regime-panel")).toBeVisible();
    await expect(page.getByTestId("situation-conditioned")).toBeVisible();
  });

  test("autonomy throttle: Analysis → abstention → conservation", async ({ page, request }) => {
    await openTab(page, "Analysis");
    await expect(page.getByTestId("situation-abstention")).toBeVisible();
    const response = await request.get(`${API}/api/conservation/status`);
    expect(response.status()).toBe(200);
    expect((await response.json()).status).toBeDefined();
  });

  test("rejection moment: Performance → lifecycle counts → reason text", async ({ page }) => {
    await openTab(page, "Performance");
    const panel = page.getByTestId("rejection-moment-panel");
    await expect(panel).not.toContainText(/Loading rejection summary/i, { timeout: 20_000 });
    await expect(panel).toContainText(/Recent rejections|Recent promotions|No rejected variants/i);
    // Empty seeded evolution is a valid state; populated histories expose
    // reason codes, while the empty state must explicitly say no variants.
    await expect(panel).toContainText(/conservation|correctness|variance|reason|No rejected variants|No promoted variants|unavailable/i);
  });

  test("counterfactual: Analysis → what-if panel → measurable delta", async ({ page }) => {
    await openTab(page, "Analysis");
    const heading = page.getByRole("heading", { name: /counterfactual|what if/i }).first();
    await expect(heading).toBeVisible();
    await expect(page.locator("main")).toContainText(/delta|impact|perturb|factor/i);
  });

  test("re-convergence: Performance → ARCH label → checkpoint depth", async ({ page }) => {
    await openTab(page, "Performance");
    const panel = page.getByTestId("reconvergence-panel");
    await expect(panel).toContainText(/ARCH|experimental|roadmap/i);
    await expect(page.getByTestId("reconvergence-depth")).toContainText(/checkpoint/i);
  });

  test("measurement spine remains consistent across diagnostics, conservation, evolution", async ({ request }) => {
    const diagnostics = await request.get(`${API}/api/self/diagnostics`);
    const conservation = await request.get(`${API}/api/conservation/status`);
    const evolution = await request.get(`${API}/api/self/evolution/summary`);
    expect(diagnostics.status()).toBe(200);
    expect(conservation.status()).toBe(200);
    expect(evolution.status()).toBe(200);
    expect((await diagnostics.json()).epsilon_firm).toBeDefined();
    expect((await conservation.json()).reason).toBeDefined();
    expect((await evolution.json()).schema_version).toBe(1);
  });

  test("all Trading tabs remain navigable without an error surface", async ({ page }) => {
    await page.goto("/");
    for (const tab of ["Dashboard", "Log Trade", "Analysis", "Performance"]) {
      await clickTab(page, tab);
      await waitForAppShell(page);
      await expect(page.locator("body")).not.toContainText(/Unhandled error|TypeError|Application error/i);
    }
  });
});
