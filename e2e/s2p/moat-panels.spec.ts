import { expect, test, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function openS2PTab(page: Page, tab: string) {
  await page.goto("/");
  await clickTab(page, tab);
}

test("SM-01 S14-CONTRAST renders the rule-vs-reasoning surface", async ({ page }) => {
  await openS2PTab(page, "Exception Triage");
  await expect(page.getByTestId("rule-vs-reasoning-panel")).toBeVisible();
});

test("SM-02 S2P-EXTINCT renders lifecycle stages", async ({ page }) => {
  await openS2PTab(page, "Evidence");
  const panel = page.getByTestId("exception-extinction-timeline");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(/DISCOVERED|SHADOWING|PROMOTED/);
});

test("SM-03 S2P-TWIN renders the modeled baseline label", async ({ page }) => {
  await openS2PTab(page, "Performance");
  await expect(page.getByTestId("frozen-twin-comparison-panel")).toBeVisible();
  await expect(page.getByTestId("frozen-twin-modeled-label")).toContainText("MODELED");
});

test("SM-04 S2P-WHATIF renders the factor inspector", async ({ page }) => {
  await openS2PTab(page, "Insight");
  const panel = page.getByTestId("what-if-inspector-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(/What would change this decision/i);
});

test("SM-05 S2P-CONFIDENCE is visible on Performance", async ({ page }) => {
  await openS2PTab(page, "Performance");
  await expect(page.getByTestId("confidence-band-panel")).toBeVisible();
});

test("SM-06 S2P-DAY0 renders the honest readiness statement", async ({ page }) => {
  await openS2PTab(page, "Dashboard");
  const panel = page.getByTestId("day-zero-readiness-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(/truth about your data/i);
});

test("SM-07 lifecycle panel exposes an unavailable empty state honestly", async ({ page }) => {
  await openS2PTab(page, "Evidence");
  await expect(page.getByTestId("exception-extinction-timeline")).toContainText(/Promotion lifecycle|DISCOVERED|SHADOWING/i);
});

test("SM-08 twin panel distinguishes pilot target from measured evidence", async ({ page }) => {
  await openS2PTab(page, "Performance");
  await expect(page.getByTestId("frozen-twin-comparison-panel")).toContainText(/MODELED|Pending outcomes|Day-0 frozen/i);
});

test("SM-09 readiness panel shows provenance and trust dimensions", async ({ page }) => {
  await openS2PTab(page, "Dashboard");
  const panel = page.getByTestId("day-zero-readiness-panel");
  await expect(panel).toContainText(/Source coverage/i);
  await expect(panel).toContainText(/Provenance/i);
  await expect(panel).toContainText(/Trust tier/i);
});

test("SM-10 moat panels are reachable across the S2P flow", async ({ page }) => {
  await openS2PTab(page, "Dashboard");
  await expect(page.getByTestId("day-zero-readiness-panel")).toBeVisible();
  await clickTab(page, "Evidence");
  await expect(page.getByTestId("exception-extinction-timeline")).toBeVisible();
  await clickTab(page, "Performance");
  await expect(page.getByTestId("frozen-twin-comparison-panel")).toBeVisible();
  await expect(page.getByTestId("confidence-band-panel")).toBeVisible();
});
