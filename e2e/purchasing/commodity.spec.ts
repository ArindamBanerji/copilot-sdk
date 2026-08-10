import { test, expect } from "../fixtures/copilot-fixture";
import { waitForScreenReady } from "../helpers/ui";

const API_BASE = "http://127.0.0.1:8020";

test("Commodity indices API returns 5 categories", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/commodity/indices`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("value");
  expect(Object.keys(data.value ?? {})).toHaveLength(5);
});

test("Commodity prices API returns data for protein", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/commodity/prices/protein`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data.value)).toBe(true);
  expect(data.value.length).toBeGreaterThan(0);
});

test("Commodity status API returns provider info", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/commodity/status`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("categories");
  expect(data.categories).toContain("protein");
});

test("Commodity provenance is not sample when live", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/commodity/indices`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  if (data.source === "live") {
    expect(data.label ?? "").not.toContain("sample");
  }
});

test("Dashboard shows commodity price panel", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await expect(page.getByTestId("commodity-price-panel")).toBeVisible({ timeout: 20_000 });
});

test("Commodity index cards visible", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  const cards = page.getByTestId("commodity-index-card");
  await expect(cards.first()).toBeVisible({ timeout: 20_000 });
});

test("Commodity provenance badge visible", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await expect(page.getByTestId("commodity-provenance")).toBeVisible({ timeout: 20_000 });
});
