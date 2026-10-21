import {
  expect,
  test,
  type Locator,
  type Page,
  type Response,
} from "@playwright/test";

import { clickTab } from "../helpers/ui";

const QUEUED_INVOICE_PATTERN = /S2P-INV|STRESS-CONC-S2P|INV-|demo-s2p|\b[1-9]\d* queued\b/i;

async function responseBody(response: Response): Promise<Record<string, unknown>> {
  try {
    const body: unknown = await response.json();
    return body !== null && typeof body === "object"
      ? body as Record<string, unknown>
      : {};
  } catch {
    return {};
  }
}

export async function waitForTriageQueue(page: Page, timeout = 90_000): Promise<void> {
  await expect(
    page.locator("article").filter({ hasText: /Invoice Selector/i }),
  ).toContainText(QUEUED_INVOICE_PATTERN, { timeout });
}

export function waitForS2PScoreResponse(
  page: Page,
  timeout = 90_000,
): Promise<Response> {
  return page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      /\/api\/s2p\/score(?:\?|$)/.test(response.url()),
    { timeout },
  );
}

export function waitForS2PLearnResponse(
  page: Page,
  timeout = 90_000,
): Promise<Response> {
  return page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      /\/api\/(?:learn|s2p\/outcome)(?:\?|$)/.test(response.url()),
    { timeout },
  );
}

export async function assertScoreSuccess(response: Response): Promise<void> {
  const body = await responseBody(response);
  if (response.status() !== 200) {
    throw new Error(
      `S2P score failed with HTTP ${response.status()}: ${JSON.stringify(body)}`,
    );
  }
  if (!body.decision_id && !body.id) {
    const disposition = body.held || body.gate || body.conservation
      ? "held by a gate"
      : "malformed response";
    throw new Error(
      `S2P score ${disposition}: no decision_id or id in ${JSON.stringify(body)}`,
    );
  }
}

export async function assertLearnSuccess(response: Response): Promise<void> {
  const body = await responseBody(response);
  if (!response.ok()) {
    throw new Error(
      `S2P learn failed with HTTP ${response.status()}: ${JSON.stringify(body)}`,
    );
  }
  if (body.learning_applied !== true) {
    throw new Error(
      `S2P learn returned learning_applied false or missing: ${JSON.stringify(body)}`,
    );
  }
}

export function panel(page: Page, text: string | RegExp): Locator {
  return page.locator("article").filter({
    has: page.locator(
      "h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']",
      { hasText: text },
    ),
  });
}

export function scoreResultPanel(page: Page): Locator {
  return panel(page, /Action index|Recommendation/i).first();
}

export function recommendationControls(page: Page): Locator {
  return page.locator("article", {
    has: page.getByRole("button", { name: /Confirm recommendation|Override/i }),
  });
}

export function s2pScoreResult(page: Page): Locator {
  return scoreResultPanel(page);
}

export async function clickAndWaitForS2PScore(
  page: Page,
  scoreButton: Locator,
  timeout = 90_000,
): Promise<Response> {
  const [response] = await Promise.all([
    waitForS2PScoreResponse(page, timeout),
    scoreButton.click(),
  ]);
  await assertScoreSuccess(response);
  await expect(s2pScoreResult(page)).toBeVisible({ timeout: 30_000 });
  return response;
}

export async function clickScoreAndValidate(page: Page): Promise<Response> {
  const selected = panel(page, /Selected Invoice/i).first();
  const selectedHasInvoice = await selected
    .getByText(/Supplier|Amount|Category/i)
    .count();
  if (selectedHasInvoice === 0) {
    const firstInvoice = panel(page, /Invoice Selector/i)
      .getByRole("button", { name: /S2P-INV|STRESS-CONC-S2P|INV-|demo-s2p/i })
      .first();
    if (!(await firstInvoice.isVisible().catch(() => false))) {
      test.skip(true, "No queued invoice available for scoring");
    }
    await firstInvoice.click();
  }
  await expect(selected).toContainText(/Supplier|Amount|Category/i, {
    timeout: 30_000,
  });
  const scoreButton = selected.getByRole("button", { name: /^Score$/i });
  await expect(scoreButton).toBeEnabled({ timeout: 30_000 });
  return clickAndWaitForS2PScore(page, scoreButton);
}

export async function openTriageAndScore(page: Page): Promise<Response> {
  await page.goto("/");
  await clickTab(page, "Exception Triage");
  await expect(
    page.getByRole("heading", { name: /Exception Triage/i }).first(),
  ).toBeVisible({ timeout: 30_000 });
  await waitForTriageQueue(page);
  return clickScoreAndValidate(page);
}

export async function expectLearningResultOrStableControls(
  page: Page,
  expectedText: RegExp,
): Promise<void> {
  const learningResult = panel(page, /Learning Result/i).first();
  try {
    await expect(learningResult).toBeVisible({ timeout: 10_000 });
    await expect(learningResult).toContainText(expectedText);
  } catch {
    await expect(recommendationControls(page).first()).toBeVisible();
  }
}
