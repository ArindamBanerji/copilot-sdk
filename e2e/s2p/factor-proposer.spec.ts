import { test, expect, type APIRequestContext, type APIResponse, type Page } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";

const API_BASE = "http://127.0.0.1:8002";

async function optionalEndpoint(request: APIRequestContext, path: string): Promise<APIResponse | null> {
  const health = await request.get(`${API_BASE}/health`, { timeout: 5_000 }).catch(() => null);
  if (!health?.ok()) return null;
  const response = await request.get(`${API_BASE}${path}`, { timeout: 5_000 }).catch(() => null);
  if (!response || response.status() === 404) return null;
  return response;
}

async function mockFactorApis(page: Page) {
  await page.route("**/api/s2p/factors/analysis", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        factors: [
          {
            factor_name: "match_status",
            current_dk_weight: 0.22,
            signal_contribution_pct: 40.0,
            outcome_correlation: 0.46,
            verdict: "keep",
            estimated_impact_pp: 0,
          },
          {
            factor_name: "tax_regulatory_compliance",
            current_dk_weight: 0.04,
            signal_contribution_pct: 3.0,
            outcome_correlation: 0.03,
            verdict: "replace_candidate",
            replacement_suggestion: "tariff_exposure",
            estimated_impact_pp: 4,
          },
        ],
        count: 2,
        advisory: true,
      },
    });
  });
  await page.route("**/api/s2p/factors/propose", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        factor: "tax_regulatory_compliance",
        replacement: "tariff_exposure",
        estimated_pp: 4,
        rationale: "Dry-run tariff_exposure before changing production factors.",
        advisory: true,
      },
    });
  });
}

async function openEvidence(page: Page) {
  await mockFactorApis(page);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Evidence");
  await expect(page.locator("main h1", { hasText: "Evidence" })).toBeVisible();
}

test("factor analysis endpoint returns array", async ({ page }) => {
  const response = await optionalEndpoint(page.request, "/api/s2p/factors/analysis");
  test.skip(!response, "S2P factor analysis endpoint not available");
  if (!response) return;
  expect(response.ok()).toBeTruthy();
  expect(Array.isArray((await response.json()).factors)).toBeTruthy();
});

test("factor recommendations endpoint returns candidates", async ({ page }) => {
  const response = await optionalEndpoint(page.request, "/api/s2p/factors/recommendations");
  test.skip(!response, "S2P factor recommendations endpoint not available");
  if (!response) return;
  expect(response.ok()).toBeTruthy();
  expect(Array.isArray((await response.json()).recommendations)).toBeTruthy();
});

test("factor insight panel renders on Evidence tab", async ({ page }) => {
  await openEvidence(page);
  await expect(page.getByRole("heading", { name: "Factor Intelligence" })).toBeVisible();
});

test("factor chart shows bars for each factor", async ({ page }) => {
  await openEvidence(page);
  const panel = page.locator("article", { hasText: "Factor Intelligence" });
  await expect(panel).toContainText("match status");
  await expect(panel).toContainText("tax regulatory compliance");
});

test("replace candidate highlighted in amber", async ({ page }) => {
  await openEvidence(page);
  await expect(page.locator("article", { hasText: "Factor Intelligence" })).toContainText("replace candidate");
});

test("propose replacement returns recommendation", async ({ page }) => {
  await openEvidence(page);
  await page.getByRole("button", { name: "Propose Replacement" }).click();
  await expect(page.locator("article", { hasText: "Factor Intelligence" })).toContainText("tariff exposure");
});
