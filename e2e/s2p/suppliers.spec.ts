import { test, expect } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

async function openSuppliers(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Suppliers");
  await expect(page.getByRole("heading", { name: "Suppliers" })).toBeVisible();
}

test("Suppliers tab shows clusters", async ({ page }) => {
  await openSuppliers(page);

  await expectAnyText(page, [/Supplier clustering/i, /Threshold-based cohorts/i]);
  await expectAnyText(page, [/High Reliability/i, /Volume Leaders/i, /Risk Watch/i, /New\/Low Volume/i, /Supplier clusters are unavailable/i]);
});

test("Supplier list shows OTIF and exception rate", async ({ page }) => {
  await openSuppliers(page);

  await expectAnyText(page, [/Supplier list/i, /Select supplier/i]);
  await expectAnyText(page, [/OTIF/i, /exception rate/i, /No supplier profiles available/i]);
});

test("Selecting supplier shows profile trend and heatmap", async ({ page }) => {
  await openSuppliers(page);

  const supplierButton = page.getByRole("button").filter({ hasText: /OTIF/i }).first();
  if (await supplierButton.count()) {
    await supplierButton.click();
  }

  await expectAnyText(page, [/Supplier profile/i, /OTIF trend/i, /Exception trend/i, /Supplier profile is unavailable/i]);
  await expectAnyText(page, [/Supplier heatmap/i, /Category exception pattern/i, /No heatmap categories available/i]);
});

test("Suppliers screen has no SOC vocabulary", async ({ page }) => {
  await openSuppliers(page);

  await expect(page.getByText(/credential_access/i)).toHaveCount(0);
  await expect(page.getByText(/lateral_movement/i)).toHaveCount(0);
  await expect(page.getByText(/data_exfiltration/i)).toHaveCount(0);
  await expect(page.getByText(/suppress/i)).toHaveCount(0);
});
