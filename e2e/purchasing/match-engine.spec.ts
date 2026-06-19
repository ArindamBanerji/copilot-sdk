import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

const API_BASE = "http://localhost:8020";

test("Match queue API returns results", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/match/queue`);
  expect(response.status()).toBe(200);
});

test("Match API returns confidence score", async ({ request }) => {
  const response = await request.post(`${API_BASE}/api/purchasing/match`, {
    data: {
      order: {
        order_id: "PW-MATCH-1",
        supplier_id: "SUP-PW",
        category: "protein",
        item: "Chicken",
        quantity: 100,
        unit_price: 10,
      },
      delivery: {
        order_id: "PW-MATCH-1",
        supplier_id: "SUP-PW",
        category: "protein",
        item: "Chicken",
        quantity: 98,
        unit_price: 10,
      },
      invoice: {
        order_id: "PW-MATCH-1",
        supplier_id: "SUP-PW",
        category: "protein",
        item: "Chicken",
        quantity: 100,
        unit_price: 10.05,
      },
    },
  });
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("match_confidence");
  expect(data.match_confidence).toBeGreaterThanOrEqual(0);
  expect(data.match_confidence).toBeLessThanOrEqual(1);
});

test("Match API returns discrepancy messages", async ({ request }) => {
  const response = await request.post(`${API_BASE}/api/purchasing/match`, {
    data: {
      order: {
        order_id: "PW-MATCH-2",
        supplier_id: "SUP-PW",
        category: "protein",
        item: "Chicken",
        quantity: 100,
        unit_price: 10,
      },
      delivery: {
        order_id: "PW-MATCH-2",
        supplier_id: "SUP-PW",
        category: "protein",
        item: "Chicken",
        quantity: 85,
        unit_price: 10,
      },
      invoice: {
        order_id: "PW-MATCH-2",
        supplier_id: "SUP-PW",
        category: "protein",
        item: "Chicken",
        quantity: 100,
        unit_price: 12,
      },
    },
  });
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.discrepancy_messages).toBeDefined();
  expect(data.discrepancy_messages.length).toBeGreaterThan(0);
  expect(data.discrepancy_messages.join(" ")).toContain("Ordered");
  expect(data.discrepancy_messages.join(" ")).toContain("Invoice");
});

test("Match kitchen language - no raw QBO terms", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/match/queue`);
  expect(response.status()).toBe(200);
  const text = JSON.stringify(await response.json());
  expect(text).not.toContain("Vendor");
  expect(text).not.toContain("Bill");
  expect(text).not.toContain("PurchaseOrder");
});

test("Order tab shows match result panel", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Order");
  await expect(page.getByTestId("match-queue-summary")).toBeVisible({ timeout: 10_000 });
});

test("Match results table has rows", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Order");
  const table = page.getByTestId("match-results-table");
  await expect(table).toBeVisible({ timeout: 10_000 });
  await expect(page.getByTestId("match-result-row").first()).toBeVisible({ timeout: 10_000 });
});

test("Match confidence indicator visible", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Order");
  const confidence = page.getByTestId("match-confidence").first();
  await expect(confidence).toBeVisible({ timeout: 10_000 });
});
