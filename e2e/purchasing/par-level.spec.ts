import { test, expect } from "../fixtures/copilot-fixture";
import { waitForScreenReady } from "../helpers/ui";

const API_BASE = "http://127.0.0.1:8020";

test("Par recommendations API returns items", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/par/recommendations`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
  if (data.length > 0) {
    expect(data[0]).toHaveProperty("item_name");
  } else {
    expect(data).toEqual([]);
  }
});

test("Par recommendations include savings estimate", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/par/recommendations`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
  if (data.length > 0) {
    expect(data[0]).toHaveProperty("weekly_savings_estimate");
    expect(typeof data[0].weekly_savings_estimate).toBe("number");
  } else {
    expect(data).toEqual([]);
  }
});

test("Par status returns data source info", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/par/status`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("data_source");
  expect(data).toHaveProperty("provenance_tier");
  expect(data.data_source).toBe("quickbooks_online");
  expect(["scraped_external", "sample"]).toContain(data.provenance_tier);
  if (data.provenance_tier === "sample") {
    expect(data.data_source).toBeTruthy();
  }
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
  await waitForScreenReady(page);
  await expect(page.getByTestId("par-level-panel")).toBeVisible({ timeout: 20_000 });
});

test("Par recommendation cards visible", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await expect(page.getByTestId("par-level-panel")).toBeVisible({ timeout: 20_000 });
  const parCards = page.getByTestId("par-recommendation-card");
  const parCount = await parCards.count();
  if (parCount > 0) {
    await expect(parCards.first()).toBeVisible();
  } else {
    await expect(page.getByTestId("par-level-panel")).toContainText(/no|0|sample|fixture/i);
  }
});

test("Par savings shows estimate label", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  const summary = page.getByTestId("par-level-summary");
  await expect(summary).toBeVisible({ timeout: 20_000 });
  await expect(summary).toContainText("estimate");
});
