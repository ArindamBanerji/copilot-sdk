import { test, expect } from '../fixtures/copilot-fixture';
import { clickTab, waitForScreenReady } from '../helpers/ui';

/**
 * Trading copilot screenshots — for RGI Trading demo embedding
 *
 * Two dashboard states:
 *   1. Healthy (IKS 70+) — strategies performing, conservation GREEN
 *   2. Degraded (IKS 40-50) — visible decay, amber/red accuracy
 *
 * Strategy names matching demo D1:
 *   RSI+MACD, volume-breakout, gap-fill mean-rev, momentum cont., breakout-pullback
 *
 * Run:
 *   cd $env:CLAUDE_SDK
 *   npx playwright test e2e/trading/capture-trading-screens.spec.ts --project=trading
 *
 * Prerequisites:
 *   - demo.py running (Trading backend on 8010, frontend on 5174)
 *   - preseed_all_copilots.py done (80 decisions seeded)
 *
 * Output: screenshots/trading/
 */

const BASE = 'http://localhost:5174';
const API  = 'http://localhost:8010';
const DIR  = 'screenshots/trading';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Wait for health endpoint to report a real phase + alpha */
async function waitForBackend(page: import('@playwright/test').Page) {
  await page.waitForFunction(async () => {
    try {
      const r = await fetch('http://localhost:8010/api/health');
      const d = await r.json();
      return d && d.phase !== undefined && d.alpha !== undefined;
    } catch { return false; }
  }, { timeout: 15_000 });
}

/** Scroll to an element matched by any of the given selectors, screenshot it */
async function captureComponent(
  page: import('@playwright/test').Page,
  selectors: string[],
  path: string,
  timeout = 3000
) {
  for (const sel of selectors) {
    const el = page.locator(sel).first();
    if (await el.isVisible({ timeout }).catch(() => false)) {
      await el.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await el.screenshot({ path });
      return true;
    }
  }
  return false;
}

// ---------------------------------------------------------------------------
// Screenshot 1 — Healthy dashboard (IKS 70+)
// ---------------------------------------------------------------------------

test.describe('Trading copilot — healthy state screenshots', () => {

  test('Dashboard — healthy (IKS 70+, conservation GREEN)', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await waitForScreenReady(page);
    await waitForBackend(page);
    await clickTab(page, 'Dashboard');
    await page.waitForTimeout(2500);

    // Full dashboard
    await page.screenshot({ path: `${DIR}/dashboard-healthy-full.png`, fullPage: true });

    // IKS / conservation projection
    await captureComponent(page, [
      '[class*="Conservation"], [data-testid="conservation-projection"]',
      '[class*="conservation"]',
    ], `${DIR}/dashboard-healthy-conservation.png`);

    // Accuracy by category (strategy names)
    await captureComponent(page, [
      '[class*="AccuracyByCategory"], [data-testid="accuracy-by-category"]',
      '[class*="accuracy"]',
      '[class*="CategoryAccuracy"]',
    ], `${DIR}/dashboard-healthy-accuracy.png`);

    // Decision Explorer
    await captureComponent(page, [
      '[class*="DecisionExplorer"], [data-testid="decision-explorer"]',
      '[class*="decision-explorer"]',
    ], `${DIR}/dashboard-healthy-decisions.png`);

    // Rule Genealogy / Rule Lifecycle
    await captureComponent(page, [
      '[class*="RuleGenealogy"], [data-testid="rule-genealogy"]',
      '[class*="rule-genealogy"]',
      '[class*="RuleLifecycle"]',
    ], `${DIR}/dashboard-healthy-rules.png`);
  });

  test('Log Trade — score + reasoning panel', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await waitForScreenReady(page);
    await clickTab(page, 'Log Trade');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${DIR}/log-trade-full.png`, fullPage: true });

    // Score result card
    await captureComponent(page, [
      '[class*="ScoreResult"], [data-testid="score-result"]',
    ], `${DIR}/log-trade-score-card.png`);

    // Reasoning panel (SC-9)
    await captureComponent(page, [
      '[class*="Reasoning"], [data-testid="reasoning-panel"]',
    ], `${DIR}/log-trade-reasoning.png`);
  });

  test('Analysis — fingerprint + contrast', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await waitForScreenReady(page);
    await clickTab(page, 'Analysis');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${DIR}/analysis-full.png`, fullPage: true });

    // Fingerprint panel — shows per-factor weights
    await captureComponent(page, [
      '[class*="Fingerprint"], [data-testid="fingerprint-panel"]',
    ], `${DIR}/analysis-fingerprint.png`);

    // Contrast card
    await captureComponent(page, [
      '[class*="Contrast"], [data-testid="contrast-card"]',
    ], `${DIR}/analysis-contrast.png`);
  });

  test('Performance — trajectory + conservation projection', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await waitForScreenReady(page);
    await clickTab(page, 'Performance');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${DIR}/performance-full.png`, fullPage: true });

    // Trajectory chart
    await captureComponent(page, [
      '[class*="Trajectory"], [data-testid="trajectory-chart"]',
    ], `${DIR}/performance-trajectory.png`);

    // Conservation projection (SC-10)
    await captureComponent(page, [
      '[class*="ConservationProjection"], [data-testid="conservation-projection"]',
    ], `${DIR}/performance-conservation-projection.png`);
  });
});

// ---------------------------------------------------------------------------
// Screenshot 2 — Degraded dashboard (IKS 40-50)
//
// Strategy: inject low-accuracy decisions via the score+confirm API
// to drag accuracy down before capturing. The seeded data from
// preseed_all_copilots.py gives IKS ~70. We add 40 deliberately
// wrong confirmations to pull it to ~40-50.
// ---------------------------------------------------------------------------

test.describe('Trading copilot — degraded state screenshots', () => {

  test('Inject degraded decisions then capture dashboard', async ({ page, request }) => {
    // ----- Phase 1: inject bad decisions to drag IKS down -----
    //
    // Score 60 trades with deliberately wrong learn outcomes.
    // Each wrong learn reduces accuracy → drops IKS.
    //
    // Categories: event_driven, income_strategy, scalp_intraday, trend_following
    // Factors (10): signal_alignment, market_regime, position_sizing, timing_quality,
    //   risk_reward_actual, emotional_indicator, signal_confidence,
    //   options_delta_exposure, options_iv_percentile, options_gamma_risk
    // Actions (4): indexed 0-3 (e.g. strong_entry, acceptable_entry, poor_execution, abstain)

    const categories = ['event_driven', 'income_strategy', 'scalp_intraday', 'trend_following'];
    const factorNames = [
      'signal_alignment', 'market_regime', 'position_sizing', 'timing_quality',
      'risk_reward_actual', 'emotional_indicator', 'signal_confidence',
      'options_delta_exposure', 'options_iv_percentile', 'options_gamma_risk'
    ];

    const badDecisions = 60;
    let injected = 0;

    for (let i = 0; i < badDecisions; i++) {
      try {
        // Build random factors as a named dict
        const factors: Record<string, number> = {};
        for (const fn of factorNames) {
          factors[fn] = 0.2 + Math.random() * 0.6;
        }

        // Score — spread across all 4 categories
        const category = categories[i % categories.length];

        const scoreResp = await request.post(`${API}/api/score`, {
          data: { category, factors },
        });

        if (!scoreResp.ok()) {
          console.log(`Score failed (${scoreResp.status()}): ${await scoreResp.text()}`);
          continue;
        }
        const scoreData = await scoreResp.json();
        const predictedAction: string = scoreData.action;
        const decisionId: string = scoreData.decision_id;

        // Learn with wrong action — pick a different action name.
        // Swap the predicted action to something clearly wrong.
        const wrongActions: Record<string, string> = {
          'strong_entry': 'poor_execution',
          'acceptable_entry': 'poor_execution',
          'poor_execution': 'strong_entry',
          'abstain': 'strong_entry',
        };
        const wrongAction = wrongActions[predictedAction] || 'poor_execution';

        const learnResp = await request.post(`${API}/api/learn`, {
          data: {
            decision_id: decisionId,
            actual_action: wrongAction,
            outcome: 'confirmed',
          },
        });

        if (!learnResp.ok()) {
          console.log(`Learn failed (${learnResp.status()}): ${await learnResp.text()}`);
          continue;
        }

        injected++;
      } catch (e) {
        console.log(`Injection error at ${i}: ${e}`);
      }
    }

    console.log(`Injected ${injected}/${badDecisions} degraded decisions`);

    // ----- Phase 2: capture degraded dashboard -----
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await waitForScreenReady(page);
    await waitForBackend(page);
    await clickTab(page, 'Dashboard');
    await page.waitForTimeout(3000);  // extra time for state refresh

    // Full degraded dashboard
    await page.screenshot({ path: `${DIR}/dashboard-degraded-full.png`, fullPage: true });

    // Conservation — should show AMBER or RED
    await captureComponent(page, [
      '[class*="Conservation"], [data-testid="conservation-projection"]',
      '[class*="conservation"]',
    ], `${DIR}/dashboard-degraded-conservation.png`);

    // Accuracy by category — should show lower percentages, some amber/red
    await captureComponent(page, [
      '[class*="AccuracyByCategory"], [data-testid="accuracy-by-category"]',
      '[class*="accuracy"]',
      '[class*="CategoryAccuracy"]',
    ], `${DIR}/dashboard-degraded-accuracy.png`);

    // Decision Explorer — should show wrong decisions
    await captureComponent(page, [
      '[class*="DecisionExplorer"], [data-testid="decision-explorer"]',
      '[class*="decision-explorer"]',
    ], `${DIR}/dashboard-degraded-decisions.png`);
  });
});
