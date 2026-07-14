import { test, expect, type Page } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";

const API_BASE = "http://127.0.0.1:8002";

async function openTriageWithNovelty(page: Page, active = true) {
  await page.route("**/api/s2p/novelty/status", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        window_size: 50,
        distance_threshold: 0.6,
        total_in_window: 10,
        novelty_count: active ? 3 : 0,
        novelty_rate: active ? 0.3 : 0.0,
        alert_active: active,
        conservation_review: active,
        status: active ? "AMBER" : "GREEN",
        recommendation: active ? "Review price_variance conservation. Novelty rate 30%." : "",
        per_category: {
          price_variance: { total: 10, novel: active ? 3 : 0, novelty_rate: active ? 0.3 : 0.0 },
        },
      },
    });
  });
  await page.route("**/api/s2p/novelty/triggered-decisions?**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        decisions: active
          ? [{ sequence: 2, category: "price_variance", nearest_distance: 0.9, is_novel: true }]
          : [],
        total: active ? 1 : 0,
      },
    });
  });
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Exception Triage");
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
}

test("novelty status endpoint returns object", async ({ page }) => {
  test.setTimeout(60_000);
  const response = await page.request.get(`${API_BASE}/api/s2p/novelty/status`, { timeout: 45_000 });
  expect(response.ok()).toBeTruthy();
  expect(typeof await response.json()).toBe("object");
});

test("novelty history endpoint returns array", async ({ page }) => {
  test.setTimeout(60_000);
  const response = await page.request.get(`${API_BASE}/api/s2p/novelty/history`, { timeout: 45_000 });
  expect(response.ok()).toBeTruthy();
  expect(Array.isArray((await response.json()).entries)).toBeTruthy();
});

test("novelty rate endpoint returns rate value", async ({ page }) => {
  const response = await page.request.get(`${API_BASE}/api/s2p/novelty/rate`);
  expect(response.ok()).toBeTruthy();
  expect(typeof (await response.json()).overall_rate).toBe("number");
});

test("novelty alert banner renders on triage when active", async ({ page }) => {
  await openTriageWithNovelty(page, true);
  await expect(page.getByRole("heading", { name: /Novelty spike detected/i })).toBeVisible();
});

test("novelty banner shows category and rate", async ({ page }) => {
  await openTriageWithNovelty(page, true);
  await expect(page.locator("article", { hasText: "Novelty alert" })).toContainText("price variance");
  await expect(page.locator("article", { hasText: "Novelty alert" })).toContainText("30%");
});

test("novelty banner hidden when rate below threshold", async ({ page }) => {
  await openTriageWithNovelty(page, false);
  await expect(page.getByText("Novelty spike detected")).not.toBeVisible();
});
