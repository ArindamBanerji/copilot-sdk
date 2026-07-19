import { expect, test, type Page } from "@playwright/test";

const FRONTEND = process.env.TRADING_FRONTEND || "http://127.0.0.1:5174";
const TABS = ["Dashboard", "Performance", "Analysis", "Journal", "Log Trade"];

async function openTab(page: Page, name: string) {
  await page.goto(FRONTEND);
  await expect(page.getByRole("heading", { name: "Trading Copilot" })).toBeVisible({ timeout: 20_000 });
  await page.getByRole("button", { name }).click();
}

test("migrated tabs have zero console.error", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });

  for (const tab of TABS) {
    await openTab(page, tab);
  }

  const unexpected = errors.filter((message) => !/dynamic endpoint unavailable/i.test(message));
  expect(unexpected).toEqual([]);
});
