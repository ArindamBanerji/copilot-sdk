import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

async function openJournal(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Journal");
  await expect(page.getByRole("heading", { name: "Trade Journal" })).toBeVisible();
}

test("Journal tab is visible and clickable", async ({ page }) => {
  await page.goto("/");

  const tab = page.getByRole("tab", { name: "Journal" });
  if (await tab.count()) {
    await expect(tab.first()).toBeVisible();
  } else {
    await expect(page.getByRole("button", { name: "Journal" }).first()).toBeVisible();
  }
  await clickTab(page, "Journal");

  await expect(page.getByRole("heading", { name: "Trade Journal" })).toBeVisible();
  await expect(page.locator("main")).not.toBeEmpty();
});

test("Journal shows filters and aggregate state", async ({ page }) => {
  await openJournal(page);

  const journal = page.locator("main", { hasText: "Trade Journal" });
  await expect(journal.getByRole("heading", { name: "Journal Filters" })).toBeVisible();
  await expect(journal.getByPlaceholder("MSFT")).toBeVisible();
  await expect(journal.getByText("Total trades", { exact: true })).toBeVisible();
  await expect(journal.getByText("Win rate", { exact: true })).toBeVisible();
  await expect(journal.getByText("Avg P&L", { exact: true })).toBeVisible();
  await expect(journal.getByText("Total P&L", { exact: true })).toBeVisible();
});

test("Journal trade table or empty import state renders", async ({ page }) => {
  await openJournal(page);

  const journal = page.locator("main", { hasText: "Trade Journal" });
  await expect(journal.getByRole("heading", { name: "Trades" })).toBeVisible({ timeout: 15_000 });
  const rows = journal.locator("tbody tr");
  if ((await rows.count()) > 0) {
    await expect(journal.getByRole("columnheader", { name: "Ticker" })).toBeVisible();
    await expect(journal.getByRole("columnheader", { name: "P&L" })).toBeVisible();
    await expect(journal.getByRole("columnheader", { name: "Category" })).toBeVisible();
  } else {
    await expect(
      journal.getByText("No trades match these journal filters. Import trades or clear filters to populate the journal."),
    ).toBeVisible();
  }
});

test("Journal row detail expansion works when rows exist", async ({ page }) => {
  await openJournal(page);

  const journal = page.locator("main", { hasText: "Trade Journal" });
  await expect(journal.getByRole("heading", { name: "Trades" })).toBeVisible({ timeout: 15_000 });
  const rows = journal.locator("tbody tr");
  if ((await rows.count()) > 0) {
    await rows.first().click();
    await expect(page.locator("section", { hasText: "Trade Detail" }).first()).toBeVisible();
    await expectAnyText(page, [/Factor Breakdown/i, /Metadata/i, /Confidence/i]);
  } else {
    await expect(
      journal.getByText("No trades match these journal filters. Import trades or clear filters to populate the journal."),
    ).toBeVisible();
  }
});

test("Journal renders after reload without console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await openJournal(page);
  await page.reload();
  await clickTab(page, "Journal");

  const journal = page.locator("main", { hasText: "Trade Journal" });
  await expect(journal.getByRole("heading", { name: "Trade Journal" })).toBeVisible();
  await expect(journal.getByRole("heading", { name: "Journal Filters" })).toBeVisible();
  await expect(journal.getByText("Total trades")).toBeVisible();
  expectNoConsoleErrors(errors);
});
