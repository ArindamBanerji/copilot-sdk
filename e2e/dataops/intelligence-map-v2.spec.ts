import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function gotoInsight(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Insight");
  await waitForAppShell(page);
  await expectAnyText(page, [/Intelligence Map/i, /Source trust and quality graph/i]);
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
  await expectAnyText(page, [
    /\$180K\/year/i,
    /Gold-line suggestions appear after combination valuation/i,
    /No connected sources/i,
    /Add connectors to build your intelligence map/i,
  ]);
});

test("intelligence map shows IKS badges or pending", async ({ page }) => {
  await gotoInsight(page);
  await expectAnyText(page, [/IKS/i, /pending/i, /mature/i, /learning/i]);
});

test("map flow verifies nodes and no jargon", async ({ page }) => {
  await gotoInsight(page);
  const panel = page.locator("section").filter({ hasText: "Source trust and quality graph" }).first();
  await panel.scrollIntoViewIfNeeded();
  await expect(panel.getByText(/source reliability|annual value|Gold-line suggestions|No connected sources|\$180K\/year/i).first()).toBeVisible();
  const panelText = await panel.innerText();
  expect(panelText).not.toMatch(/centroid|DK weight|factor vector|N=/i);
});
