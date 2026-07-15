import { expect, test } from "@playwright/test";
import { SOC, expectAnyText, isBackendHealthy, openCopilotTab } from "./demo-fixture";

test.describe.serial("Staged Trust Beats", () => {
  test("ST-1: Compounding shows latest intervention refusal", async ({ page }) => {
    test.skip(!(await isBackendHealthy(page.request, SOC)), "SOC backend is not running");
    await openCopilotTab(page, SOC, /Compounding|Decision Economics/i);

    const panel = page.getByTestId("staged-trust-panel");
    await expect(panel).toBeVisible({ timeout: 20000 });
    await expect(panel).toContainText(/system said no|intervention|refused|paused/i);
  });

  test("ST-2: Simulate Failure shows AMBER or degraded path", async ({ page }) => {
    test.skip(!(await isBackendHealthy(page.request, SOC)), "SOC backend is not running");
    await openCopilotTab(page, SOC, /Compounding|Decision Economics/i);

    await page.getByRole("button", { name: /Simulate Failure/i }).click();
    await expectAnyText(page, [/AMBER/i, /degraded/i, /blocked/i, /paused/i], 20000);
  });

  test("ST-4: Evidence Room renders enterprise stack action references", async ({ page }) => {
    test.skip(!(await isBackendHealthy(page.request, SOC)), "SOC backend is not running");
    await openCopilotTab(page, SOC, /Evidence Room|Evidence/i);

    await expect(page.locator("main")).not.toBeEmpty({ timeout: 15000 });
    await expectAnyText(page, [/Evidence/i, /Governance/i, /Audit/i, /ServiceNow|Sentinel|external/i], 20000);
  });
});
