import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell, waitForScreenReady } from "../helpers/ui";

async function gotoInsight(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);
  await clickTab(page, "Insight");
  await waitForAppShell(page);
  await page.locator('[data-testid="intelligence-map"][data-screen-ready="true"]').waitFor({ timeout: 20_000 });
}

test("intelligence map renders on insight tab", async ({ page }) => {
  await gotoInsight(page);
  await expect(page.getByText("Intelligence Map", { exact: true })).toBeVisible();
});

test("intelligence map shows source nodes", async ({ page }) => {
  await gotoInsight(page);
  await expectAnyText(page, [/sources/i, /No connected sources/i]);
});

test("intelligence map shows gold dotted lines or empty state", async ({ page }) => {
  await gotoInsight(page);
  const map = page.getByTestId("intelligence-map");
  if (await map.getByTestId("gold-line-label").count()) {
    await expect(map.getByTestId("gold-line-label").first()).toContainText(/\$[\d,.]+K?\/yr/i);
  } else {
    await expect(map).toContainText(/No connected sources|Add connectors to build your intelligence map/i);
  }
});

test("intelligence map shows IKS badges or pending", async ({ page }) => {
  await gotoInsight(page);
  await expectAnyText(page, [/IKS/i, /pending/i, /mature/i, /learning/i]);
});

test("map flow verifies nodes and no jargon", async ({ page }) => {
  await gotoInsight(page);
  const panel = page.locator("section").filter({ hasText: "Source trust and quality graph" }).first();
  await panel.scrollIntoViewIfNeeded();
  await expect(panel).toContainText(/source reliability|annual value|Gold-line suggestions|No connected sources|\$[\d,.]+K?\/yr/i);
  const panelText = await panel.innerText();
  expect(panelText).not.toMatch(/centroid|DK weight|factor vector|N=/i);
});
