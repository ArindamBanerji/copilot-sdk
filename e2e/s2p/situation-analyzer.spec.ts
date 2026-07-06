import { expect, type Page, test } from '@playwright/test';

async function s2pBackendUp(page: Page) {
  const response = await page.request.get('http://127.0.0.1:8002/health', { timeout: 5_000 }).catch(() => null);
  return Boolean(response?.ok());
}

async function goToS2P(page: Page) {
  await page.goto('http://localhost:5177');
}

async function goToTriage(page: Page) {
  await goToS2P(page);
  await page.getByRole('button', { name: /Exception Triage/i }).click();
  await expect(page.locator('main h1', { hasText: /^Exception Triage$/ })).toBeVisible({ timeout: 10_000 });
  await expect(situationPanel(page).getByRole('heading', { name: 'Situation Analysis', exact: true })).toBeVisible({ timeout: 10_000 });
}

async function scoreSelected(page: Page) {
  const score = page.getByRole('button', { name: /^Score$/i });
  if (await score.isEnabled().catch(() => false)) {
    await score.click();
  }
}

function situationPanel(page: Page) {
  return page.getByTestId('situation-panel');
}

async function expectDownState(page: Page) {
  await expect(page.getByText('Situation Analysis')).toBeVisible();
  await expect(situationPanel(page).getByText(/unavailable|not connected|Select an exception|Score the exception/i)).toBeVisible();
}

test('1. SituationPanel heading visible', async ({ page }) => {
  await goToTriage(page);
  await expect(page.getByText('Situation Analysis')).toBeVisible();
});

test('2. NL explanation renders', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(situationPanel(page).getByText(/price|Contract|Confidence|->/i)).toBeVisible({ timeout: 10_000 });
});

test('3. Category renders', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(situationPanel(page).getByText(/price variance|quantity mismatch|duplicate risk|contract gap|format compliance/i)).toBeVisible({ timeout: 10_000 });
});

test('4. Confidence percentage renders', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(situationPanel(page).getByText(/\d+%/).first()).toBeVisible({ timeout: 10_000 });
});

test('5. Context chain nodes visible', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(situationPanel(page).getByText(/invoice/i).first()).toBeVisible({ timeout: 10_000 });
  await expect(situationPanel(page).getByText(/commodity|purchase order|similar invoice|contract|rules|threshold/i).first()).toBeVisible({ timeout: 10_000 });
});

test('6. Traversal depth shown', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(situationPanel(page).getByText(/\d+ hops?/i)).toBeVisible({ timeout: 10_000 });
});

test('7. Factors list renders', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(situationPanel(page).getByText(/amount variance ratio|match status|duplicate score|commodity index correlation/i)).toBeVisible({ timeout: 10_000 });
});

test('8. Provenance badges on values', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(situationPanel(page).getByText(/learned|context|proven|sample/i).first()).toBeVisible({ timeout: 10_000 });
});

test('9. Heading renders when no exception selected', async ({ page }) => {
  await page.route('http://127.0.0.1:8002/api/s2p/preview/queue', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ exceptions: [], total: 0, auto_approve_rate: 0, confidence_avg: 0 }),
    });
  });
  await goToTriage(page);
  await expect(page.getByText('Situation Analysis')).toBeVisible();
  await expect(situationPanel(page).getByText(/Select an exception/i)).toBeVisible();
});

test('10. Graceful when backend unavailable', async ({ page }) => {
  await goToTriage(page);
  if (await s2pBackendUp(page)) return;
  await expect(page.getByText('Situation Analysis')).toBeVisible();
  await expect(situationPanel(page).getByText(/unavailable|Select an exception|Score the exception/i)).toBeVisible();
  await expect(situationPanel(page).locator('.text-red-700')).toHaveCount(0);
});

test('11. Partial context renders gracefully', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(situationPanel(page).getByRole('heading', { name: 'Situation Analysis', exact: true })).toBeVisible();
  await expect(situationPanel(page).getByText(/Some context unavailable|Context|Situation analysis unavailable/i).first()).toBeVisible({ timeout: 10_000 });
});

test('12. Sample provenance visually distinct', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  const sample = situationPanel(page).getByText(/sample/i).first();
  if (!(await sample.isVisible({ timeout: 10_000 }).catch(() => false))) return;
  await expect(sample.locator('..')).toHaveClass(/border-dashed|orange/);
});

test('13. No crash on empty context', async ({ page }) => {
  const up = await s2pBackendUp(page);
  if (!up) {
    await goToTriage(page);
    await expectDownState(page);
    return;
  }
  await page.route(/\/api\/s2p\/situation\/.+/, async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        decision_id: 'empty',
        category: 'price_variance',
        context_chain: [],
        nl_explanation: 'No context available.',
        confidence: 0.5,
        factors_used: [],
        traversal_depth: 0,
        context_available: false,
        warnings: [],
        missing_variables: [],
        provenance: { nl_explanation: 'sample', confidence: 'sample', overall: 'sample' },
      }),
    });
  });
  await goToTriage(page);
  await scoreSelected(page);
  await expect(page.getByText('Situation Analysis')).toBeVisible();
  await expect(situationPanel(page).getByText(/No context chain returned/i)).toBeVisible({ timeout: 10_000 });
});

test('14. Coexists with evidence panels', async ({ page }) => {
  await goToTriage(page);
  await expect(situationPanel(page).getByRole('heading', { name: 'Situation Analysis', exact: true })).toBeVisible();
  await expect(
    page.locator('article').filter({
      has: page.getByRole('heading', { name: 'Category explanation', exact: true }),
    })
  ).toBeVisible();
});

test('15. Page loads within 10 seconds', async ({ page }) => {
  const start = Date.now();
  await goToS2P(page);
  await expect(page.getByText(/S2P Copilot|Dashboard|Exception Triage/i).first()).toBeVisible({ timeout: 10_000 });
  expect(Date.now() - start).toBeLessThan(10_000);
});
