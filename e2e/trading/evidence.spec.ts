import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

async function openLogTrade(page: Page) {
  await page.goto("/");
  await clickTab(page, "Log Trade");
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();
}

async function fillTrade(page: Page) {
  await page.getByPlaceholder("MSFT").fill("MSFT");
  await page.getByRole("button", { name: "Lookup" }).click();
  await expectAnyText(page, [/MSFT/, /Source/i]);
  await page.getByLabel("Entry Price").fill("420");
  await page.getByLabel("Shares").fill("10");
  await page.getByLabel("Portfolio Value").fill("100000");
  await page.getByLabel("Stop Loss").fill("400");
  await page.getByLabel("Target").fill("460");
}

function evidencePanel(page: Page) {
  return page.locator("section", { has: page.getByRole("heading", { name: "Evidence" }) }).first();
}

test("Evidence text appears after scoring a trade", async ({ page }) => {
  test.setTimeout(60_000);
  await openLogTrade(page);
  await fillTrade(page);

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;

  const evidence = evidencePanel(page);
  await expect(evidence).toBeVisible({ timeout: 15_000 });
  await expect(evidence.getByText(/Recommended action is/i).first()).toBeVisible();
  await expect(evidence.getByText(/Deterministic explanation/i).first()).toBeVisible();
  await expect(evidence.getByText(/Signal alignment/i).first()).toBeVisible();
  await expect(evidence.getByText(/Regime fit/i).first()).toBeVisible();
  await expect(evidence.getByText(/Decision context/i).first()).toBeVisible();
  await expect(evidence.getByText(/strong execution|partial execution|poor execution/i).first()).toBeVisible();
});

test("Evidence panel never displays forbidden factor wording", async ({ page }) => {
  await openLogTrade(page);
  await fillTrade(page);

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;

  const evidence = evidencePanel(page);
  await expect(evidence).toBeVisible({ timeout: 15_000 });
  await expect(evidence.getByText("Decision context").first()).toBeVisible();
  await expect(evidence.getByText(/Emotional indicator/i)).toHaveCount(0);
});

test("Journal detail renders evidence when a trade row exists", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Journal");
  await expect(page.getByRole("heading", { name: "Trade Journal" })).toBeVisible();

  const journal = page.locator("main", { hasText: "Trade Journal" });
  await expect(journal.getByRole("heading", { name: "Trades" })).toBeVisible({ timeout: 15_000 });
  const rows = journal.locator("tbody tr");
  if ((await rows.count()) > 0) {
    await rows.first().click();
    await expect(page.locator("section", { hasText: "Trade Detail" }).first()).toBeVisible();
    const evidence = evidencePanel(page);
    await expect(evidence).toBeVisible({ timeout: 10_000 });
    await expect(evidence.getByText(/Recommended action is/i).first()).toBeVisible();
    await expect(evidence.getByText(/Signal alignment/i).first()).toBeVisible();
    await expect(evidence.getByText(/Decision context/i).first()).toBeVisible();
  } else {
    await expect(
      journal.getByText("No trades match these journal filters. Import trades or clear filters to populate the journal."),
    ).toBeVisible();
  }
});

test("Evidence interactions have no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await openLogTrade(page);
  await fillTrade(page);

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expect(evidencePanel(page)).toBeVisible({ timeout: 15_000 });

  expectNoConsoleErrors(errors);
});
