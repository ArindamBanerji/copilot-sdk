import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function gotoLogTrade(page: Page) {
  await page.goto("/");
  await clickTab(page, "Log Trade");
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();
}

async function fillMinimumTrade(page: Page) {
  const ticker = page.getByPlaceholder("MSFT");
  await ticker.fill("MSFT");
  await page.getByRole("button", { name: "Lookup" }).click();
  await expectAnyText(page, [/MSFT/, /\$\d+(\.\d+)?/, /Source/i]);

  await page.getByLabel("Entry Price").fill("420");
  await page.getByLabel("Shares").fill("10");
  await page.getByLabel("Portfolio Value").fill("100000");
  await page.getByLabel("Stop Loss").fill("400");
  await page.getByLabel("Target").fill("460");

  const checklistItems = page.locator("section", { hasText: "Research Checklist" }).getByRole("checkbox");
  const count = await checklistItems.count();
  for (let index = 0; index < Math.min(count, 3); index += 1) {
    await checklistItems.nth(index).check();
  }
}

test("ticker lookup works", async ({ page }) => {
  await gotoLogTrade(page);

  await page.getByPlaceholder("MSFT").fill("AAPL");
  await page.getByRole("button", { name: "Lookup" }).click();

  await expectAnyText(page, [/AAPL/, /Unknown ticker/, /Source/i]);
});

test("research checklist renders", async ({ page }) => {
  await gotoLogTrade(page);

  await expect(page.getByText("Research Checklist")).toBeVisible();
  await expect(page.getByText("Written thesis documented")).toBeVisible();
  await expect(page.getByRole("checkbox").first()).toBeVisible();
});

test("score button exists", async ({ page }) => {
  await gotoLogTrade(page);

  await expect(page.getByRole("button", { name: "Score This Trade" })).toBeVisible();
  await expect(page.getByText("Factor Vector")).toBeVisible();
});

test("score produces result", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoLogTrade(page);
  await fillMinimumTrade(page);

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;

  await expectAnyText(page, [/buy/i, /hold/i, /sell/i, /confidence/i, /\d+%/]);
  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
});

test("learn response shows reward after confirm", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoLogTrade(page);
  await fillMinimumTrade(page);

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expect(page.getByRole("button", { name: "Confirm" }).first()).toBeVisible();

  const learnResponse = page.waitForResponse((response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok());
  await page.getByRole("button", { name: "Confirm" }).first().click();
  await learnResponse;

  await expectAnyText(page, [/Trade confirmed/i, /confirmed/i, /system learned/i]);
  await expectAnyText(page, [/Reward/i, /\+[0-9]+(\.[0-9]+)?/, /[0-9]+(\.[0-9]+)? reward/i]);
});

test("reasoning panel appears after scoring", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoLogTrade(page);
  await fillMinimumTrade(page);

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;

  await expectAnyText(page, [/confidence/i, /buy/i, /hold/i, /sell/i, /\d+%/]);
  await expectAnyText(page, [/Why This Recommendation/i, /Factor Analysis/i, /reasoning/i]);
  await expectAnyText(page, [/Confidence Breakdown/i, /Historical Evidence/i, /Learned from/i]);
});
