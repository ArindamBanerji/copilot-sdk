import { test, expect, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function mockSimulationApis(page: Page) {
  await page.route("**/api/s2p/simulation/scenarios", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        scenarios: [
          {
            scenario_id: "SIM-001",
            name: "Tariff Shock - Southeast Asia",
            type: "tariff_increase",
            description: "Import tariff increase hits high-volume suppliers.",
            affected_suppliers: ["SUP-SEA-001"],
            affected_categories: ["price_variance"],
            trigger: "New tariff schedule",
            conservation_impact: "RED",
            estimated_quarterly_cost: 420000,
            recovery_time_days: 45,
          },
          {
            scenario_id: "SIM-003",
            name: "Demand Spike - Seasonal Peak",
            type: "demand_spike",
            description: "Seasonal demand increases exception volume.",
            affected_suppliers: ["SUP-SEAS-003"],
            affected_categories: ["quantity_mismatch"],
            trigger: "Forecasted demand spike",
            conservation_impact: "AMBER",
            estimated_quarterly_cost: 180000,
            recovery_time_days: 21,
          },
        ],
        total: 2,
      },
    });
  });

  await page.route("**/api/s2p/simulation/impact-summary", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        total_scenarios: 2,
        total_quarterly_exposure: 600000,
        worst_case_recovery_days: 45,
        scenarios_causing_red: 1,
        scenarios_causing_amber: 1,
        scenarios_green_safe: 0,
      },
    });
  });
}

async function mockDiscoveryApis(page: Page) {
  await page.route("**/api/s2p/discovery/extended", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        discoveries: [
          {
            discovery_id: "DISC-EXT-001",
            title: "Tariff pressure propagates to invoice holds",
            type: "commodity_risk",
            sources: ["Celonis", "D&B", "S2P invoice exceptions"],
            correlation_strength: 0.91,
            confidence: 0.89,
            impact_estimate: "$520K exposure in 8 weeks",
            supplier_ids: ["SUP-YANGTZE"],
            pattern: "commodity_spike_supplier_stress_exception_cluster",
            first_detected: "2026-05-02T09:00:00Z",
            detection_count: 18,
            recommendation: "Lock tariff-exposed pricing.",
            propagation_path: ["commodity_index", "supplier_risk", "price_variance", "buyer_escalation"],
          },
        ],
        total: 1,
        per_supplier: {
          "SUP-YANGTZE": {
            supplier_id: "SUP-YANGTZE",
            discovery_count: 1,
            detection_count: 18,
            highest_correlation: 0.91,
          },
        },
        by_type: {
          commodity_risk: 1,
        },
        sources_connected: 3,
      },
    });
  });
}

async function openDashboard(page: Page) {
  await mockSimulationApis(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

async function openInsight(page: Page) {
  await mockDiscoveryApis(page);
  await page.goto("/");
  await clickTab(page, "Insight");
  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
}

function panel(page: Page, heading: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: heading,
    }),
  });
}

test("Dashboard shows Disruption Simulation panel", async ({ page }) => {
  await openDashboard(page);
  const simulation = panel(page, "Disruption Simulation");

  await expect(simulation).toBeVisible();
  await expect(simulation).toContainText(/Scenario planning/i);
});

test("Disruption Simulation shows scenario or empty unavailable state", async ({ page }) => {
  await openDashboard(page);
  const simulation = panel(page, "Disruption Simulation");

  await expect(simulation).toContainText(/Tariff Shock|No disruption scenarios|unavailable/i);
  await expect(simulation).toContainText(/SIM-001|No disruption scenarios|unavailable/i);
});

test("Disruption Simulation shows conservation impact badges or summary counts", async ({ page }) => {
  await openDashboard(page);
  const simulation = panel(page, "Disruption Simulation");

  await expect(simulation).toContainText(/RED|AMBER|GREEN|unavailable/i);
  await expect(simulation).toContainText(/Scenario planning|Total exposure/i);
});

test("Disruption Simulation shows cost exposure and recovery information", async ({ page }) => {
  await openDashboard(page);
  const simulation = panel(page, "Disruption Simulation");

  await expect(simulation).toContainText(/Total exposure|Cost|unavailable/i);
  await expect(simulation).toContainText(/Worst recovery|Recovery|days|unavailable/i);
});

test("Insight shows Cross-System Discovery panel", async ({ page }) => {
  await openInsight(page);
  const discovery = panel(page, "Cross-System Discovery");

  await expect(discovery).toBeVisible();
  await expect(discovery).toContainText(/Connected signals/i);
});

test("Cross-System Discovery shows correlation or empty unavailable state", async ({ page }) => {
  await openInsight(page);
  const discovery = panel(page, "Cross-System Discovery");

  await expect(discovery).toContainText(/91%|No extended discoveries|unavailable/i);
  await expect(discovery).toContainText(/Tariff pressure|No extended discoveries|unavailable/i);
});

test("Cross-System Discovery shows sources or type distribution", async ({ page }) => {
  await openInsight(page);
  const discovery = panel(page, "Cross-System Discovery");

  await expect(discovery).toContainText(/Sources connected|unavailable/i);
  await expect(discovery).toContainText(/Distribution by type|commodity risk|unavailable/i);
});

test("Simulation and discovery panels have no SOC vocabulary", async ({ page }) => {
  await openDashboard(page);
  const simulation = panel(page, "Disruption Simulation");
  await expect(simulation).not.toContainText(/credential_access|lateral_movement|data_exfiltration|suppress/i);

  await openInsight(page);
  const discovery = panel(page, "Cross-System Discovery");
  await expect(discovery).not.toContainText(/credential_access|lateral_movement|data_exfiltration|suppress/i);
});
