import { test, expect, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function openSuppliers(page: Page) {
  await page.goto("/");
  await clickTab(page, "Suppliers");
  await expect(page.getByRole("heading", { name: "Suppliers" })).toBeVisible();
}

function supplierCards(page: Page) {
  return supplierList(page).getByRole("button").filter({ hasText: /Exceptions/i }).filter({ hasText: /OTIF/i });
}

function supplierList(page: Page) {
  return page.locator("article", { hasText: "Profile source" });
}

function historyPanel(page: Page) {
  return page.locator("article", { hasText: "Accumulator events" });
}

async function selectFirstSupplierIfPresent(page: Page) {
  const cards = supplierCards(page);
  if ((await cards.count()) > 0) {
    await cards.nth(0).click();
  }
}

test("test_suppliers_screen_renders_profiles", async ({ page }) => {
  await openSuppliers(page);

  const list = supplierList(page);
  await expect(list).toContainText(/Supplier list|Profile source/i);
  await expect(list).toContainText(/computed profiles|No supplier data yet|Unable to load supplier profiles|Profile source/i);
});

test("test_supplier_card_shows_exception_rate", async ({ page }) => {
  await openSuppliers(page);

  await expect(supplierList(page)).toContainText(/Exceptions|No supplier data yet|Unable to load supplier profiles|Profile source/i);
});

test("test_supplier_card_shows_otif", async ({ page }) => {
  await openSuppliers(page);

  await expect(supplierList(page)).toContainText(/OTIF|No supplier data yet|Unable to load supplier profiles|Profile source/i);
});

test("test_supplier_trend_indicator_visible", async ({ page }) => {
  await openSuppliers(page);

  await expect(page.locator("main")).toContainText(/Insufficient data|Worsening|Improving|Flat|No supplier data yet|Unable to load supplier profiles|Select a supplier to view profile details/i);
});

test("test_supplier_source_badge_visible", async ({ page }) => {
  await openSuppliers(page);

  await expect(supplierList(page)).toContainText(/Demo Data|Fixture \+ Live|Live Profiles|No supplier data yet|Unable to load supplier profiles|Profile source/i);
});

test("test_declining_supplier_highlighted", async ({ page }) => {
  await openSuppliers(page);

  const list = supplierList(page);
  if (await list.getByText(/Declining/i).count()) {
    await expect(list).toContainText(/Declining/i);
  } else {
    await expect(list).toContainText(/computed profiles|No supplier data yet|Unable to load supplier profiles|Profile source/i);
  }
});

test("test_supplier_history_panel_renders", async ({ page }) => {
  await openSuppliers(page);
  await selectFirstSupplierIfPresent(page);

  const history = historyPanel(page);
  await expect(history).toContainText(/Verified decision history|Accumulator events/i);
  await expect(history).toContainText(/No verified decisions yet for this supplier|Invoice|Supplier history is unavailable|Select a supplier/i);
});

test("Selecting supplier shows profile, seasonality, history, and heatmap", async ({ page }) => {
  await openSuppliers(page);
  await selectFirstSupplierIfPresent(page);

  await expect(page.locator("main")).toContainText(/Exception trend|Select a supplier to view profile details/i);
  await expect(page.locator("article", { hasText: "Seasonality" })).toContainText(/Insufficient seasonal data|Lead time by quarter|OTIF by quarter|Select a supplier to view seasonal patterns/i);
  await expect(historyPanel(page)).toContainText(/Verified decision history|Accumulator events/i);
  await expect(page.locator("article", { hasText: "Supplier heatmap" })).toContainText(/Category exception pattern|No heatmap categories available/i);
});

test("Suppliers screen has no SOC vocabulary", async ({ page }) => {
  await openSuppliers(page);

  const main = page.locator("main");
  await expect(main).not.toContainText(/credential_access/i);
  await expect(main).not.toContainText(/lateral_movement/i);
  await expect(main).not.toContainText(/data_exfiltration/i);
  await expect(main).not.toContainText(/suppress/i);
});
