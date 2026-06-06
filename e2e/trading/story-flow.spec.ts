import { type Locator, type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

function panelByHeading(page: Page, heading: string | RegExp): Locator {
  return page
    .locator("h1, h2, h3, h4", { hasText: heading })
    .locator("xpath=ancestor::*[self::article or self::section or contains(concat(' ', normalize-space(@class), ' '), ' copilot-card ')][1]")
    .first();
}

async function gotoDashboard(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await expectAnyText(page, [/Dashboard/i, /Portfolio Summary/i]);
}

async function gotoLogTrade(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expectAnyText(page, [/Log Trade/i, /Score This Trade/i]);
}

async function gotoAnalysis(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Fingerprint/i]);
}

async function gotoPerformance(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Performance Summary/i, /Trajectory/i, /IKS/i]);
}

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

test("Act 1 Dashboard: portfolio summary and category accuracy are visible", async ({ page }) => {
  await gotoDashboard(page);

  await expect(panelByHeading(page, "Portfolio Summary")).toBeVisible();
  const accuracy = panelByHeading(page, "Accuracy by Category");
  await expect(accuracy).toBeVisible();
  await expectAnyText(page, [/SC-12/i, /category accuracy/i, /No category accuracy yet/i, /verified trading decisions/i]);
});

test("Act 2 Log Trade: score/factor input workflow is visible", async ({ page }) => {
  await gotoLogTrade(page);

  await expectAnyText(page, [/Ticker/i, /Trade Thesis/i, /Research Checklist/i, /Score This Trade/i]);
});

test("Act 3 Analysis: fingerprint and decision explorer are visible", async ({ page }) => {
  await gotoAnalysis(page);

  await expectAnyText(page, [/YOUR TWO SELVES/i, /YOUR EDGE/i, /YOUR NOISE/i]);
  const explorer = panelByHeading(page, "Decision Explorer");
  await expect(explorer).toBeVisible();
  await expectAnyText(page, [/SC-14/i, /GraphStore decisions/i, /No decisions yet/i]);
});

test("Act 4 Performance: trajectory and centroid timeline are visible", async ({ page }) => {
  await gotoPerformance(page);

  await expectAnyText(page, [/Trajectory/i, /Performance Summary/i]);
  const centroid = panelByHeading(page, "Centroid Timeline");
  await expect(centroid).toBeVisible();
  await expectAnyText(page, [/SC-11/i, /centroid/i, /No centroid history yet/i]);
});

test("Act 5 Score -> Learn -> Verify returns a non-server-error outcome", async ({ page }) => {
  test.setTimeout(60_000);
  await gotoLogTrade(page);
  await fillTrade(page);

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  const score = await scoreResponse;
  expect(score.status()).toBeLessThan(500);

  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
  const learnResponse = page
    .waitForResponse((response) => response.url().includes("/api/learn") && response.request().method() === "POST", { timeout: 15_000 })
    .catch(() => null);
  await page.getByRole("button", { name: "Confirm" }).click();
  const learn = await learnResponse;
  if (learn) {
    expect([200, 503]).toContain(learn.status());
  }
  await expectAnyText(page, [/Trade confirmed/i, /system learned/i, /Reward/i, /paused/i, /Learn failed/i]);
});

test("SC-11 Centroid timeline renders populated or empty state", async ({ page }) => {
  await gotoPerformance(page);

  const centroid = panelByHeading(page, "Centroid Timeline");
  await expect(centroid).toBeVisible();
  await expectAnyText(page, [/SC-11/i, /checkpoints/i, /No centroid history yet/i]);
});

test("SC-16 Audit trail renders populated or empty state", async ({ page }) => {
  await gotoPerformance(page);

  const audit = panelByHeading(page, "Audit Trail");
  await expect(audit).toBeVisible();
  await expectAnyText(page, [/SC-16/i, /evidence/i, /No audit trail yet/i, /trails/i]);
});

test("Full Trading 5-act story traverses without console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoDashboard(page);
  await expect(panelByHeading(page, "Accuracy by Category")).toBeVisible();

  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expectAnyText(page, [/Score This Trade/i, /Research Checklist/i]);

  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expect(panelByHeading(page, "Decision Explorer")).toBeVisible();

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expect(panelByHeading(page, "Centroid Timeline")).toBeVisible();
  await expect(panelByHeading(page, "Audit Trail")).toBeVisible();

  expectNoConsoleErrors(errors);
});
