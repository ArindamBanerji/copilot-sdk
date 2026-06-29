import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function gotoInsight(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Insight");
  await waitForAppShell(page);
  await expect(page.getByText("Ask Your Data", { exact: true })).toBeVisible({ timeout: 15000 });
}

test("test_nl_query_panel_visible", async ({ page }) => {
  await gotoInsight(page);
  await expect(page.getByPlaceholder("What is the most reliable source?")).toBeVisible();
  await expect(page.getByRole("button", { name: "Ask" })).toBeVisible();
});

test("test_nl_query_submit", async ({ page }) => {
  await gotoInsight(page);
  await page.getByPlaceholder("What is the most reliable source?").fill("What is the most reliable source?");
  await page.getByRole("button", { name: "Ask" }).click();
  await expectAnyText(page, [/reliable source/i, /source/i, /answer/i]);
});

test("test_nl_query_shows_evidence", async ({ page }) => {
  await gotoInsight(page);
  await page.getByPlaceholder("What is the most reliable source?").fill("What is the most reliable source?");
  await page.getByRole("button", { name: "Ask" }).click();
  await expect(page.getByText("Evidence", { exact: true })).toBeVisible({ timeout: 15000 });
});
