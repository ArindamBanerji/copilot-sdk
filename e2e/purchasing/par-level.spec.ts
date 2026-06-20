import { test, expect } from "../fixtures/copilot-fixture";
import { waitForAppShell } from "../helpers/ui";

const API_BASE = "http://localhost:8020";

test("Par recommendations API returns items", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/par/recommendations`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
  expect(data.length).toBeGreaterThan(0);
});

test("Par recommendations include savings estimate", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/par/recommendations`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data[0]).toHaveProperty("weekly_savings_estimate");
});

test("Par status returns data source info", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/par/status`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.data_source).toBe("quickbooks_online");
  expect(data.provenance_tier).toBe("scraped_external");
});

test("Par category filter works", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/par/recommendations/protein`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
  for (const item of data) {
    expect(item.category).toBe("protein");
  }
});

test("Par provenance is not sample", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/par/recommendations`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  for (const item of data) {
    expect(item.provenance).not.toBe("sample");
  }
});

test("Dashboard shows par level panel", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByTestId("par-level-panel")).toBeVisible({ timeout: 10_000 });
});

test("Par recommendation cards visible", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByTestId("par-recommendation-card").first()).toBeVisible({ timeout: 10_000 });
});

test("Par savings shows estimate label", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const summary = page.getByTestId("par-level-summary");
  await expect(summary).toBeVisible({ timeout: 10_000 });
  await expect(summary).toContainText("estimate");
});
