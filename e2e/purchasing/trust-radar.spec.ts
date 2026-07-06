import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

const API_BASE = "http://localhost:8020";

async function gotoAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);
}

test("Trust weights API returns categories", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/trust-weights`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("phase");
  if (data.weights) {
    expect(Object.keys(data.weights)).toEqual(
      expect.arrayContaining(["protein", "produce", "dairy", "dry_goods", "beverages"]),
    );
  } else {
    expect(data.phase).toBe("learning");
  }
});

test("Trust expected weights API returns defaults", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/trust-weights/expected`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.source).toBe("preset_default");
  expect(Object.keys(data.weights)).toHaveLength(5);
});

test("Trust insights API returns list", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/trust-weights/insights`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
});

test("Trust weights have 7 factors per category", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/trust-weights/expected`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  for (const factors of Object.values<Record<string, number>>(data.weights)) {
    expect(Object.keys(factors)).toHaveLength(7);
  }
});

test("Analysis shows trust radar panel", async ({ page }) => {
  await gotoAnalysis(page);
  await expect(page.getByTestId("trust-radar-panel")).toBeVisible({ timeout: 20_000 });
});

test("Trust radar chart visible or learning state shown", async ({ page }) => {
  await gotoAnalysis(page);
  const chart = page.getByTestId("trust-radar-chart");
  const learning = page.getByTestId("trust-learning-state");
  if (await chart.count()) {
    await expect(chart).toBeVisible({ timeout: 20_000 });
  } else {
    await expect(learning).toBeVisible({ timeout: 20_000 });
  }
});

test("Trust insight cards visible when insights exist", async ({ page, request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/trust-weights/insights`);
  const insights = await response.json();
  await gotoAnalysis(page);
  if (insights.length > 0) {
    await expect(page.getByTestId("trust-insight-card").first()).toBeVisible({ timeout: 20_000 });
  } else {
    await expect(page.getByTestId("trust-radar-panel")).toBeVisible({ timeout: 20_000 });
  }
});

test("Trust factor labels use kitchen language", async ({ page }) => {
  await gotoAnalysis(page);
  const panel = page.getByTestId("trust-radar-panel");
  await expect(panel).toContainText("Whether They Show Up", { timeout: 20_000 });
  await expect(panel).toContainText("What They Used to Charge", { timeout: 20_000 });
});
