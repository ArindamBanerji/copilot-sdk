import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab } from "../helpers/ui";

async function openJournal(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Journal");
  await expect(page.getByRole("heading", { name: "Trade Journal" })).toBeVisible();
}

test("JournalQueryBar visible on Journal tab", async ({ page }) => {
  await openJournal(page);

  await expect(page.getByTestId("journal-query-bar")).toBeVisible();
  await expect(page.getByPlaceholder("Ask your journal...")).toBeVisible();
});

test("JournalQueryBar submit renders results", async ({ page }) => {
  await openJournal(page);

  await page.getByPlaceholder("Ask your journal...").fill("best performing setups");
  await page.getByRole("button", { name: "Search" }).click();

  await expect(page.getByText(/trades matched|trades shown|Showing all/i).first()).toBeVisible();
});

test("JournalQueryBar empty results message", async ({ page }) => {
  await openJournal(page);

  await page.getByPlaceholder("Ask your journal...").fill("RSI weight > 999");
  await page.getByRole("button", { name: "Search" }).click();

  await expect(page.getByText("No trades match your query")).toBeVisible();
});
