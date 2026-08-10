import { test, expect } from "../fixtures/copilot-fixture";
import { waitForAppShell, waitForScreenReady } from "../helpers/ui";

test("dashboard shows provenance badge", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);
  await expect(page.getByTestId("provenance-badge").first()).toBeVisible({ timeout: 20_000 });
});

test("badge reflects data source", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);
  await expect(page.getByTestId("provenance-badge").first()).toContainText(
    /External|░░|Learned|██|Sample|Cached|Unlabeled/,
    { timeout: 20_000 },
  );
});
