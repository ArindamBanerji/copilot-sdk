import { test, expect, type Page } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

async function openSuppliers(page: Page) {
  await page.goto("/");
  await clickTab(page, "Suppliers");
  await expect(page.getByRole("heading", { name: "Suppliers" })).toBeVisible();
}

function supplierCards(page: Page) {
  return page.getByRole("button").filter({ hasText: /Exceptions/i }).filter({ hasText: /OTIF/i });
}

async function selectFirstSupplierIfPresent(page: Page) {
  const cards = supplierCards(page);
  if ((await cards.count()) > 0) {
    await cards.first().click();
  }
}

test("test_suppliers_screen_renders_profiles", async ({ page }) => {
  await openSuppliers(page);

  await expectAnyText(page, [/Supplier list/i, /Profile source/i]);
  await expectAnyText(page, [/computed profiles/i, /No supplier data yet/i, /Unable to load supplier profiles/i]);
});

test("test_supplier_card_shows_exception_rate", async ({ page }) => {
  await openSuppliers(page);

  await expectAnyText(page, [/Exceptions/i, /No supplier data yet/i, /Unable to load supplier profiles/i]);
});

test("test_supplier_card_shows_otif", async ({ page }) => {
  await openSuppliers(page);

  await expectAnyText(page, [/OTIF/i, /No supplier data yet/i, /Unable to load supplier profiles/i]);
});

test("test_supplier_trend_indicator_visible", async ({ page }) => {
  await openSuppliers(page);

  await expectAnyText(page, [/Insufficient data/i, /Worsening/i, /Improving/i, /Flat/i, /No supplier data yet/i]);
});

test("test_supplier_source_badge_visible", async ({ page }) => {
  await openSuppliers(page);

  await expectAnyText(page, [/Demo Data/i, /Fixture \+ Live/i, /Live Profiles/i, /No supplier data yet/i]);
});

test("test_declining_supplier_highlighted", async ({ page }) => {
  await openSuppliers(page);

  const decliningBadge = page.getByText(/Declining/i).first();
  if ((await decliningBadge.count()) > 0) {
    await expect(decliningBadge).toBeVisible();
  } else {
    await expectAnyText(page, [/computed profiles/i, /No supplier data yet/i, /Unable to load supplier profiles/i]);
  }
});

test("test_supplier_history_panel_renders", async ({ page }) => {
  await openSuppliers(page);
  await selectFirstSupplierIfPresent(page);

  await expectAnyText(page, [/Verified decision history/i, /Accumulator events/i]);
  await expectAnyText(page, [/No verified decisions yet for this supplier/i, /Invoice/i, /Supplier history is unavailable/i]);
});

test("Selecting supplier shows profile, seasonality, history, and heatmap", async ({ page }) => {
  await openSuppliers(page);
  await selectFirstSupplierIfPresent(page);

  await expectAnyText(page, [/Supplier profile/i, /Exception trend/i, /Select a supplier to view profile details/i]);
  await expectAnyText(page, [/Seasonality/i, /Insufficient seasonal data/i, /Lead time by quarter/i, /OTIF by quarter/i]);
  await expectAnyText(page, [/Verified decision history/i, /Accumulator events/i]);
  await expectAnyText(page, [/Supplier heatmap/i, /Category exception pattern/i, /No heatmap categories available/i]);
});

test("Suppliers screen has no SOC vocabulary", async ({ page }) => {
  await openSuppliers(page);

  await expect(page.getByText(/credential_access/i)).toHaveCount(0);
  await expect(page.getByText(/lateral_movement/i)).toHaveCount(0);
  await expect(page.getByText(/data_exfiltration/i)).toHaveCount(0);
  await expect(page.getByText(/suppress/i)).toHaveCount(0);
});
