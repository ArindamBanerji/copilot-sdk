import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

const API_BASE = "http://localhost:8020";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
}

test("Scorecard API returns supplier list", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/suppliers/scorecards`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
  expect(data.length).toBeGreaterThan(0);
});

test("Scorecard single supplier returns tier", async ({ request }) => {
  const listResponse = await request.get(`${API_BASE}/api/purchasing/suppliers/scorecards`);
  expect(listResponse.status()).toBe(200);
  const list = await listResponse.json();
  const supplierId = list[0]?.supplier_id;
  expect(supplierId).toBeTruthy();

  const response = await request.get(
    `${API_BASE}/api/purchasing/supplier/${encodeURIComponent(supplierId)}/scorecard`,
  );
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("tier");
});

test("IKS summary returns score", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/iks/summary`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("iks_score");
  expect(data.iks_score).toBeGreaterThanOrEqual(0);
  expect(data.iks_score).toBeLessThanOrEqual(100);
});

test("Scorecard provenance is not sample", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/suppliers/scorecards`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  for (const row of data) {
    expect(row.provenance).not.toBe("sample");
  }
});

test("Performance shows IKS tracker panel", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByTestId("iks-tracker-panel")).toBeVisible({ timeout: 20_000 });
});

test("Performance shows supplier scorecard panel", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByTestId("supplier-scorecard-panel")).toBeVisible({ timeout: 20_000 });
});

test("Supplier tier badges visible", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByTestId("supplier-tier-badge").first()).toBeVisible({ timeout: 20_000 });
});

test("IKS gauge shows percentage", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByTestId("iks-gauge")).toContainText("%", { timeout: 20_000 });
});
