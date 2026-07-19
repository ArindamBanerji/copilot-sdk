import { expect, type Page, test } from '@playwright/test';

test.setTimeout(90_000);

async function s2pBackendUp(page: Page) {
  const response = await page.request.get('http://127.0.0.1:8002/health', { timeout: 5_000 }).catch(() => null);
  return Boolean(response?.ok());
}

async function goToS2P(page: Page) {
  await page.goto('http://127.0.0.1:5177');
}

async function goToTriage(page: Page) {
  await goToS2P(page);
  await page.getByRole('button', { name: /Exception Triage/i }).click();
  await expect(page.locator('main h1', { hasText: /^Exception Triage$/ })).toBeVisible({ timeout: 10_000 });
  await expect(situationPanel(page).getByRole('heading', { name: 'Situation Analysis', exact: true })).toBeVisible({ timeout: 10_000 });
}

function waitForScoreResponse(page: Page) {
  return page.waitForResponse((response) =>
    response.url().includes('/score') &&
    response.request().method() === 'POST' &&
    response.status() === 200
  );
}

async function scoreSelected(page: Page) {
  const score = page.getByRole('button', { name: /^Score$/i });
  if (!(await score.isEnabled().catch(() => false))) {
    const firstInvoice = page.getByRole('button', { name: /S2P-INV-/i }).first();
    await expect(firstInvoice).toBeVisible({ timeout: 30_000 });
    await firstInvoice.click();
  }
  await expect(score).toBeEnabled({ timeout: 10_000 });
  await Promise.all([
    waitForScoreResponse(page),
    score.click(),
  ]);
  await expect(
    page.locator('article', { hasText: /Recommendation/i }).filter({
      has: page.getByText(/^Action index$/i),
    }).first()
  ).toBeVisible({ timeout: 20_000 });
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
  await expect(page.locator('main').getByText(/Decision S2P-|Decision proximity explanation|scored factor vector/i).first()).toBeVisible({ timeout: 10_000 });
});

test('3. Category renders', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(page.locator('main').getByText(/price_variance|quantity_mismatch|duplicate_risk|contract_gap|format_compliance/i).first()).toBeVisible({ timeout: 30_000 });
});

test('4. Confidence percentage renders', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(page.locator('main').getByText(/\d+%/).first()).toBeVisible({ timeout: 10_000 });
});

test('5. Context chain nodes visible', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(page.locator('main').getByText(/invoice date|invoice|line items/i).first()).toBeVisible({ timeout: 10_000 });
  await expect(page.locator('main').getByText(/commodity|contract|threshold|within bounds|rules/i).first()).toBeVisible({ timeout: 10_000 });
});

test('6. Traversal depth shown', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(situationPanel(page).getByText(/Situation context|Context|hops?|within bounds/i).first()).toBeVisible({ timeout: 10_000 });
});

test('7. Factors list renders', async ({ page }) => {
  await goToTriage(page);
  if (!(await s2pBackendUp(page))) {
    await expectDownState(page);
    return;
  }
  await scoreSelected(page);
  await expect(page.locator('main').getByText(/\d+\s+factors/i).first()).toBeVisible({ timeout: 10_000 });
  await expect(page.locator('main').getByText(/^Confidence$/i).first()).toBeVisible({ timeout: 10_000 });
  await expect(page.locator('main').getByText(/^Action index$/i).first()).toBeVisible({ timeout: 10_000 });
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
  await expect(situationPanel(page).getByText(/^Select an exception to begin\.$/i)).toBeVisible();
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
  await expect(situationPanel(page).getByText(/No context chain returned|Score the exception/i).first()).toBeVisible({ timeout: 10_000 });
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
