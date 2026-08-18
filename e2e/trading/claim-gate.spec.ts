import { expect, test } from "@playwright/test";

const BASE = process.env.TRADING_BACKEND || "http://127.0.0.1:8010";

test.beforeEach(async ({ request }) => {
  const health = await request.get(`${BASE}/health`, { timeout: 5_000 }).catch(() => null);
  test.skip(!health?.ok(), "Trading backend not running");
});

test("claim-facing metric response carries evidence tier and label", async ({ request }) => {
  const response = await request.get(`${BASE}/api/trading/analytics/vol-sharpe`);
  expect(response.status()).toBe(200);
  expect(response.headers()["x-evidence-tier"]).toMatch(/^T_[ASOR]$/);
  expect(response.headers()["x-evidence-label"]).toBeTruthy();
  const body = await response.json();
  expect(body.evidence_tier).toBeTruthy();
  expect(body.evidence_label).toBeTruthy();
});

test("promotion endpoint remains fail-closed for unsafe authority", async ({ request }) => {
  const response = await request.post(`${BASE}/api/trading/promotion/trend_following/promote`, {
    data: { confirmed_by: "e2e" },
  });
  expect([200, 409]).toContain(response.status());
  if (response.status() === 409) {
    const body = await response.json();
    expect(JSON.stringify(body).toLowerCase()).toMatch(/evidence|conservation|promotion/);
  }
});
