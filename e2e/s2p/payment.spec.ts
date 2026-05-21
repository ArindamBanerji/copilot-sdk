import { expect, test, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

const paymentStrategies = [
  {
    supplier_id: "SUP-001",
    supplier_name: "Aster Industrial Chemicals",
    current_terms: "Net 45",
    recommended_strategy: "early_pay",
    reason: "Early pay improves OTIF for exception-prone chemical supply and unlocks a supplier discount.",
    payment_otif_correlation: 0.72,
    discount_opportunity: 180000,
    risk_if_delayed: "high",
    confidence: 0.86,
  },
  {
    supplier_id: "SUP-005",
    supplier_name: "Yangtze Raw Materials",
    current_terms: "Net 45",
    recommended_strategy: "early_pay",
    reason: "Supplier deprioritizes orders when payment exceeds 45 days.",
    payment_otif_correlation: 0.65,
    discount_opportunity: 120000,
    risk_if_delayed: "high",
    confidence: 0.84,
  },
  {
    supplier_id: "SUP-009",
    supplier_name: "Rhine-Stahl Metals",
    current_terms: "Net 45",
    recommended_strategy: "early_pay",
    reason: "Quality improves with early payment.",
    payment_otif_correlation: 0.58,
    discount_opportunity: 40000,
    risk_if_delayed: "medium",
    confidence: 0.81,
  },
  {
    supplier_id: "SUP-003",
    supplier_name: "Northstar Packaging",
    current_terms: "Net 30",
    recommended_strategy: "on_time",
    reason: "No meaningful payment-performance correlation; already performs well on Net-30 terms.",
    payment_otif_correlation: 0.15,
    discount_opportunity: 0,
    risk_if_delayed: "low",
    confidence: 0.78,
  },
  {
    supplier_id: "SUP-004",
    supplier_name: "Novatek IT Services",
    current_terms: "Net 60",
    recommended_strategy: "on_time",
    reason: "Premium service levels remain stable regardless of payment timing.",
    payment_otif_correlation: 0.08,
    discount_opportunity: 0,
    risk_if_delayed: "low",
    confidence: 0.76,
  },
  {
    supplier_id: "SUP-002",
    supplier_name: "Pacifica Logistics",
    current_terms: "Net 30",
    recommended_strategy: "on_time",
    reason: "Stable performance across terms; keep standard on-time payment cadence.",
    payment_otif_correlation: 0.22,
    discount_opportunity: 0,
    risk_if_delayed: "medium",
    confidence: 0.74,
  },
  {
    supplier_id: "SUP-010",
    supplier_name: "Helix Lab Supplies",
    current_terms: "Net 30",
    recommended_strategy: "on_time",
    reason: "Stable lab supplier performance supports normal on-time payment.",
    payment_otif_correlation: 0.18,
    discount_opportunity: 0,
    risk_if_delayed: "low",
    confidence: 0.77,
  },
  {
    supplier_id: "SUP-006",
    supplier_name: "Meridian Office Services",
    current_terms: "Net 15",
    recommended_strategy: "extend",
    reason: "No performance impact from later payment; extend terms for DPO +8 days.",
    payment_otif_correlation: -0.02,
    discount_opportunity: 0,
    risk_if_delayed: "low",
    confidence: 0.82,
  },
  {
    supplier_id: "SUP-007",
    supplier_name: "Boreal Equipment Maintenance",
    current_terms: "Net 30",
    recommended_strategy: "extend",
    reason: "No payment-performance correlation and lower volume support a working-capital extension.",
    payment_otif_correlation: 0.05,
    discount_opportunity: 0,
    risk_if_delayed: "low",
    confidence: 0.75,
  },
  {
    supplier_id: "SUP-008",
    supplier_name: "Gridline Utilities",
    current_terms: "Due on receipt",
    recommended_strategy: "extend",
    reason: "Utility service has no OTIF sensitivity to payment timing; extend where contract allows.",
    payment_otif_correlation: -0.01,
    discount_opportunity: 0,
    risk_if_delayed: "low",
    confidence: 0.8,
  },
];

async function mockSupplierApis(page: Page) {
  await page.route("**/api/s2p/suppliers/payment-strategy", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        strategies: paymentStrategies,
        total_discount_opportunity: 340000,
        suppliers_analyzed: 10,
        dpo_improvement_days: 8,
        summary: "3 early-pay ($340K/yr), 4 on-time, 3 extend (+8 DPO days)",
      },
    });
  });

  await page.route("**/api/s2p/suppliers/clusters", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        clusters: [],
        total_suppliers: 0,
        consolidation_candidates: 0,
        estimated_annual_savings: 0,
        method: "behavioral_centroid",
      },
    });
  });

  await page.route("**/api/s2p/suppliers/declining", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: { suppliers: [], total: 0, source: "accumulator_with_fixture_fallback" },
    });
  });

  await page.route("**/api/s2p/suppliers/*/history?*", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: { events: [], total: 0 },
    });
  });

  await page.route("**/api/s2p/suppliers/*/heatmap", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: { supplier_id: "SUP-001", categories: [], factors: [], invoice_count: 0 },
    });
  });

  await page.route("**/api/s2p/suppliers", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        suppliers: [
          {
            supplier_id: "SUP-001",
            supplier_name: "Aster Industrial Chemicals",
            exception_rate: 0.12,
            exception_rate_trend: null,
            otif: 0.88,
            otif_by_quarter: {},
            avg_lead_time_days: null,
            lead_time_by_quarter: {},
            invoice_count: 1240,
            last_invoice_date: null,
            pricing_trend: null,
            categories: ["industrial chemicals"],
            last_updated: null,
            source: "fixture",
          },
        ],
        total: 1,
        source: "accumulator_with_fixture_fallback",
      },
    });
  });
}

async function openSuppliers(page: Page) {
  await mockSupplierApis(page);
  await page.goto("/");
  await clickTab(page, "Suppliers");
  await expect(page.getByRole("heading", { name: "Suppliers" })).toBeVisible();
}

function paymentPanel(page: Page) {
  return page.locator("article").filter({
    has: page.locator("h2", { hasText: "Payment Timing Optimization" }),
  });
}

test("Suppliers screen shows payment strategy panel", async ({ page }) => {
  await openSuppliers(page);
  const panel = paymentPanel(page);

  await expect(panel).toBeVisible();
  await expect(panel).toContainText("Working capital");
});

test("payment strategy shows total discount opportunity", async ({ page }) => {
  await openSuppliers(page);
  const panel = paymentPanel(page);

  await expect(panel).toContainText("Discount opportunity");
  await expect(panel).toContainText("$340K");
});

test("payment strategy shows strategy breakdown", async ({ page }) => {
  await openSuppliers(page);
  const panel = paymentPanel(page);

  await expect(panel).toContainText("Early pay");
  await expect(panel).toContainText("On-time");
  await expect(panel).toContainText("Extend");
});

test("early-pay suppliers show discount amounts", async ({ page }) => {
  await openSuppliers(page);
  const panel = paymentPanel(page);

  await expect(panel).toContainText("Aster Industrial Chemicals");
  await expect(panel).toContainText("$180K");
  await expect(panel).toContainText("Yangtze Raw Materials");
  await expect(panel).toContainText("$120K");
});

test("extend suppliers show DPO improvement", async ({ page }) => {
  await openSuppliers(page);
  const panel = paymentPanel(page);

  await expect(panel).toContainText("DPO improvement");
  await expect(panel).toContainText("+8 days");
  await expect(panel).toContainText("Meridian Office Services");
});

test("payment strategy table has all suppliers analyzed", async ({ page }) => {
  await openSuppliers(page);
  const panel = paymentPanel(page);

  await expect(panel).toContainText("Suppliers analyzed");
  await expect(panel).toContainText("10");
  await expect(panel.locator("tbody tr")).toHaveCount(10);
});

test("payment panel has no SOC vocabulary", async ({ page }) => {
  await openSuppliers(page);
  const panel = paymentPanel(page);

  await expect(panel).not.toContainText(/credential_access/i);
  await expect(panel).not.toContainText(/lateral_movement/i);
  await expect(panel).not.toContainText(/data_exfiltration/i);
  await expect(panel).not.toContainText(/suppress/i);
});
