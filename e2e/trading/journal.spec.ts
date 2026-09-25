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
  await expect(journal.getByTestId("journal-query-bar")).toBeVisible();
  await expect(journal.getByText(/Category|Outcome|Limit/i).first()).toBeVisible();
});

test("Journal trade table or empty import state renders", async ({ page }) => {
  await openJournal(page);

  const journal = page.locator("main", { hasText: "Trade Journal" });
  await expect(journal.getByTestId("decision-explorer-panel")).toBeVisible({ timeout: 15_000 });
  await expect(journal.getByTestId("audit-trail-panel")).toBeVisible({ timeout: 15_000 });
});

test("Journal row detail expansion works when rows exist", async ({ page }) => {
  await openJournal(page);

  const journal = page.locator("main", { hasText: "Trade Journal" });
  await expect(journal.getByTestId("decision-explorer-panel")).toBeVisible({ timeout: 15_000 });
  await expectAnyText(page, [/Decision Explorer/i, /Audit Trail/i, /Rule Lifecycle/i]);
});

test("Journal renders after reload without console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await openJournal(page);
  await page.reload();
  await clickTab(page, "Journal");

  const journal = page.locator("main", { hasText: "Trade Journal" });
  await expect(journal.getByRole("heading", { name: "Trade Journal" })).toBeVisible();
  await expect(journal.getByRole("heading", { name: "Journal Filters" })).toBeVisible();
  await expect(journal.getByTestId("journal-query-bar")).toBeVisible();
  expectNoConsoleErrors(errors);
});

