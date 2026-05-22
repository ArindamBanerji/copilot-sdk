import { test, expect, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function mockObservabilityApis(page: Page) {
  await page.route("**/api/s2p/novelty/status", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        window_size: 50,
        distance_threshold: 0.6,
        total_in_window: 24,
        novelty_count: 3,
        novelty_rate: 0.125,
        alert_active: false,
        per_category: {
          price_variance: {
            total_in_window: 12,
            novelty_count: 1,
            novelty_rate: 0.083,
          },
          duplicate_risk: {
            total_in_window: 12,
            novelty_count: 2,
            novelty_rate: 0.167,
          },
        },
      },
    });
  });

  await page.route("**/api/s2p/explorer/drift/**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        category: 0,
        category_name: "price_variance",
        factors: [
          "match_status",
          "amount_variance_ratio",
          "duplicate_score",
          "supplier_exception_history",
          "payment_terms_impact",
          "commodity_index_correlation",
          "tax_regulatory_compliance",
        ],
        centroids: {
          auto_approve: [0.88, 0.12, 0.08, 0.18, 0.24, 0.30, 0.92],
          hold_for_review: [0.55, 0.42, 0.22, 0.34, 0.38, 0.40, 0.76],
          escalate_to_buyer: [0.35, 0.74, 0.28, 0.45, 0.42, 0.48, 0.68],
        },
      },
    });
  });

  await page.route("**/api/s2p/explorer/dk-weights", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        factors: [
          "match_status",
          "amount_variance_ratio",
          "duplicate_score",
          "supplier_exception_history",
          "payment_terms_impact",
          "commodity_index_correlation",
          "tax_regulatory_compliance",
        ],
        weights: [],
        available: false,
      },
    });
  });
}

async function openDashboard(page: Page) {
  await mockObservabilityApis(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

async function openInsight(page: Page) {
  await mockObservabilityApis(page);
  await page.goto("/");
  await clickTab(page, "Insight");
  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
}

function panel(page: Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

test("Dashboard shows Distribution Monitor panel", async ({ page }) => {
  await openDashboard(page);
  const monitor = panel(page, "Distribution Monitor");

  await expect(monitor).toBeVisible();
  await expect(monitor).toContainText(/Novelty detection/i);
});

test("Distribution Monitor shows novelty rate and status", async ({ page }) => {
  await openDashboard(page);
  const monitor = panel(page, "Distribution Monitor");

  await expect(monitor).toContainText(/Novelty rate/i);
  await expect(monitor).toContainText(/13%|12%/i);
  await expect(monitor).toContainText(/Alert status/i);
  await expect(monitor).toContainText(/Normal|ALERT/i);
});

test("Distribution Monitor shows window information", async ({ page }) => {
  await openDashboard(page);
  const monitor = panel(page, "Distribution Monitor");

  await expect(monitor).toContainText(/Decisions in window/i);
  await expect(monitor).toContainText(/Window size/i);
  await expect(monitor).toContainText(/24/);
  await expect(monitor).toContainText(/50/);
});

test("Insight shows Centroid Explorer panel", async ({ page }) => {
  await openInsight(page);
  const explorer = panel(page, "Centroid Explorer");

  await expect(explorer).toBeVisible();
  await expect(explorer).toContainText(/Centroid evidence/i);
});

test("Centroid Explorer shows Factor Weights section", async ({ page }) => {
  await openInsight(page);
  const explorer = panel(page, "Centroid Explorer");

  await expect(explorer).toContainText(/Factor weights/i);
  await expect(explorer).toContainText(/DK weights unavailable|DK weights are available/i);
  await expect(explorer).toContainText(/match status|amount variance/i);
});

test("Centroid Explorer shows Centroids by Action", async ({ page }) => {
  await openInsight(page);
  const explorer = panel(page, "Centroid Explorer");

  await expect(explorer).toContainText(/auto approve/i);
  await expect(explorer).toContainText(/hold for review/i);
  await expect(explorer).toContainText(/escalate to buyer/i);
});

test("Centroid Explorer has category selector", async ({ page }) => {
  await openInsight(page);
  const explorer = panel(page, "Centroid Explorer");

  await expect(explorer.getByLabel(/Category/i)).toBeVisible();
  await expect(explorer).toContainText(/price variance/i);
});

test("Observability panels have no SOC vocabulary", async ({ page }) => {
  await openDashboard(page);
  const monitor = panel(page, "Distribution Monitor");
  await expect(monitor).not.toContainText(/credential_access|lateral_movement|data_exfiltration|suppress/i);

  await openInsight(page);
  const explorer = panel(page, "Centroid Explorer");
  await expect(explorer).not.toContainText(/credential_access|lateral_movement|data_exfiltration|suppress/i);
});
