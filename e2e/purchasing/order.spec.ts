import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function gotoOrder(page: Page) {
  await page.goto("/");
  await clickTab(page, "Order");
  await expect(page.getByRole("heading", { name: "Score the next purchase" })).toBeVisible();
}

async function scoreOrder(page: Page) {
  await expect(page.getByText("Six scorer inputs")).toBeVisible();
  const scoreButton = page.getByRole("button", { name: "Score This Order" });
  await expect(scoreButton).toBeEnabled();
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await scoreButton.click();
  await scoreResponse;
}

test("item dropdown exists", async ({ page }) => {
  await gotoOrder(page);

  await expect(page.getByText("Item")).toBeVisible();
  await expect(page.locator(".order-form-grid select").first()).toBeVisible();
});

test("cost analysis shows stockout vs waste", async ({ page }) => {
  await gotoOrder(page);

  await expect(page.getByText("Cost analysis")).toBeVisible();
  await expect(page.getByText("Stockout costs far more than waste")).toBeVisible();
  await expect(page.getByText("Stockout estimate")).toBeVisible();
  await expect(page.getByText("Waste estimate")).toBeVisible();
});

test("six auto-computed factors visible", async ({ page }) => {
  await gotoOrder(page);

  await expect(page.getByText("Six scorer inputs")).toBeVisible();
  for (const label of ["Expected demand", "Day of week", "Weather", "Events", "Historical waste", "Supplier lead time"]) {
    await expect(page.getByText(label, { exact: true }).first()).toBeVisible();
  }
});

test("score produces result", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoOrder(page);

  await scoreOrder(page);

  await expect(page.getByText("Engine assessment")).toBeVisible();
  await expect(page.getByText(/similar orders/i).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
  await expectAnyText(page, [/Order as planned/i, /Order more/i, /Order less/i, /Skip/i, /\d+%/]);
});

test("similar orders panel shows matches after score if available", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoOrder(page);

  await scoreOrder(page);

  await expect(page.getByText("Prior decisions before confirmation")).toBeVisible();
  await expectAnyText(page, [/similar orders/i, /No close historical matches/i, /Similarity/i, /Waste/i]);
});
