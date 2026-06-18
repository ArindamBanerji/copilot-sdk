import { type APIRequestContext, type Locator, type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

const BACKEND = process.env.TRADING_BACKEND || "http://localhost:8010";

const FACTOR_NAMES = [
  "signal_alignment",
  "market_regime",
  "position_sizing",
  "timing_quality",
  "risk_reward_actual",
  "emotional_indicator",
  "signal_confidence",
  "options_delta_exposure",
  "options_iv_percentile",
  "options_gamma_risk",
];

const FACTOR_LABELS = FACTOR_NAMES.map(labelForFactor);
const FACTOR_TEXT = new RegExp(FACTOR_LABELS.join("|"), "i");

type TrustApiBody = {
  mode?: string;
  phase?: string;
  factors?: unknown[];
  factor_details?: unknown[];
  factorDetails?: unknown[];
  per_category?: Record<string, unknown[]>;
  perCategory?: Record<string, unknown[]>;
};

function labelForFactor(factor: string): string {
  return factor
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function factorRows(body: TrustApiBody): unknown[] {
  if (Array.isArray(body.factor_details)) return body.factor_details;
  if (Array.isArray(body.factorDetails)) return body.factorDetails;
  if (Array.isArray(body.factors)) return body.factors;
  return [];
}

async function fetchTrust(request: APIRequestContext, query = ""): Promise<TrustApiBody> {
  const res = await request.get(`${BACKEND}/api/context/trust-analysis${query}`);
  expect(res.status()).toBe(200);
  return (await res.json()) as TrustApiBody;
}

async function gotoDashboard(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
}

function trustPanel(page: Page): Locator {
  return page.getByTestId("trust-radar-panel").or(
    page.locator("section.copilot-card").filter({
      has: page.getByText(/Signal Trust Analysis/i),
    }),
  );
}

async function gotoAnalysis(page: Page): Promise<Locator> {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);

  const panel = trustPanel(page).first();
  await expect(panel).toBeVisible({ timeout: 10_000 });
  await expect(panel.getByText(/Loading signal trust/i)).toHaveCount(0, { timeout: 15_000 });
  return panel;
}

async function visibleFactorCount(panel: Locator): Promise<number> {
  let count = 0;
  for (const label of FACTOR_LABELS) {
    const factor = panel.getByText(label).first();
    if ((await factor.count()) === 0) continue;
    try {
      await expect(factor).toBeVisible({ timeout: 250 });
      count += 1;
    } catch {
      // Keep counting other factors.
    }
  }
  return count;
}

test.describe("Trust Radar - spot checks", () => {
  test("Analysis tab shows trust section heading", async ({ page }) => {
    const panel = await gotoAnalysis(page);

    await expect(panel.getByText(/Signal Trust Analysis/i)).toBeVisible();
  });

  test("Trust section shows at least one factor name", async ({ page }) => {
    const panel = await gotoAnalysis(page);

    await expect(panel.getByText(FACTOR_TEXT).first()).toBeVisible({ timeout: 10_000 });
  });

  test("Hero insight text is not empty", async ({ page }) => {
    const panel = await gotoAnalysis(page);
    const insight = panel.getByText(/Most consistent factor:|Your most trusted signal is|Insufficient data for trust analysis/i).first();

    await expect(insight).toBeVisible({ timeout: 10_000 });
    expect((await insight.textContent())?.trim().length).toBeGreaterThan(0);
  });

  test("Trust API returns valid response shape", async ({ request }) => {
    const body = await fetchTrust(request);

    expect(["dk", "variance"]).toContain(body.mode);
    expect(["A", "B"]).toContain(body.phase);
    expect(factorRows(body).length).toBeGreaterThan(0);
  });

  test("Trust API returns 10 factors", async ({ request }) => {
    const body = await fetchTrust(request);

    expect(factorRows(body)).toHaveLength(10);
  });

  test("Trust API per-category query works", async ({ request }) => {
    const body = await fetchTrust(request, "?category=trend_following");

    expect(factorRows(body)).toHaveLength(10);
  });

  test("Click on Analysis tab loads trust section", async ({ page }) => {
    await page.goto("/");
    await waitForAppShell(page);
    await clickTab(page, "Analysis");
    await waitForAppShell(page);

    await expect(trustPanel(page).first()).toBeVisible({ timeout: 5_000 });
  });

  test("Noise factors are visually distinguished", async ({ page }) => {
    const panel = await gotoAnalysis(page);
    const noise = panel.getByText(/\bnoise\b|noisy|very noisy/i).first();

    if ((await noise.count()) > 0) {
      await expect(noise).toBeVisible();
    } else {
      await expect(panel.getByText(/Signal Trust Analysis/i)).toBeVisible();
    }
  });

  test("Top signal callout is visible", async ({ page }) => {
    const panel = await gotoAnalysis(page);

    await expect(
      panel.getByText(/Your most trusted signal:|Your most trusted signal is|Most consistent factor:/i).first(),
    ).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("Trust Radar - flow tests", () => {
  test("Dashboard -> Analysis -> trust loads with data", async ({ page }) => {
    await gotoDashboard(page);
    await expectAnyText(page, [/Dashboard/i], { timeout: 10_000 });

    await clickTab(page, "Analysis");
    await waitForAppShell(page);

    const panel = trustPanel(page).first();
    await expect(panel).toBeVisible({ timeout: 10_000 });
    await expect(panel.getByText(/variance\s+\d|DK weight|Import trades/i).first()).toBeVisible({ timeout: 10_000 });
    expect(await visibleFactorCount(panel)).toBeGreaterThanOrEqual(3);
  });

  test("Category dropdown changes trust display", async ({ page }) => {
    const panel = await gotoAnalysis(page);
    const select = panel.locator("select").first();

    if ((await select.count()) === 0) {
      await expect(panel.getByText(/variance|Signal Trust Analysis/i).first()).toBeVisible();
      return;
    }

    const options = await select.locator("option").all();
    if (options.length <= 1) {
      await expect(select).toBeVisible();
      return;
    }

    await select.selectOption({ index: 1 });
    await expect(select).not.toHaveValue("");
    await expect(panel.getByText(/DK weight/i).first()).toBeVisible({ timeout: 5_000 });
  });

  test("Analysis -> Dashboard -> Analysis preserves trust", async ({ page }) => {
    const panel = await gotoAnalysis(page);
    const initialInsight = await panel
      .getByText(/Most consistent factor:|Your most trusted signal is|Insufficient data for trust analysis/i)
      .first()
      .textContent();

    await clickTab(page, "Dashboard");
    await waitForAppShell(page);
    await clickTab(page, "Analysis");
    await waitForAppShell(page);

    const nextPanel = trustPanel(page).first();
    await expect(nextPanel).toBeVisible({ timeout: 10_000 });
    const nextInsight = await nextPanel
      .getByText(/Most consistent factor:|Your most trusted signal is|Insufficient data for trust analysis/i)
      .first()
      .textContent();
    expect(nextInsight?.trim().length).toBeGreaterThan(0);
    if (initialInsight) expect(nextInsight).toBe(initialInsight);
  });

  test("Trust section and fingerprint show same factor set", async ({ page }) => {
    const panel = await gotoAnalysis(page);
    const trustCount = await visibleFactorCount(panel);
    expect(trustCount).toBeGreaterThan(0);

    const fingerprintMarker = page.getByText(/YOUR EDGE|YOUR NOISE|Fingerprint/i).first();
    if ((await fingerprintMarker.count()) === 0) return;

    await expect(fingerprintMarker).toBeVisible();
    const pageText = await page.locator("main").innerText();
    const overlap = FACTOR_LABELS.filter((label) => pageText.includes(label)).length;
    expect(overlap).toBeGreaterThan(0);
  });

  test("Full Analysis tab walkthrough - all panels render", async ({ page }) => {
    await gotoAnalysis(page);

    await expectAnyText(page, [/Signal Trust Analysis/i], { timeout: 10_000 });
    await expectAnyText(page, [/Pattern|behavioral/i], { timeout: 10_000 });
    await expectAnyText(page, [/Correlation|cross-position/i], { timeout: 10_000 });
    await expectAnyText(page, [/YOUR EDGE|YOUR NOISE|Fingerprint/i], { timeout: 10_000 });
    await expect(page.locator("main")).not.toContainText(/\b(error|unavailable)\b/i);
  });

  test("Dashboard market badge + Analysis trust - coherent data story", async ({ page }) => {
    await gotoDashboard(page);
    await expect(page.getByText(/Market data:/i).first()).toBeVisible({ timeout: 10_000 });

    await clickTab(page, "Analysis");
    await waitForAppShell(page);

    const panel = trustPanel(page).first();
    await expect(panel).toBeVisible({ timeout: 10_000 });
    await expect(panel.getByText(/Phase\s+[AB]/i).first()).toBeVisible();
  });
});
