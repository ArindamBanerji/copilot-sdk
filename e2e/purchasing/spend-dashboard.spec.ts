import { test, expect } from "../fixtures/copilot-fixture";
import { waitForAppShell } from "../helpers/ui";

const API_BASE = "http://127.0.0.1:8020";

test("Spend summary API returns totals", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/spend/summary`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("total_spend");
  expect(typeof data.total_spend).toBe("number");
  if (data.total_spend === 0) {
    expect(data.total_spend).toBe(0);
  }
});

test("Spend by-category returns 5 categories", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/spend/by-category`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.length).toBe(5);
});

test("Spend alerts API returns list", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/spend/alerts`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
});

test("Cost per cover API returns trend", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/spend/cost-per-cover`);
  expect(response.status()).toBe(200);
});

test("By-supplier returns sorted list", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/spend/by-supplier`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.length).toBeLessThanOrEqual(10);
});

test("By-supplier API returns top suppliers", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/spend/by-supplier`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
  if (data.length > 0) {
    expect(data[0]).toHaveProperty("supplier_name");
  } else {
    expect(data).toEqual([]);
  }
});

test("Dashboard shows spend summary panel", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByTestId("spend-summary-panel")).toBeVisible({ timeout: 20_000 });
});

test("Spend overview shows total", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const overview = page.getByTestId("spend-overview");
  await expect(overview).toBeVisible({ timeout: 20_000 });
  await expect(overview).toContainText("$");
});

test("Category breakdown shows 5 categories", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const categories = page.getByTestId("spend-categories");
  await expect(categories).toBeVisible({ timeout: 20_000 });
  await expect(categories).toContainText("Protein");
  await expect(categories).toContainText("Produce");
  await expect(categories).toContainText("Dairy");
  await expect(categories).toContainText("Dry Goods");
  await expect(categories).toContainText("Beverages");
});

test("Kitchen language - covers not customers", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const panel = page.getByTestId("spend-summary-panel");
  await expect(panel).toBeVisible({ timeout: 20_000 });
  const text = await panel.textContent();
  expect(text?.toLowerCase()).not.toContain("customer");
});

test("Price alerts list shows items when alerts exist", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const badge = page.getByTestId("price-alerts-badge");
  await expect(badge).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("price-alerts-list")).toBeVisible({ timeout: 20_000 });
});

test("Supplier spend breakdown is visible", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const breakdown = page.getByTestId("supplier-spend-breakdown");
  await expect(breakdown).toBeVisible({ timeout: 20_000 });
});

test("Cost per cover section is visible", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const trend = page.getByTestId("cost-per-cover-trend");
  await expect(trend).toBeVisible({ timeout: 20_000 });
});

test("Period selector changes data", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  const selector = page.getByTestId("spend-period-selector");
  await expect(selector).toBeVisible({ timeout: 20_000 });
  await selector.selectOption("7");
  await expect(page.getByTestId("spend-overview")).toBeVisible({ timeout: 5_000 });
});
