import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab } from "../helpers/ui";

test.setTimeout(60_000);

async function openJournal(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Journal");
  await expect(page.getByRole("heading", { name: "Trade Journal" })).toBeVisible();
}

function waitForJournalQuery(page: import("@playwright/test").Page) {
  return page.waitForResponse(
    (response) =>
      response.url().includes("/api/trading/journal/query") &&
      response.request().method() === "POST",
    { timeout: 30_000 },
  );
}

test("JournalQueryBar visible on Journal tab", async ({ page }) => {
  await openJournal(page);

  await expect(page.getByTestId("journal-query-bar")).toBeVisible();
  await expect(page.getByPlaceholder("Ask your journal...")).toBeVisible();
});

test("JournalQueryBar submit renders results", async ({ page }) => {
  await openJournal(page);

  await page.getByPlaceholder("Ask your journal...").fill("best performing setups");
  await Promise.all([waitForJournalQuery(page), page.getByRole("button", { name: "Search" }).click()]);

  await expect(page.getByText(/trades matched|trades shown|Showing all/i).first()).toBeVisible();
});

test("JournalQueryBar empty results message", async ({ page }) => {
  await openJournal(page);

  await page.getByPlaceholder("Ask your journal...").fill("RSI weight > 999");
  await Promise.all([waitForJournalQuery(page), page.getByRole("button", { name: "Search" }).click()]);

  await expect(page.getByText("No trades match your query")).toBeVisible();
});

