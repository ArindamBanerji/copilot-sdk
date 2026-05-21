import { expect, test, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function mockSupplierApis(page: Page) {
  await page.route("**/api/s2p/suppliers/clusters", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        clusters: [
          {
            cluster_id: 1,
            label: "Reliable Premium",
            members: ["SUP-001", "SUP-002", "SUP-003"],
            centroid: [0.94, 0.08, 0.82, 0.9, 0.75],
            consolidation_potential: "low",
            estimated_savings: 0,
          },
          {
            cluster_id: 2,
            label: "Budget Volatile",
            members: ["SUP-004", "SUP-005", "SUP-006"],
            centroid: [0.71, 0.26, 0.44, 0.68, 0.55],
            consolidation_potential: "high",
            estimated_savings: 2400000,
          },
          {
            cluster_id: 3,
            label: "Mid-Tier Consistent",
            members: ["SUP-007", "SUP-008"],
            centroid: [0.84, 0.14, 0.69, 0.8, 0.66],
            consolidation_potential: "medium",
            estimated_savings: 450000,
          },
          {
            cluster_id: 4,
            label: "Niche Specialist",
            members: ["SUP-009", "SUP-010"],
            centroid: [0.88, 0.12, 0.76, 0.86, 0.7],
            consolidation_potential: "low",
            estimated_savings: 0,
          },
        ],
        total_suppliers: 10,
        consolidation_candidates: 2,
        estimated_annual_savings: 2850000,
        method: "behavioral_centroid",
      },
    });
  });

  await page.route("**/api/s2p/suppliers", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        suppliers: [
          {
            supplier_id: "SUP-001",
            supplier_name: "Northstar",
            exception_rate: 0.08,
            exception_rate_trend: null,
            otif: 0.96,
            otif_by_quarter: {},
            avg_lead_time_days: null,
            lead_time_by_quarter: {},
            invoice_count: 12,
            last_invoice_date: null,
            pricing_trend: null,
            categories: ["price_variance"],
            last_updated: null,
            source: "fixture",
          },
        ],
        total: 1,
        source: "accumulator_with_fixture_fallback",
      },
    });
  });

  await page.route("**/api/s2p/suppliers/declining", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        suppliers: [],
        total: 0,
        source: "accumulator_with_fixture_fallback",
      },
    });
  });

  await page.route("**/api/s2p/suppliers/*/history?*", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        events: [],
        total: 0,
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

function clusteringPanel(page: Page) {
  return page.locator("article").filter({
    has: page.locator("h2", { hasText: "Behavioral Clusters" }),
  });
}

test("suppliers screen shows clustering panel", async ({ page }) => {
  await openSuppliers(page);
  const panel = clusteringPanel(page);

  await expect(panel).toBeVisible();
  await expect(panel).toContainText("behavioral centroid");
});

test("clustering panel shows cluster cards with labels", async ({ page }) => {
  await openSuppliers(page);
  const panel = clusteringPanel(page);

  await expect(panel).toContainText("Reliable Premium");
  await expect(panel).toContainText("Budget Volatile");
  await expect(panel).toContainText("Mid-Tier Consistent");
  await expect(panel).toContainText("Niche Specialist");
});

test("high potential cluster displays high potential status", async ({ page }) => {
  await openSuppliers(page);
  const panel = clusteringPanel(page);

  await expect(panel).toContainText("High potential");
});

test("clustering shows consolidation savings", async ({ page }) => {
  await openSuppliers(page);
  const panel = clusteringPanel(page);

  await expect(panel).toContainText("Annual Savings");
  await expect(panel).toContainText("$2.9M");
  await expect(panel).toContainText("Estimated savings");
});

test("clustering shows total supplier count", async ({ page }) => {
  await openSuppliers(page);
  const panel = clusteringPanel(page);

  await expect(panel).toContainText("Suppliers");
  await expect(panel).toContainText("10");
  await expect(panel).toContainText("Candidates");
});

test("clustering panel has no SOC vocabulary", async ({ page }) => {
  await openSuppliers(page);
  const panel = clusteringPanel(page);

  await expect(panel).not.toContainText(/credential_access/i);
  await expect(panel).not.toContainText(/lateral_movement/i);
  await expect(panel).not.toContainText(/data_exfiltration/i);
  await expect(panel).not.toContainText(/suppress/i);
});
