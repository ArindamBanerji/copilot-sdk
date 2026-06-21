import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

const API_BASE = "http://localhost:8020";

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);
}

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
}

test("provenance badge visible on dashboard", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByTestId("provenance-badge").first()).toBeVisible({ timeout: 20_000 });
});

test("badge shows external for live data", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByTestId("provenance-badge").first()).toContainText(/External|░░|Cached/, {
    timeout: 20_000,
  });
});

test("badge shows sample for fixture data when fixture source is active", async ({ page, request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/commodity/indices`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  test.skip(!["sample", "fixture"].includes(String(data.source)), "No fixture-backed purchasing source active");

  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByTestId("commodity-provenance")).toContainText(/sample/i, { timeout: 20_000 });
});

test("commodity panel shows provenance", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByTestId("commodity-price-panel")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("commodity-provenance")).toBeVisible({ timeout: 20_000 });
});

test("spend dashboard shows provenance", async ({ page, request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/spend/summary`);
  expect(response.status()).toBe(200);

  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByTestId("spend-summary-panel")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("provenance-badge").first()).toBeVisible({ timeout: 20_000 });
});

test("par recommendations show provenance", async ({ page, request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/par/recommendations`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  for (const item of data) {
    expect(item.provenance).toBeTruthy();
    expect(item.provenance).not.toBe("sample");
  }

  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByTestId("par-level-panel")).toBeVisible({ timeout: 20_000 });
});

test("scorecard shows provenance", async ({ page, request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/suppliers/scorecards`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  for (const item of data) {
    expect(item.provenance).toBeTruthy();
    expect(item.provenance).not.toBe("sample");
  }

  await gotoPerformance(page);
  await expect(page.getByTestId("supplier-scorecard-panel")).toBeVisible({ timeout: 20_000 });
});

test("trust radar shows provenance", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("trust-radar-panel")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("provenance-badge").first()).toBeVisible({ timeout: 20_000 });
});
