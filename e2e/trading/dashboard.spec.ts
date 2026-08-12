import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell, waitForScreenReady } from "../helpers/ui";

test("dashboard loads without blank screen", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expect(page.getByRole("heading", { name: "Trading Copilot" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.locator("main")).not.toBeEmpty();
});

test("shows portfolio summary", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expect(page.getByText("Portfolio Summary")).toBeVisible();
  await expect(page.getByText(/open positions/i).first()).toBeVisible();
  await expect(page.getByText("Win Rate", { exact: true }).first()).toBeVisible();
  await expectAnyText(page, [/\$\d[\d,]*/, /\d+(\.\d+)?%/, /-/]);
});

test("IKS is visible with numeric value", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expect(page.getByText("IKS").first()).toBeVisible();
  await expect(page.getByLabel(/^IKS \d+$/).first()).toBeVisible();
});

test("shows thesis breakdown", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expect(page.getByText("Thesis Breakdown")).toBeVisible();
  await expectAnyText(page, [/momentum/i, /technical/i, /fundamental/i, /event/i, /mean/i]);
});

test("shows calendar heatmap day names", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expect(page.getByText("Calendar Heatmap")).toBeVisible();
  for (const day of ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]) {
    await expect(page.getByText(day)).toBeVisible();
  }
});

test("paper badge is visible", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expectAnyText(page, [/paper/i, /with fingerprint/i, /without/i]);
  await clickTab(page, "Dashboard");
  await waitForScreenReady(page);
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});

test("trust badge is visible on dashboard", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  const badge = page.getByTestId("data-trust-badge");
  await expect(badge).toBeVisible();
  await expect(badge).toHaveAttribute("data-trust-state", "ready");
});

test("trust badge shows learned factors", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  const badge = page.getByTestId("data-trust-badge");
  await expect(badge.getByTestId("data-trust-factor")).toHaveCount(5);
  await expect(badge).toContainText(/Research depth|Market conditions|Signal confidence/);
});

test("trust badge shows color coding", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  const badge = page.getByTestId("data-trust-badge");
  await expect(badge.locator('[data-trust-level="high"]')).toHaveCount(3);
  await expect(badge.locator('[data-trust-level="medium"], [data-trust-level="low"]')).toHaveCount(2);
});

test("trust badge shows factor contrast", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  const badge = page.getByTestId("data-trust-badge");
  await expect(badge.getByTestId("data-trust-contrast")).toContainText(
    /Highest \d+\.\d{2}.*Lowest \d+\.\d{2}.*Spread \d+\.\d{2}/,
  );
});
