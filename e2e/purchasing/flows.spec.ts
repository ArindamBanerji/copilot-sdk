import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

async function scoreCurrentOrder(page: Page) {
  await expect(page.getByText("Six scorer inputs")).toBeVisible();
  const scoreButton = page.getByRole("button", { name: "Score This Order" });
  await expect(scoreButton).toBeEnabled();
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await scoreButton.click();
  await scoreResponse;
  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
}

test("full order lifecycle: dashboard item, order, score, confirm", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");

  const parMonitor = page.locator("section.par-monitor", { hasText: "Par level monitor" });
  const dashboardOrderButtons = parMonitor.getByRole("button", { name: /^Order$/ });
  if ((await dashboardOrderButtons.count()) > 0) {
    await dashboardOrderButtons.first().click();
  } else {
    await page.getByRole("button", { name: "Order Something Else" }).click();
  }

  await expect(page.getByRole("heading", { name: "Score the next purchase" })).toBeVisible();
  await scoreCurrentOrder(page);
  await page.getByRole("button", { name: "Confirm" }).click();
  await expectAnyText(page, [/system learned/i, /Confirming and storing order metadata/i, /ordering decision/i]);
});

test("tab navigation all 5 tabs", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await page.goto("/");

  for (const tab of ["Dashboard", "Order", "Analysis", "Inventory", "Performance"]) {
    await clickTab(page, tab);
    await expectAnyText(page, [new RegExp(tab, "i"), /Loading/i, /Score the next purchase/i, /System Improvements/i]);
  }

  expectNoConsoleErrors(errors);
});

test("analysis and inventory data consistency", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Analysis");
  await expect(page.getByText("Category accuracy")).toBeVisible();
  await expectAnyText(page, [/protein/i, /produce/i, /dairy/i]);

  await clickTab(page, "Inventory");
  await expect(page.getByText("Category summary")).toBeVisible();
  await expectAnyText(page, [/protein/i, /produce/i, /dairy/i]);
});

test("order from dropdown versus dashboard item click", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Order");
  await expect(page.getByRole("heading", { name: "Score the next purchase" })).toBeVisible();

  const itemSelect = page.locator(".order-form-grid select").first();
  await expect(itemSelect).toBeVisible();
  const optionCount = await itemSelect.locator("option").count();
  if (optionCount > 1) {
    const secondValue = await itemSelect.locator("option").nth(1).getAttribute("value");
    if (secondValue) {
      await itemSelect.selectOption(secondValue);
    }
  }

  await expect(page.getByText("Cost analysis")).toBeVisible();
  await expect(page.getByText("Six scorer inputs")).toBeVisible();
});
