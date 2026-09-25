import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForScreenReady } from "../helpers/ui";

async function gotoPerformance(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
  await expect(page.getByText("Audit & Compliance Pack", { exact: true })).toBeVisible({ timeout: 15000 });
}

test("test_audit_panel_visible", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByText("Audit & Compliance Pack", { exact: true })).toBeVisible();
});

test("test_audit_shows_decision_count", async ({ page }) => {
  await gotoPerformance(page);
  const response = await page.request.get("http://127.0.0.1:8020/api/self/diagnostics", { timeout: 30_000 });
  expect(response.ok()).toBeTruthy();
  const diagnostics = await response.json();
  const verified = diagnostics?.measurement_state?.decisions_verified ?? diagnostics?.conservation?.verified_count;
  await expect(page.getByText(/Total decisions|Verified decisions|Decision count/i).first()).toBeVisible();
  await expect(page.getByText(new RegExp(`\\b${verified}\\b`)).first()).toBeVisible();
});

test("test_audit_export_buttons", async ({ page }) => {
  await gotoPerformance(page);
  await expect(page.getByRole("link", { name: "Download JSON" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Download CSV" })).toBeVisible();
});
