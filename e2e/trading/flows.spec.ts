import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

async function fillTrade(page: Page) {
  await page.getByPlaceholder("MSFT").fill("MSFT");
  await page.getByRole("button", { name: "Lookup" }).click();
  await expectAnyText(page, [/MSFT/, /Source/i]);
  await page.getByLabel("Entry Price").fill("420");
  await page.getByLabel("Shares").fill("5");
  await page.getByLabel("Portfolio Value").fill("100000");
  await page.getByLabel("Stop Loss").fill("400");
  await page.getByLabel("Target").fill("455");
  const checklist = page.locator("section", { hasText: "Research Checklist" }).getByRole("checkbox");
  if ((await checklist.count()) > 0) {
    await checklist.first().check();
  }
}

test("full trade lifecycle: log, score, confirm, dashboard", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await clickTab(page, "Log Trade");
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();

  await fillTrade(page);
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;

  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
  await page.getByRole("button", { name: "Confirm" }).click();
  await expectAnyText(page, [/Trade confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});

test("tab navigation cycle all tabs accessible without console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await page.goto("/");

  for (const tab of ["Dashboard", "Log Trade", "Analysis", "Performance", "Trade Detail"]) {
    await clickTab(page, tab);
    await expectAnyText(page, [new RegExp(tab, "i"), /Loading/i, /Select a trade/i]);
  }

  expectNoConsoleErrors(errors);
});

test("analysis reflects pre-seeded data", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Analysis");

  await expect(page.getByText("YOUR TWO SELVES")).toBeVisible();
  await expect(page.getByText("Counterfactual")).toBeVisible();
  await expectAnyText(page, [/Fingerprint/i, /Research Impact/i, /Risk Management/i, /\d+(\.\d+)?%/]);
});
