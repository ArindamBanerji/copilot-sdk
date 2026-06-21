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

  await expect(page.getByText("Item", { exact: true })).toBeVisible();
  await expect(page.getByTestId("order-item-select")).toBeVisible();
});

test("cost analysis shows stockout vs waste", async ({ page }) => {
  await gotoOrder(page);

  await expect(page.getByText("Cost analysis")).toBeVisible();
  await expect(page.getByText("Stockout costs far more than waste")).toBeVisible();
  await expect(page.getByText("Stockout estimate")).toBeVisible();
  await expect(page.getByText("Waste estimate")).toBeVisible();
});

test("cost framing narrative visible", async ({ page }) => {
  await gotoOrder(page);

  await expectAnyText(page, [/Stockout costs far more than waste/i, /service-risk spread/i, /guarded against zero waste/i]);
  await expectAnyText(page, [/Order cost/i, /Stockout estimate/i, /Waste estimate/i, /Risk ratio/i]);
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

test("confirm shows reward after scoring", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoOrder(page);

  await scoreOrder(page);
  await expectAnyText(page, [/confidence/i, /Engine assessment/i, /\d+%/]);

  await expect(page.getByTestId("reason-selector")).toBeVisible({ timeout: 20_000 });
  await page.getByTestId("reason-selector").selectOption("supplier_preference");
  const learnResponse = page.waitForResponse((response) => response.url().includes("/api/purchasing/verify") && response.request().method() === "POST" && response.ok());
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/Learned/i, /system learned/i, /ordering decision/i, /Reward/i, /IKS/i]);
});

test("learn response shows reward after confirm", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoOrder(page);

  await scoreOrder(page);
  await expect(page.getByRole("button", { name: "Confirm" }).first()).toBeVisible();

  await expect(page.getByTestId("reason-selector")).toBeVisible({ timeout: 20_000 });
  await page.getByTestId("reason-selector").selectOption("supplier_preference");
  const learnResponse = page.waitForResponse((response) => response.url().includes("/api/purchasing/verify") && response.request().method() === "POST" && response.ok());
  await page.getByRole("button", { name: "Confirm" }).first().click();
  await learnResponse;

  await expectAnyText(page, [/Learned/i, /confirmed/i, /system learned/i, /ordering decision/i]);
  await expectAnyText(page, [/Reward/i, /\+[0-9]+(\.[0-9]+)?/, /[0-9]+(\.[0-9]+)? reward/i]);
});

test("similar orders panel shows matches after score if available", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoOrder(page);

  await scoreOrder(page);

  await expect(page.getByText("Prior decisions before confirmation")).toBeVisible();
  await expectAnyText(page, [/similar orders/i, /No close historical matches/i, /Similarity/i, /Waste/i]);
});

test("reasoning panel appears after scoring", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoOrder(page);

  await scoreOrder(page);

  await expectAnyText(page, [/confidence/i, /Engine assessment/i, /\d+%/]);
  await expectAnyText(page, [/Why This Recommendation/i, /Factor Analysis/i, /reasoning/i]);
  await expectAnyText(page, [/Confidence Breakdown/i, /Historical Evidence/i, /Learned from/i]);
});
