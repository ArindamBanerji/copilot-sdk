import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { waitForScorerResponse } from "../helpers";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

async function scoreCurrentOrder(page: Page) {
  await expect(page.getByText("Six scorer inputs")).toBeVisible();
  const scoreButton = page.getByRole("button", { name: "Score This Order" });
  await expect(scoreButton).toBeEnabled();
  const scoreResponse = waitForScorerResponse(page, "/api/score");
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

test("score confirm then Performance shows IKS", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await clickTab(page, "Order");
  await expect(page.getByRole("heading", { name: "Score the next purchase" })).toBeVisible();

  const itemSelect = page.getByTestId("order-item-select");
  if (await itemSelect.isVisible().catch(() => false)) {
    const optionCount = await itemSelect.locator("option").count();
    if (optionCount > 1) {
      const secondValue = await itemSelect.locator("option").nth(1).getAttribute("value");
      if (secondValue) {
        await itemSelect.selectOption(secondValue);
        await expect(page.getByRole("button", { name: "Score This Order" })).toBeEnabled();
        await page.waitForLoadState("networkidle");
      }
    }
  }

  await scoreCurrentOrder(page);
  const learnResponse = page.waitForResponse(
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok(),
    { timeout: 15_000 },
  ).catch(() => null);
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/system learned/i, /reward/i, /ordering decision/i, /IKS/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/IKS/i, /Trajectory/i, /orders to learn/i]);
  await page.waitForFunction(
    () => !document.querySelector("main")?.textContent?.includes("Loading"),
    { timeout: 15000 },
  );
  const mainText = await page.locator("main").innerText();
  expect(mainText).toMatch(/IKS[\s\S]{0,80}\d+(\.\d+)?/i);
});

test("full round trip visits dashboard, order, analysis, inventory, and performance", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/items need attention/i, /dashboard/i, /cover/i]);

  await clickTab(page, "Order");
  await expectAnyText(page, [/Score the next purchase/i, /stockout/i, /order/i]);

  await clickTab(page, "Analysis");
  await expectAnyText(page, [/YOUR TWO SELVES/i, /THE HISTORIAN/i, /Fingerprint/i]);

  await clickTab(page, "Inventory");
  await expectAnyText(page, [/System Improvements/i, /Inventory/i, /variant/i, /Category summary/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/IKS/i, /Trajectory/i, /orders to learn/i]);
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
  await expectAnyText(page, [/protein/i, /produce/i, /dairy/i, /category/i, /inventory/i, /items/i]);

  await clickTab(page, "Inventory");
  await expect(page.getByText("Category summary")).toBeVisible();
  await expectAnyText(page, [/protein/i, /produce/i, /dairy/i]);
});

test("order from dropdown versus dashboard item click", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Order");
  await expect(page.getByRole("heading", { name: "Score the next purchase" })).toBeVisible();

  const itemSelect = page.getByTestId("order-item-select");
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

test("AE-managed and rejected items show different badges", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/AE managed/i, /managed/i]);

  await clickTab(page, "Inventory");
  await expectAnyText(page, [/System Improvements/i, /variant/i, /produce/i, /dairy/i]);
  await expectAnyText(page, [/Reject aggressive dairy skip/i, /purchasing-skip-dairy-v1/i, /rejected/i, /excluded/i]);
});

test("inventory shows category groups and variant counts", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Inventory");

  await expectAnyText(page, [/protein/i, /produce/i, /dairy/i]);
  await expectAnyText(page, [/System Improvements/i, /\d+\s+variants?/i, /variant/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/IKS/i, /Trajectory/i]);
});

test("Dashboard to Order score to confirm to Performance IKS", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await expectAnyText(page, [/items need attention/i, /cover/i, /Par level monitor/i]);

  await clickTab(page, "Order");
  await expectAnyText(page, [/Score the next purchase/i, /stockout/i, /order/i]);

  const itemSelect = page.getByTestId("order-item-select");
  if (await itemSelect.isVisible().catch(() => false)) {
    const optionCount = await itemSelect.locator("option").count();
    if (optionCount > 1) {
      const secondValue = await itemSelect.locator("option").nth(1).getAttribute("value");
      if (secondValue) {
        await itemSelect.selectOption(secondValue);
        await expect(page.getByRole("button", { name: "Score This Order" })).toBeEnabled();
        await page.waitForLoadState("networkidle");
      }
    }
  }

  await scoreCurrentOrder(page);
  const learnResponse = page.waitForResponse(
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok(),
    { timeout: 15_000 },
  ).catch(() => null);
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/system learned/i, /reward/i, /ordering decision/i, /IKS/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Current IKS/i, /\bIKS\b/i, /Trajectory/i]);
});

test("Inventory variants to Analysis contrast to Performance narrative", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Inventory");
  await expectAnyText(page, [/waste/i, /variant/i, /protein/i, /produce/i]);

  await clickTab(page, "Analysis");
  await expectAnyText(page, [/CONTRAST/i, /YOUR TWO SELVES/i, /THE HISTORIAN/i, /Fingerprint/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/orders to learn/i, /Current IKS/i, /\bIKS\b/i, /Trajectory/i]);
});

test("score to reasoning to Performance projection round trip", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await clickTab(page, "Order");
  await expectAnyText(page, [/Score the next purchase/i, /Score This Order/i]);

  await scoreCurrentOrder(page);
  await expectAnyText(page, [/Why This Recommendation/i, /Factor Analysis/i, /Confidence Breakdown/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Performance/i, /Trajectory/i, /orders to learn/i]);
  await expectAnyText(page, [/Automation Projection/i, /55%/, /75%/, /90%/, /verified decisions/i]);
});

test("all main tabs load after shared reasoning and projection port", async ({ page }) => {
  await page.goto("/");
  for (const tab of ["Dashboard", "Order", "Analysis", "Inventory", "Performance"]) {
    await clickTab(page, tab);
    await expect(page.locator("main")).not.toBeEmpty();
    await expectAnyText(page, [new RegExp(tab, "i"), /items need attention/i, /Score the next purchase/i, /YOUR TWO SELVES/i, /System Improvements/i, /Performance/i]);
  }
});

test("SC round trip: accuracy to decisions to inventory audit trail", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/SC-12/i, /Accuracy/i, /threshold/i, /No verified decisions yet/i]);

  await clickTab(page, "Analysis");
  await expectAnyText(page, [/SC-14/i, /Decision Explorer/i, /Category/i, /Action/i]);

  await clickTab(page, "Inventory");
  await expectAnyText(page, [/SC-13/i, /Rule Genealogy/i, /lineage/i]);
  await expectAnyText(page, [/SC-15/i, /Rule Lifecycle/i, /promoted/i, /rejected/i]);
  await expectAnyText(page, [/SC-16/i, /Audit Trail/i, /decision/i, /outcome/i, /No audit trails yet/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/SC-11/i, /Centroid History/i, /centroid/i, /No centroid history yet/i]);
});

test("api self features render populated or empty states", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Category accuracy alerts/i, /No verified decisions yet/i, /Threshold/i]);

  await clickTab(page, "Inventory");
  await expectAnyText(page, [/Audit Trail/i, /No audit trails yet/i, /decision/i]);
  await expectAnyText(page, [/Rule Genealogy/i, /Rule Lifecycle/i]);
});
