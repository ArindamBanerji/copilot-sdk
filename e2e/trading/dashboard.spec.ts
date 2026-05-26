import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

test("dashboard loads without blank screen", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);

  await expect(page.getByRole("heading", { name: "Trading Copilot" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.locator("main")).not.toBeEmpty();
});

test("shows portfolio summary", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);

  await expect(page.getByText("Portfolio Summary")).toBeVisible();
  await expect(page.getByText(/open positions/i).first()).toBeVisible();
  await expect(page.getByText("Win Rate", { exact: true }).first()).toBeVisible();
  await expectAnyText(page, [/\$\d[\d,]*/, /\d+(\.\d+)?%/, /-/]);
});

test("IKS is visible with numeric value", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);

  await expect(page.getByText("IKS").first()).toBeVisible();
  await expect(page.getByLabel(/^IKS \d+$/).first()).toBeVisible();
});

test("shows thesis breakdown", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);

  await expect(page.getByText("Thesis Breakdown")).toBeVisible();
  await expectAnyText(page, [/momentum/i, /technical/i, /fundamental/i, /event/i, /mean/i]);
});

test("shows calendar heatmap day names", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);

  await expect(page.getByText("Calendar Heatmap")).toBeVisible();
  for (const day of ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]) {
    await expect(page.getByText(day)).toBeVisible();
  }
});

test("paper badge is visible", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);

  await expectAnyText(page, [/paper/i, /with fingerprint/i, /without/i]);
  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});
