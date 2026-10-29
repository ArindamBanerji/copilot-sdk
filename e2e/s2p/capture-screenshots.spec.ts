/**
 * capture_s2p_screenshots_v1.ts
 *
 * Captures 4 screenshots from S2P copilot (port 5177) at 1440×900
 * for v21 live panels. Maps to story drivers SD1–SD4.
 *
 * Prerequisites:
 *   - S2P backend running on port 8002
 *   - S2P frontend running on port 5177
 *   - Data pre-seeded (demo.py handles this)
 *
 * Usage (from copilot-sdk/):
 *   npx playwright test e2e/s2p/capture-screenshots.spec.ts --project=s2p
 *
 * Output: screenshots/ directory with 4 PNG files
 */

import { test, expect } from '@playwright/test';

const S2P_URL = 'http://localhost:5177';
const SCREENSHOT_DIR = 'screenshots';

/** Click a tab by its visible text label */
async function clickTab(page: import('@playwright/test').Page, tabName: string) {
  // CopilotShell renders tabs as clickable elements with the tab name
  const tab = page.getByRole('tab', { name: tabName }).or(
    page.locator(`[role="tab"]:has-text("${tabName}")`)
  ).or(
    page.locator(`button:has-text("${tabName}"), a:has-text("${tabName}")`)
  );
  await tab.first().click();
}

/** Wait for screen data-ready and give panels time to render */
async function waitForScreenReady(page: import('@playwright/test').Page, timeout = 15000) {
  // Wait for data-screen-ready="true" (handles both static and dynamic)
  await page.waitForSelector('[data-screen-ready="true"]', { timeout });
  // Extra settle time for charts/panels to finish rendering
  await page.waitForTimeout(2000);
}

test.describe('S2P v21 Live Panel Screenshots', () => {

  test.use({
    viewport: { width: 1440, height: 900 },
  });

  test.beforeAll(async () => {
    // Verify S2P backend is up
    const res = await fetch('http://localhost:8002/api/health').catch(() => null);
    if (!res || !res.ok) {
      throw new Error('S2P backend not running on port 8002. Start with: demo.py');
    }
  });

  test('SD1: Performance — Earned Autonomy', async ({ page }) => {
    await page.goto(S2P_URL, { waitUntil: 'networkidle' });
    await clickTab(page, 'Performance');
    await waitForScreenReady(page);

    // Wait for conservation data to load (ConservationMiniGauge)
    await page.waitForSelector('[data-screen-ready="true"]', { timeout: 10000 });
    // Extra time for TrajectoryChart + ConservationMiniGauge + AuthorityPanel
    await page.waitForTimeout(1500);

    await page.screenshot({
      path: `${SCREENSHOT_DIR}/sd1_performance_earned_autonomy.png`,
      fullPage: false,
    });
  });

  test('SD2: Insight — Commodity Shock (8-factor fingerprint)', async ({ page }) => {
    await page.goto(S2P_URL, { waitUntil: 'networkidle' });
    await clickTab(page, 'Insight');
    await waitForScreenReady(page);

    // InsightScreen auto-selects first invoice via <select> dropdown.
    // FactorFingerprintPanel renders the 8-factor bar chart automatically.
    // Wait for the fingerprint panel to have content
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: `${SCREENSHOT_DIR}/sd2_insight_commodity_shock.png`,
      fullPage: false,
    });
  });

  test('SD3: Exception Triage — Touchless Rate', async ({ page }) => {
    await page.goto(S2P_URL, { waitUntil: 'networkidle' });
    await clickTab(page, 'Exception Triage');

    // TriageScreen uses DYNAMIC data-screen-ready={String(queueSettled)}
    // queueSettled = !loading && (queue !== null || queueError !== null)
    // Must wait for the attribute value to be exactly "true"
    await page.waitForSelector('[data-screen-ready="true"]', { timeout: 20000 });

    // Extra time for invoice list buttons + selected invoice panel to render
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: `${SCREENSHOT_DIR}/sd3_triage_touchless_rate.png`,
      fullPage: false,
    });
  });

  test('SD4: Evidence — Spend Governance', async ({ page }) => {
    await page.goto(S2P_URL, { waitUntil: 'networkidle' });
    await clickTab(page, 'Evidence');
    await waitForScreenReady(page);

    // EvidenceScreen auto-selects first invoice via <select> dropdown.
    // AuditTrailPanel, CompliancePanel, ComplianceScreeningPanel render automatically.
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: `${SCREENSHOT_DIR}/sd4_evidence_spend_governance.png`,
      fullPage: false,
    });
  });
});
