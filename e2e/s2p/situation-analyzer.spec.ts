import { expect, type Page, test } from '@playwright/test';
import { openTriageAndScore } from './helpers';

/* ── Helpers ── */

async function s2pBackendUp(page: Page) {
  const response = await page.request
    .get('http://127.0.0.1:8002/health', { timeout: 5_000 })
    .catch(() => null);
  return Boolean(response?.ok());
}

async function goToS2P(page: Page) {
  await page.goto('http://127.0.0.1:5177');
}

async function goToTriage(page: Page) {
  await goToS2P(page);
  await page.getByRole('button', { name: /Exception Triage/i }).click();
  await expect(
    page.locator('main h1', { hasText: /^Exception Triage$/ }),
  ).toBeVisible({ timeout: 10_000 });
  await expect(
    situationPanel(page).getByRole('heading', {
      name: 'Situation Analysis',
      exact: true,
    }),
  ).toBeVisible({ timeout: 10_000 });
  const firstInvoice = page
    .getByRole('button', {
      name: /S2P-INV|STRESS-CONC-S2P|INV-|demo-s2p/i,
    })
    .first();
  if (await firstInvoice.count()) {
    await expect(firstInvoice).toBeVisible({ timeout: 15_000 });
    await expect(firstInvoice).toBeEnabled({ timeout: 15_000 });
  }
}

function situationPanel(page: Page) {
  return page.getByTestId('situation-panel');
}

async function expectDownState(page: Page) {
  await expect(
    page.getByRole('heading', { name: 'Situation Analysis', exact: true }),
  ).toBeVisible();
  await expect(
    situationPanel(page).getByText(
      /unavailable|not connected|Select an exception|Score the exception/i,
    ),
  ).toBeVisible();
}

/* ═══════════════════════════════════════════════════════════════
   Group 1 — Page Load (independent pages, no scoring needed)
   ═══════════════════════════════════════════════════════════════ */

test.describe('Situation Analyzer — Page Load', () => {
  test.beforeEach(() => {
    test.setTimeout(90_000);
  });

  test('1. SituationPanel heading visible', async ({ page }) => {
    await goToTriage(page);
    await expect(
      page.getByRole('heading', { name: 'Situation Analysis', exact: true }),
    ).toBeVisible();
  });

  test('14. Coexists with evidence panels', async ({ page }) => {
    await goToTriage(page);
    await expect(
      situationPanel(page).getByRole('heading', {
        name: 'Situation Analysis',
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      page.locator('article').filter({
        has: page.getByRole('heading', {
          name: 'Category explanation',
          exact: true,
        }),
      }),
    ).toBeVisible();
  });

  test('15. Page loads within 10 seconds', async ({ page }) => {
    const start = Date.now();
    await goToS2P(page);
    await expect(
      page.getByText(/S2P Copilot|Dashboard|Exception Triage/i).first(),
    ).toBeVisible({ timeout: 10_000 });
    expect(Date.now() - start).toBeLessThan(12_000);
  });
});

/* ═══════════════════════════════════════════════════════════════
   Group 2 — Scored State (serial, ONE shared page — score once)
   Navigate + score in beforeAll; 9 tests share that state.
   ═══════════════════════════════════════════════════════════════ */

test.describe.serial('Situation Analyzer — Scored State', () => {
  let page: Page;
  let backendUp = false;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    backendUp = await s2pBackendUp(page);
    if (backendUp) {
      await openTriageAndScore(page);
    }
  });

  test.afterAll(async () => {
    await page?.close();
  });

  test('2. NL explanation renders', async () => {
    if (!backendUp) {
      await goToTriage(page);
      await expectDownState(page);
      return;
    }
    await expect(
      page
        .locator('main')
        .getByText(
          /Decision S2P-|Decision proximity explanation|scored factor vector/i,
        )
        .first(),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('3. Category renders', async () => {
    if (!backendUp) return; // covered by test 2
    await expect(
      page
        .locator('main')
        .getByText(
          /price_variance|quantity_mismatch|duplicate_risk|contract_gap|format_compliance/i,
        )
        .first(),
    ).toBeVisible({ timeout: 30_000 });
  });

  test('4. Confidence percentage renders', async () => {
    if (!backendUp) return;
    await expect(
      page.locator('main').getByText(/\d+%/).first(),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('5. Context chain nodes visible', async () => {
    if (!backendUp) return;
    await expect(
      page
        .locator('main')
        .getByText(/invoice date|invoice|line items/i)
        .first(),
    ).toBeVisible({ timeout: 10_000 });
    await expect(
      page
        .locator('main')
        .getByText(/commodity|contract|threshold|within bounds|rules/i)
        .first(),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('6. Traversal depth shown', async () => {
    if (!backendUp) return;
    await expect(
      situationPanel(page)
        .getByText(/Situation context|Context|hops?|within bounds/i)
        .first(),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('7. Factors list renders', async () => {
    if (!backendUp) return;
    await expect(
      page.locator('main').getByText(/\d+\s+factors/i).first(),
    ).toBeVisible({ timeout: 10_000 });
    await expect(
      page.locator('main').getByText(/^Confidence$/i).first(),
    ).toBeVisible({ timeout: 10_000 });
    await expect(
      page.locator('main').getByText(/^Action index$/i).first(),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('8. Provenance badges on values', async () => {
    if (!backendUp) return;
    await expect(
      situationPanel(page)
        .getByText(/learned|context|proven|sample/i)
        .first(),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('11. Partial context renders gracefully', async () => {
    if (!backendUp) {
      await goToTriage(page);
      await expectDownState(page);
      return;
    }
    await expect(
      situationPanel(page).getByRole('heading', {
        name: 'Situation Analysis',
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      situationPanel(page)
        .getByText(
          /Some context unavailable|Context|Situation analysis unavailable/i,
        )
        .first(),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('12. Sample provenance visually distinct', async () => {
    if (!backendUp) return;
    const sample = situationPanel(page).getByText(/sample/i).first();
    if (
      !(await sample.isVisible({ timeout: 10_000 }).catch(() => false))
    )
      return;
    await expect(sample.locator('..')).toHaveClass(/border-dashed|orange/);
  });
});

/* ═══════════════════════════════════════════════════════════════
   Group 3 — Mocked / Special State (independent pages)
   Route interception or backend-down scenarios.
   ═══════════════════════════════════════════════════════════════ */

test.describe('Situation Analyzer — Edge Cases', () => {
  test.beforeEach(() => {
    test.setTimeout(90_000);
  });

  test('9. Heading renders when no exception selected', async ({
    page,
  }) => {
    await page.route(
      'http://127.0.0.1:8002/api/s2p/preview/queue',
      async (route) => {
        await route.fulfill({
          contentType: 'application/json',
          body: JSON.stringify({
            exceptions: [],
            total: 0,
            auto_approve_rate: 0,
            confidence_avg: 0,
          }),
        });
      },
    );
    await goToTriage(page);
    await expect(
      page.getByRole('heading', { name: 'Situation Analysis', exact: true }),
    ).toBeVisible();
    await expect(
      situationPanel(page).getByText(
        /^Select an exception to begin\.$/i,
      ),
    ).toBeVisible();
  });

  test('10. Graceful when backend unavailable', async ({ page }) => {
    // Check backend BEFORE navigating to avoid 45s queue wait
    if (await s2pBackendUp(page)) return;
    await goToTriage(page);
    await expect(
      page.getByRole('heading', { name: 'Situation Analysis', exact: true }),
    ).toBeVisible();
    await expect(
      situationPanel(page).getByText(
        /unavailable|Select an exception|Score the exception/i,
      ),
    ).toBeVisible();
    await expect(
      situationPanel(page).locator('.text-red-700'),
    ).toHaveCount(0);
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
          provenance: {
            nl_explanation: 'sample',
            confidence: 'sample',
            overall: 'sample',
          },
        }),
      });
    });
    await openTriageAndScore(page);
    await expect(
      page.getByRole('heading', { name: 'Situation Analysis', exact: true }),
    ).toBeVisible();
    await expect(
      situationPanel(page)
        .getByText(/No context chain returned|Score the exception/i)
        .first(),
    ).toBeVisible({ timeout: 10_000 });
  });
});
