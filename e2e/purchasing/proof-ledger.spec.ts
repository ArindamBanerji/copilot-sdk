import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForScreenReady } from "../helpers/ui";

test("proof ledger and Day-0 readiness render on Performance", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
  await expect(page.getByTestId("purchasing-proof-panel")).toBeVisible();
  await expect(page.getByText("Proof Ledger")).toBeVisible();
  await expect(page.getByText("Day-0 Readiness")).toBeVisible();
  await expect(page.getByText("Legal exposure")).toBeVisible();
});
