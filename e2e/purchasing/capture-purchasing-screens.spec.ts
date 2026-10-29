import { test, expect } from '../fixtures/copilot-fixture';
import { clickTab, waitForScreenReady } from '../helpers/ui';

/**
 * Purchasing copilot screenshots — for Restaurant-RGI demo embedding
 *
 * Run:
 *   cd $env:CLAUDE_SDK
 *   npx playwright test e2e/purchasing/capture-purchasing-screens.spec.ts --project=purchasing
 *
 * Prerequisites: demo.py running, preseed_all_copilots.py done
 * Output: screenshots/purchasing/
 */

const BASE = 'http://localhost:5175';
const DIR = 'screenshots/purchasing';

test.describe('Purchasing copilot screenshots', () => {

  test('Order screen — score + reasoning', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await waitForScreenReady(page);
    await clickTab(page, 'Order');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${DIR}/order-full.png`, fullPage: true });

    const scoreCard = page.locator('[class*="ScoreResult"], [data-testid="score-result"]').first();
    if (await scoreCard.isVisible({ timeout: 3000 }).catch(() => false)) {
      await scoreCard.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await scoreCard.screenshot({ path: `${DIR}/order-score-card.png` });
    }

    const reasoning = page.locator('[class*="Reasoning"], [data-testid="reasoning-panel"]').first();
    if (await reasoning.isVisible({ timeout: 3000 }).catch(() => false)) {
      await reasoning.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await reasoning.screenshot({ path: `${DIR}/order-reasoning.png` });
    }
  });

  test('Dashboard — conservation + IKS', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await waitForScreenReady(page);
    await clickTab(page, 'Dashboard');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${DIR}/dashboard-full.png`, fullPage: true });

    const conservation = page.locator('[class*="Conservation"], [data-testid="conservation-projection"]').first();
    if (await conservation.isVisible({ timeout: 3000 }).catch(() => false)) {
      await conservation.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await conservation.screenshot({ path: `${DIR}/dashboard-conservation.png` });
    }
  });

  test('Performance — trajectory + compounding', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await waitForScreenReady(page);
    await clickTab(page, 'Performance');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${DIR}/performance-full.png`, fullPage: true });

    const trajectory = page.locator('[class*="Trajectory"], [data-testid="trajectory-chart"]').first();
    if (await trajectory.isVisible({ timeout: 3000 }).catch(() => false)) {
      await trajectory.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await trajectory.screenshot({ path: `${DIR}/performance-trajectory.png` });
    }
  });

  test('Analysis — fingerprint + contrast', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await waitForScreenReady(page);
    await clickTab(page, 'Analysis');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${DIR}/analysis-full.png`, fullPage: true });

    const fingerprint = page.locator('[class*="Fingerprint"], [data-testid="fingerprint-panel"]').first();
    if (await fingerprint.isVisible({ timeout: 3000 }).catch(() => false)) {
      await fingerprint.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await fingerprint.screenshot({ path: `${DIR}/analysis-fingerprint.png` });
    }
  });

  test('Inventory — category view', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await waitForScreenReady(page);
    await clickTab(page, 'Inventory');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${DIR}/inventory-full.png`, fullPage: true });
  });

});
