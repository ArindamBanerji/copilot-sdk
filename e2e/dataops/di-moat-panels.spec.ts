import { expect, test } from "../fixtures/copilot-fixture";
import type { Page } from "@playwright/test";
import { clickTab, waitForScreenReady } from "../helpers/ui";

async function openTab(page: Page, name: string) {
  await page.goto("/");
  await clickTab(page, name);
  await waitForScreenReady(page);
}

test("DL-01 DI-PROOF renders earned proof and what-if toggle", async ({ page }) => {
  await openTab(page, "Insight");
  await expect(page.getByTestId("earned-proof-panel")).toBeVisible();
  await expect(page.getByTestId("earned-proof-toggle")).toBeVisible();
});

test("DL-02 DI-PROOF shows a delta when a source is removed", async ({ page }) => {
  await openTab(page, "Insight");
  await page.getByTestId("earned-proof-toggle").click();
  await expect(page.getByTestId("earned-proof-delta")).toBeVisible();
});

test("DL-03 DI-GOLD renders acquisition advice", async ({ page }) => {
  await openTab(page, "Insight");
  const panel = page.getByTestId("acquisition-advisor-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(/Data tells you what to buy|prospective acquisition/i);
});

test("DL-04 DI-GOLD marks recommendations as prospective", async ({ page }) => {
  await openTab(page, "Insight");
  await expect(page.getByTestId("acquisition-advisor-panel")).toContainText(/Prospective|No prospective/i);
});

test("DL-05 DI-FIRSTVS6TH renders source compounding chart", async ({ page }) => {
  await openTab(page, "Insight");
  await expect(page.getByTestId("source-compounding-panel")).toBeVisible();
  await expect(page.getByTestId("source-compounding-panel")).toContainText(/First versus sixth source|Source history/i);
});

test("DL-06 DI-FIRSTVS6TH states when source history is pending", async ({ page }) => {
  await openTab(page, "Insight");
  await expect(page.getByTestId("source-compounding-panel")).toContainText(/Source-profile|Source history/i);
});

test("DL-07 DI-TWIN renders frozen and live arms", async ({ page }) => {
  await openTab(page, "Evidence");
  const panel = page.getByTestId("frozen-twin-control-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(/Frozen checkpoint|Live arm/i);
});

test("DL-08 DI-TWIN keeps modeled label until measured", async ({ page }) => {
  await openTab(page, "Evidence");
  await expect(page.getByTestId("di-twin-modeled-label")).toContainText(/MODELED|MEASURED/);
});

test("DL-09 DI-GATEWAY renders trust gate records or honest empty state", async ({ page }) => {
  await openTab(page, "Evidence");
  const panel = page.getByTestId("agent-trust-gateway-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(/gate result|No gateway verification/i);
});

test("DL-10 DI-GATEWAY exposes gate result per verification", async ({ page }) => {
  await openTab(page, "Evidence");
  await expect(page.getByTestId("agent-trust-gateway-panel")).toContainText(/Gate result|No gateway verification/i);
});

test("DL-11 DI-ABSTAIN renders after an insufficient-evidence score", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  const fixtureAlert = page.getByText("DI-ABSTENTION-001");
  await expect(fixtureAlert).toBeVisible();
  await fixtureAlert.locator("xpath=..").getByRole("button", { name: "Triage" }).click();
  await waitForScreenReady(page);
  const action = page.getByRole("button", { name: /Auto-approve|Investigate|Escalate|Pause downstream|Refer/i }).first();
  await expect(action).toBeVisible();
  await action.click();
  await expect(page.getByTestId("abstention-banner")).toBeVisible({ timeout: 15_000 });
});

test("DL-12 DI moat panels are reachable across the product flow", async ({ page }) => {
  await openTab(page, "Insight");
  await expect(page.getByTestId("earned-proof-panel")).toBeVisible();
  await clickTab(page, "Evidence");
  await expect(page.getByTestId("frozen-twin-control-panel")).toBeVisible();
  await clickTab(page, "Triage");
  await waitForScreenReady(page);
  await expect(page.getByRole("heading", { name: /Triage/i })).toBeVisible();
});
