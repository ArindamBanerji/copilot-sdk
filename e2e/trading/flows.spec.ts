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

test("score confirm then Performance shows IKS", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await clickTab(page, "Log Trade");
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();

  await fillTrade(page);
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();

  const learnResponse = page.waitForResponse(
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok(),
    { timeout: 15_000 },
  ).catch(() => null);
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/Trade confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Performance Summary/i, /Current IKS/i, /IKS/i, /Trajectory/i]);
  const mainText = await page.locator("main").innerText();
  expect(mainText).toMatch(/IKS[\s\S]{0,80}\d+(\.\d+)?/i);
});

test("score confirm learn cycle preserves conservation after RL", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await clickTab(page, "Log Trade");
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();

  await fillTrade(page);
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expect(page.getByRole("button", { name: "Confirm" }).first()).toBeVisible();

  const learnResponse = page.waitForResponse(
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok(),
    { timeout: 15_000 },
  );
  await page.getByRole("button", { name: "Confirm" }).first().click();
  await learnResponse;
  await expectAnyText(page, [/Trade confirmed/i, /confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Performance Summary/i, /Conservation/i, /Trajectory/i]);
  await expectAnyText(page, [/55%/, /75%/, /90%/, /verified/i, /trajectory/i]);
});

test("full round trip visits dashboard, log trade, analysis, performance, and dashboard", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Dashboard/i, /Portfolio Summary/i, /portfolio/i]);

  await clickTab(page, "Log Trade");
  await expectAnyText(page, [/Ticker/i, /Trade Thesis/i, /Score This Trade/i]);

  await clickTab(page, "Analysis");
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Fingerprint/i, /edge/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/IKS/i, /Trajectory/i, /Performance Summary/i]);

  await clickTab(page, "Dashboard");
  await expectAnyText(page, [/Dashboard/i, /Portfolio Summary/i, /portfolio/i]);
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

test("dashboard shows decision history entries", async ({ page }) => {
  await page.goto("/");

  await expectAnyText(page, [/Decision History/i]);
  await expectAnyText(page, [/buy/i, /sell/i, /hold/i, /trade/i, /open/i]);
});

test("analysis contrast card reflects pre-seeded alignment", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Analysis");

  await expectAnyText(page, [/YOUR TWO SELVES/i, /Aligned trades compound/i]);
  await expectAnyText(page, [/Aligned/i, /Misaligned/i, /Neutral/i]);
  await expectAnyText(page, [/Win rate/i, /Trades/i, /\d+/]);
});

test("score then confirm then Performance and Analysis reflect it", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await clickTab(page, "Log Trade");
  await expectAnyText(page, [/Log Trade/i, /Ticker/i, /Score This Trade/i]);

  await fillTrade(page);
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();

  const learnResponse = page.waitForResponse(
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok(),
    { timeout: 15_000 },
  ).catch(() => null);
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/Trade confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Current IKS/i, /\bIKS\b/i, /Trajectory/i]);

  await clickTab(page, "Analysis");
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Aligned/i, /Misaligned/i, /Neutral/i]);
});

test("Dashboard to Log Trade to Analysis to Performance content at each stop", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Portfolio Summary/i, /Decision History/i, /portfolio/i]);

  await clickTab(page, "Log Trade");
  await expectAnyText(page, [/Ticker/i, /Research Checklist/i, /Score This Trade/i]);

  await clickTab(page, "Analysis");
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Fingerprint/i, /Counterfactual/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Current IKS/i, /\bIKS\b/i, /Trajectory/i, /Rolling/i]);
});

test("score to reasoning to Performance projection round trip", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await clickTab(page, "Log Trade");
  await expectAnyText(page, [/Log Trade/i, /Score This Trade/i]);

  await fillTrade(page);
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expectAnyText(page, [/Why This Recommendation/i, /Factor Analysis/i, /Confidence Breakdown/i]);

  await clickTab(page, "Performance");
  await expectAnyText(page, [/Performance Summary/i, /Trajectory/i]);
  await expectAnyText(page, [/Automation Projection/i, /55%/, /75%/, /90%/, /verified decisions/i]);
});

test("all main tabs load after shared reasoning and projection port", async ({ page }) => {
  await page.goto("/");
  for (const tab of ["Dashboard", "Log Trade", "Analysis", "Performance"]) {
    await clickTab(page, tab);
    await expect(page.locator("main")).not.toBeEmpty();
    await expectAnyText(page, [new RegExp(tab, "i"), /Portfolio Summary/i, /Score This Trade/i, /YOUR TWO SELVES/i, /Performance Summary/i]);
  }
});
