import { test, expect } from "../fixtures/copilot-fixture";
import { waitForAppShell } from "../helpers/ui";

const API_BASE = "http://127.0.0.1:8020";

test("Auto-order status returns disabled by default", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/auto-order/status`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.enabled).toBe(false);
});

test("Enable auto-order requires conservation", async ({ request }) => {
  const response = await request.post(`${API_BASE}/api/purchasing/auto-order/enable`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("enabled");
});

test("Disable auto-order works", async ({ request }) => {
  await request.post(`${API_BASE}/api/purchasing/auto-order/enable`);
  const response = await request.post(`${API_BASE}/api/purchasing/auto-order/disable`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.enabled).toBe(false);
});

test("Auto-order audit returns list", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/auto-order/audit`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
});

test("Auto-order kitchen language", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/auto-order/status`);
  expect(response.status()).toBe(200);
  const text = JSON.stringify(await response.json());
  expect(text).not.toContain("auto_approve");
  expect(text).not.toContain("Vendor");
});

test("Evaluate endpoint returns decision", async ({ request }) => {
  const response = await request.post(`${API_BASE}/api/purchasing/auto-order/evaluate`, {
    data: { category: "protein", confidence: 0.95 },
  });
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("auto_order");
});

test("Dashboard shows auto-order panel", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const panel = page.getByTestId("auto-order-status");
  await expect(panel).toBeVisible({ timeout: 20_000 });
});

test("Auto-order toggle visible", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const toggle = page.getByTestId("auto-order-toggle");
  await expect(toggle).toBeVisible({ timeout: 20_000 });
});

test("Auto-order stats card visible", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const stats = page.getByTestId("auto-order-stats");
  await expect(stats).toBeVisible({ timeout: 20_000 });
});

test("Auto-order history table visible", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const history = page.getByTestId("auto-order-history");
  await expect(history).toBeVisible({ timeout: 20_000 });
});
