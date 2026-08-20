import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForScreenReady } from "../helpers/ui";

async function gotoInsight(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Insight");
  await waitForScreenReady(page);
}

async function gotoDashboard(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
}

test("DF-01: FusionClimaxPanel renders cross-graph result", async ({ page }) => {
  await gotoInsight(page);
  const panel = page.getByTestId("fusion-climax-panel");
  await expect(panel).toBeVisible();
  await expect(panel.getByTestId("fusion-source-summary")).toBeVisible({ timeout: 20_000 });
  await expect(panel.getByTestId("fusion-cross-graph-result")).toBeVisible();
});

test("DF-02: FusionClimaxPanel shows monthly resolution value", async ({ page }) => {
  await gotoInsight(page);
  const panel = page.getByTestId("fusion-climax-panel");
  await expect(panel.getByTestId("fusion-monthly-impact")).toBeVisible({ timeout: 20_000 });
  await expect(panel.getByTestId("fusion-monthly-impact")).toContainText(/\$[\d,]+|pending/i);
  await expect(panel.getByTestId("fusion-apply-fix")).toBeVisible();
});

test("DF-03: DIWiringPanel navigates TrustCard to Products to Map", async ({ page }) => {
  await gotoDashboard(page);
  const wiring = page.getByTestId("di-wiring-panel");
  await expect(wiring).toBeVisible();
  await expect(wiring.getByTestId("trust-card")).toBeVisible();
  await wiring.getByRole("link", { name: /2 · Products/ }).click();
  await expect(wiring.getByTestId("products-card")).toBeVisible();
  await wiring.getByRole("link", { name: /3 · Intelligence Map/ }).click();
  await expect(wiring.getByTestId("intelligence-map")).toBeVisible();
});

test("DF-04: CompoundingCurveOverlay shows governed and frozen arms", async ({ page }) => {
  await gotoDashboard(page);
  const panel = page.getByTestId("compounding-curve-overlay");
  await expect(panel).toBeVisible();
  await expect(panel.getByTestId("compounding-curve-chart")).toBeVisible();
  await expect(panel.getByTestId("compounding-governed-arm")).toHaveAttribute("d", /.+/);
  await expect(panel.getByTestId("compounding-frozen-arm")).toHaveAttribute("d", /.+/);
  await expect(panel.getByTestId("compounding-curve-legend")).toContainText(/Governed arm|Frozen baseline/);
});

test("DF-05: CompoundingCurveOverlay governed arm rises", async ({ page }) => {
  await gotoDashboard(page);
  const panel = page.getByTestId("compounding-curve-overlay");
  await expect(panel.getByTestId("compounding-curve-narrative")).toContainText(/lifting|instrumented/i);
  await expect(panel.locator("[data-governed-rising]")).toHaveAttribute("data-governed-rising", "true");
});

test("DF-06: Dashboard to Insight preserves fusion and compounding flow", async ({ page }) => {
  await gotoDashboard(page);
  await expect(page.getByTestId("di-wiring-panel")).toBeVisible();
  await clickTab(page, "Insight");
  await waitForScreenReady(page);
  await expect(page.getByTestId("fusion-climax-panel")).toBeVisible();
  await expect(page.getByTestId("compounding-curve-overlay")).toBeVisible();
});
