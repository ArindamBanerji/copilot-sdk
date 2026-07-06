import { expect, type Page, test } from '@playwright/test';

async function goToS2P(page: Page) {
  await page.goto('http://localhost:5177');
  await expect(page.getByText(/S2P Copilot|Dashboard/i).first()).toBeVisible({ timeout: 10_000 });
}

async function openTab(page: Page, name: RegExp) {
  await goToS2P(page);
  await page.getByRole('button', { name }).click();
}

test('Dashboard tab renders', async ({ page }) => {
  await openTab(page, /Dashboard/i);
  await expect(page.getByText(/Dashboard|exception queue|recommendations/i).first()).toBeVisible();
});

test('Exception Triage tab renders', async ({ page }) => {
  await openTab(page, /Exception Triage/i);
  await expect(page.locator('main h1', { hasText: /^Exception Triage$/ })).toBeVisible();
});

test('Insight tab renders', async ({ page }) => {
  await openTab(page, /Insight/i);
  await expect(page.locator('main h1', { hasText: /^Insight$/ })).toBeVisible();
});

test('Evidence tab renders', async ({ page }) => {
  await openTab(page, /Evidence/i);
  await expect(page.locator('main h1', { hasText: /^Evidence$/ })).toBeVisible();
});

test('Suppliers tab renders', async ({ page }) => {
  await openTab(page, /Suppliers/i);
  await expect(page.locator('main h1', { hasText: /^Suppliers$/ })).toBeVisible();
});

test('Performance tab renders', async ({ page }) => {
  await openTab(page, /Performance/i);
  await expect(page.locator('main h1', { hasText: /^Performance$/ })).toBeVisible();
});
