import { test, expect } from "@playwright/test";
import { clickTab } from "../helpers/ui";

function main(page: import("@playwright/test").Page) {
  return page.locator("main");
}

function panel(page: import("@playwright/test").Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

test("dashboard shows Control Tower intent queue", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  const controlTower = panel(page, "Control Tower");
  await expect(controlTower).toContainText(/Intent queue/i);
  await expect(controlTower).toContainText(/intent|priority|invoice/i);
});

test("Control Tower exposes queue or empty state", async ({ page }) => {
  await page.goto("/");

  await expect(panel(page, "Control Tower")).toContainText(/Top priority invoices|No prioritized invoices available|S2P-INV/i);
});

test("Control Tower dashboard copy has no SOC vocabulary", async ({ page }) => {
  await page.goto("/");

  await clickTab(page, "Dashboard");
  await expect(main(page)).not.toContainText(/credential_access/i);
  await expect(main(page)).not.toContainText(/lateral_movement/i);
  await expect(main(page)).not.toContainText(/data_exfiltration/i);
  await expect(main(page)).not.toContainText(/suppress/i);
});
