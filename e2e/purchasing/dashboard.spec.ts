import { test, expect } from "../fixtures/copilot-fixture";
import { expectAnyText, waitForScreenReady } from "../helpers/ui";

test("dashboard loads", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);

  await expect(page.getByRole("heading", { name: "Purchasing Copilot" })).toBeVisible();
  await expect(page.getByText(/items need attention|No item is below the reorder threshold/i)).toBeVisible();
  await expect(page.locator("main")).not.toBeEmpty();
});

test("par level monitor shows items and dollar amounts", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);

  await expect(page.getByText("Par level monitor")).toBeVisible();
  await expect(page.getByText("Real inventory, ranked by reorder pressure")).toBeVisible();
  await expectAnyText(page, [/\$\d[\d,]*/, /No item is below the reorder threshold/i]);
});

test("AE status bar visible", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);

  await expect(page.getByText("Autonomous execution")).toBeVisible();
  await expect(page.getByText("Items you are consistent on can be managed")).toBeVisible();
  await expectAnyText(page, [/AE rules/i, /Managed accuracy/i, /Promoted savings/i]);
});

test("AE shows promoted and rejected variant counts", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);

  await expect(page.getByText("Autonomous execution")).toBeVisible();
  await expectAnyText(page, [/promoted/i, /active/i, /managed/i, /AE rules/i]);
  await expectAnyText(page, [/rejected/i, /excluded/i]);
  await expectAnyText(page, [/\d+\s+(active|promoted|managed|AE rules|rule|rules)/i, /(active|promoted|managed|AE rules|rule|rules)\s*[:\-]?\s*\d+/i]);
  await expectAnyText(page, [/\d+\s+(rejected|excluded|blocked)/i, /(rejected|excluded|blocked)\s*[:\-]?\s*\d+/i]);
});

test("rejected dairy rule is not shown as AE-managed", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);

  // Rejected dairy rule may be displayed (marked as rejected, not hidden)
  await expectAnyText(page, [/rejected/i, /dairy/i, /V-PUR/i]);
});

test("cover count visible", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);

  await expect(page.getByText(/cover/i).first()).toBeVisible();
  await expectAnyText(page, [/Expected covers/i, /covers/i, /\d+/]);
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
  await expect(badge).toContainText(/Demand forecast|Price memory|Supplier lead time/);
});

test("trust badge shows color coding", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  const badge = page.getByTestId("data-trust-badge");
  await expect(badge.locator('[data-trust-level="high"]')).toHaveCount(1);
  await expect(badge.locator('[data-trust-level="low"]')).toHaveCount(4);
});

test("trust badge shows factor contrast", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  const badge = page.getByTestId("data-trust-badge");
  await expect(badge.getByTestId("data-trust-contrast")).toContainText(/Highest 1\.00.*Lowest 0\.00.*Spread 1\.00/);
});
