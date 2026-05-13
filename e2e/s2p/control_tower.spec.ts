import { test, expect } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

test("dashboard shows Control Tower intent queue", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expectAnyText(page, [/Control Tower/i, /Intent queue/i]);
  await expectAnyText(page, [/intent/i, /priority/i, /invoice/i]);
});

test("Control Tower exposes queue or empty state", async ({ page }) => {
  await page.goto("/");

  await expectAnyText(page, [/Top priority invoices/i, /No prioritized invoices available/i, /S2P-INV/i]);
});

test("Control Tower dashboard copy has no SOC vocabulary", async ({ page }) => {
  await page.goto("/");

  await clickTab(page, "Dashboard");
  await expect(page.getByText(/credential_access/i)).toHaveCount(0);
  await expect(page.getByText(/lateral_movement/i)).toHaveCount(0);
  await expect(page.getByText(/data_exfiltration/i)).toHaveCount(0);
  await expect(page.getByText(/suppress/i)).toHaveCount(0);
});
