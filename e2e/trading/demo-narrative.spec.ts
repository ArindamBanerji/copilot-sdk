import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function openPerformanceTab(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Performance Summary/i, /Trajectory/i, /IKS/i]);
}

async function openDashboard(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expectAnyText(page, [/Dashboard/i, /Decision History/i]);
}

async function mockTransferStatus(page: Page) {
  await page.route("**/api/transfer/status", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        warm_started: true,
        source_copilot: "soc",
        patterns_transferred: 3,
        categories_transferred: 3,
        source_accuracy: 0.84,
        provenance: "transfer",
      }),
    });
  });
}

async function mockArchetypeCurrent(page: Page) {
  await page.route("**/api/archetypes/current", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ current: "financial_services" }),
    });
  });
}

test("transfer comparison card shows on Performance after transfer status", async ({ page }) => {
  await mockTransferStatus(page);
  await openPerformanceTab(page);
  await expect(page.getByRole("heading", { name: "Transfer Impact" })).toBeVisible();
});

test("transfer comparison card shows baseline vs post-transfer", async ({ page }) => {
  await mockTransferStatus(page);
  await openPerformanceTab(page);
  await expectAnyText(page, [/Before transfer/i, /After transfer/i, /Estimated calibration saved/i]);
});

test("archetype comparison card shows on Dashboard", async ({ page }) => {
  await mockArchetypeCurrent(page);
  await openDashboard(page);
  await expect(page.getByRole("heading", { name: "Archetype Advantage" })).toBeVisible();
});

test("archetype comparison shows generic vs selected", async ({ page }) => {
  await mockArchetypeCurrent(page);
  await openDashboard(page);
  await expectAnyText(page, [/Generic start/i, /Archetype start/i, /Estimated head start/i]);
});

test("first-run suggestion hidden when decisions exist", async ({ page }) => {
  await openDashboard(page);
  await expect(page.getByRole("heading", { name: "Get started faster" })).not.toBeVisible();
});

test("first-run suggestion browse button hidden when decisions exist", async ({ page }) => {
  await openDashboard(page);
  await expect(page.getByRole("button", { name: "Browse Industry Templates" })).not.toBeVisible();
});
