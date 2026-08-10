import type { APIRequestContext } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForScreenReady } from "../helpers/ui";

const API_BASE = "http://127.0.0.1:8020";

async function queueItems(request: APIRequestContext) {
  const response = await request.get(`${API_BASE}/api/purchasing/queue`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data.queue)).toBe(true);
  return data.queue;
}

test("Queue API returns prioritized items", async ({ request }) => {
  const data = await queueItems(request);
  if (data.length > 1) {
    expect(data[0].priority_score).toBeGreaterThanOrEqual(data[1].priority_score);
  }
});

test("Queue items have confidence and action", async ({ request }) => {
  const data = await queueItems(request);
  if (data.length > 0) {
    expect(data[0]).toHaveProperty("recommended_action");
    expect(data[0]).toHaveProperty("confidence");
    expect(data[0]).toHaveProperty("priority_score");
    expect(data[0]).toHaveProperty("top_factors");
  }
});

test("Queue items have top 3 factors", async ({ request }) => {
  const data = await queueItems(request);
  if (data.length > 0 && data[0].top_factors) {
    expect(data[0].top_factors.length).toBeLessThanOrEqual(3);
  }
});

test("Queue kitchen language", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/queue`);
  expect(response.status()).toBe(200);
  const text = JSON.stringify(await response.json());
  expect(text).not.toContain("Vendor");
  expect(text).not.toContain("PurchaseOrder");
});

test("Queue respects limit param", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/queue?limit=3`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.queue.length).toBeLessThanOrEqual(3);
});

test("Queue priority scores bounded 0-1", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/queue`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  for (const item of data.queue || []) {
    expect(item.priority_score).toBeGreaterThanOrEqual(0);
    expect(item.priority_score).toBeLessThanOrEqual(1);
  }
});

test("Order tab shows queue panel", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Order");
  await expect(page.getByTestId("queue-summary")).toBeVisible({ timeout: 20_000 });
});

test("Queue table has items", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Order");
  const table = page.getByTestId("queue-table");
  await expect(table).toBeVisible({ timeout: 20_000 });
});

test("Queue items show priority", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Order");
  await expect(page.getByTestId("queue-table")).toBeVisible({ timeout: 20_000 });
  const queueItems = page.getByTestId("queue-item");
  const queueCount = await queueItems.count();
  if (queueCount > 0) {
    await expect(queueItems.first()).toBeVisible();
    await expect(queueItems.first().getByTestId("priority-badge")).toBeVisible();
  } else {
    await expect(page.getByTestId("queue-summary")).toBeVisible();
  }
});
