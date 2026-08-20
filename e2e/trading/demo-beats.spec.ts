import { expect, test } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

async function openTab(page: import("@playwright/test").Page, tab: string) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, tab);
  await waitForAppShell(page);
}

test("TF-01: regime mirror renders per-regime accuracy", async ({ page }) => {
  await openTab(page, "Analysis");
  await expect(page.getByTestId("regime-mirror-panel")).toBeVisible();
});

test("TF-02: situational abstention banner renders", async ({ page }) => {
  await openTab(page, "Log Trade");
  await expect(page.getByTestId("situational-abstention-banner")).toBeVisible();
});

test("TF-03: autonomy throttle renders conservation state", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("autonomy-throttle-panel")).toBeVisible();
});

test("TF-04: regime rejection panel renders", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("regime-rejection-panel")).toBeVisible();
});

test("TF-05: clustering-adjusted Sharpe renders", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("vol-short-panel")).toBeVisible();
});

test("TF-06: VRP panel renders", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("vrp-panel")).toBeVisible();
});

test("TF-07: rich-cheap panel renders", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("rich-cheap-panel")).toBeVisible();
});

test("TF-08: dispersion panel renders", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("dispersion-panel")).toBeVisible();
});

test("TF-09: tail bets panel renders", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("tail-bets-panel")).toBeVisible();
});

test("TF-10: claim gate badge renders on Analysis", async ({ page }) => {
  await openTab(page, "Analysis");
  await expect(page.getByTestId("claim-gate-badge")).toBeVisible();
});

test("TF-11: certificate panel renders", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("certificate-panel")).toBeVisible();
});

test("TF-12: gate dividend panel renders", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("gate-dividend-panel")).toBeVisible();
});

test("TF-13: rejection moment table renders counts", async ({ page }) => {
  await openTab(page, "Performance");
  const table = page.getByTestId("rejection-moment-table");
  await expect(table).toBeVisible();
  await expect(table).toContainText(/Tested|Promoted|Rejected/i);
});
