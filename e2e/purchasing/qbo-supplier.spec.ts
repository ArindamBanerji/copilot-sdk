import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

const API_BASE = "http://localhost:8020";

async function gotoInventoryTab(page: Parameters<typeof waitForAppShell>[0]) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Inventory");
  await waitForAppShell(page);
}

test("QBO vendors API returns supplier list", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/qbo/vendors`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(Array.isArray(data)).toBe(true);
  expect(data.length).toBeGreaterThanOrEqual(30);
  if (data[0]) {
    expect(data[0]).toHaveProperty("supplier_name");
    expect(data[0]).not.toHaveProperty("DisplayName");
  }
});

test("QBO status API returns connection info", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/qbo/status`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("connected");
});

test("QBO price history returns dated prices", async ({ request }) => {
  const vendorsResponse = await request.get(`${API_BASE}/api/purchasing/qbo/vendors`);
  const vendors = await vendorsResponse.json();
  const supplierId = vendors[0]?.supplier_id;
  if (supplierId) {
    const invoicesResponse = await request.get(`${API_BASE}/api/purchasing/qbo/bills`);
    const invoices = await invoicesResponse.json();
    const supplierInvoice = invoices.find((invoice: Record<string, unknown>) => invoice.supplier_id === supplierId);
    const itemName = String(
      (supplierInvoice?.line_items as Array<Record<string, unknown>> | undefined)?.[0]?.item_name ?? "salmon filet",
    );
    const response = await request.get(
      `${API_BASE}/api/purchasing/qbo/price-history/${encodeURIComponent(supplierId)}/${encodeURIComponent(itemName)}`,
    );
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
    if (data[0]) {
      expect(data[0]).toHaveProperty("date");
      expect(data[0]).toHaveProperty("unit_price");
    }
  }
});

test("QBO lead times returns stats", async ({ request }) => {
  const vendorsResponse = await request.get(`${API_BASE}/api/purchasing/qbo/vendors`);
  const vendors = await vendorsResponse.json();
  const supplierId = vendors[0]?.supplier_id;
  if (supplierId) {
    const response = await request.get(`${API_BASE}/api/purchasing/qbo/lead-times/${supplierId}`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("mean_days");
  }
});

test("QBO profile endpoint returns profiler data", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/qbo/profile`);
  expect(response.status()).toBe(200);
});

test("QBO kitchen language - no raw QBO terms", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/qbo/vendors`);
  const vendors = await response.json();
  const json = JSON.stringify(vendors);
  expect(json).not.toContain("DisplayName");
  expect(json).not.toContain("VendorRef");
  expect(json).not.toContain("TotalAmt");
  expect(json).not.toContain("TxnDate");
});

test("Inventory tab shows supplier intelligence panel", async ({ page }) => {
  await gotoInventoryTab(page);
  const panel = page.getByTestId("supplier-intelligence-panel");
  await expect(panel).toBeVisible({ timeout: 20_000 });
});

test("Supplier table shows at least one row", async ({ page }) => {
  await gotoInventoryTab(page);
  const table = page.getByTestId("supplier-table");
  await expect(table).toBeVisible({ timeout: 20_000 });
  const rows = page.getByTestId("supplier-row");
  await expect(rows.first()).toBeVisible();
});

test("QBO status badge is visible", async ({ page }) => {
  await gotoInventoryTab(page);
  const badge = page.getByTestId("qbo-status-badge");
  await expect(badge).toBeVisible({ timeout: 20_000 });
});

test("Supplier names use kitchen language", async ({ page }) => {
  await gotoInventoryTab(page);
  const panel = page.getByTestId("supplier-intelligence-panel");
  await expect(panel).toBeVisible({ timeout: 20_000 });
  const text = await panel.textContent();
  expect(text).not.toContain("Vendor");
  expect(text).toContain("Supplier");
});
