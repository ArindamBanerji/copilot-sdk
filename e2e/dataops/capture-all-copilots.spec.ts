import { test, expect } from '../fixtures/copilot-fixture';
import { clickTab, waitForScreenReady } from '../helpers/ui';

test('capture dataops - Intelligence Map', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://localhost:5176', { waitUntil: 'networkidle' });
  await waitForScreenReady(page);

  // Navigate to Insight tab
  await clickTab(page, 'Insight');
  await page.waitForTimeout(2000);

  // Wait for intelligence map to be ready
  await page.locator('[data-testid="intelligence-map"][data-screen-ready="true"]')
    .waitFor({ timeout: 20_000 });

  // Scroll the intelligence map into view
  const map = page.getByTestId('intelligence-map').last();
  await map.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1000);

  // Capture just the intelligence map panel
  await map.screenshot({ path: 'screenshots/dataops-intelligence-map.png' });
});

test('capture dataops - Insight full page', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://localhost:5176', { waitUntil: 'networkidle' });
  await waitForScreenReady(page);

  await clickTab(page, 'Insight');
  await page.locator('[data-testid="intelligence-map"][data-screen-ready="true"]')
    .waitFor({ timeout: 20_000 });
  await page.waitForTimeout(2000);

  // Full page capture
  await page.screenshot({ path: 'screenshots/dataops-insight-full.png', fullPage: true });
});

test('capture dataops - Dashboard enterprise health', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://localhost:5176', { waitUntil: 'networkidle' });
  await waitForScreenReady(page);

  await clickTab(page, 'Dashboard');
  await page.waitForTimeout(2000);

  // Enterprise health card
  const ehCard = page.getByTestId('enterprise-value-card');
  await expect(ehCard).toBeVisible();
  await ehCard.scrollIntoViewIfNeeded();
  await page.waitForTimeout(500);
  await ehCard.screenshot({ path: 'screenshots/dataops-enterprise-health.png' });

  // Full dashboard
  await page.screenshot({ path: 'screenshots/dataops-dashboard-full.png', fullPage: true });
});
