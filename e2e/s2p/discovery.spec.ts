import { expect, test, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function mockDiscoveryApis(page: Page) {
  await page.route("**/api/s2p/discovery/alerts", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        discoveries: [
          {
            discovery_id: "DISC-YANGTZE-PRICE-RISK",
            title: "Price increase risk at Yangtze Raw Materials",
            sources: ["Celonis", "D&B", "Commodity index", "S2P invoice exceptions"],
            correlation_strength: 0.89,
            impact_estimate: "$420K exposure in 6 weeks",
            pattern: "financial_stress_commodity_spike_exception_concentration",
            confidence: 0.89,
            discovered_at: "2026-05-01T08:00:00Z",
            recommendation: "Lock pricing and prepare backup POs before commodity exposure reaches open invoices.",
          },
          {
            discovery_id: "DISC-CHICAGO-FORMAT-CLUSTER",
            title: "Chicago invoice format exception concentration",
            sources: ["S2P invoice exceptions", "ERP vendor master", "AgentEvolver"],
            correlation_strength: 0.82,
            impact_estimate: "$180K annual processing cost",
            pattern: "regional_format_variance_exception_cluster",
            confidence: 0.82,
            discovered_at: "2026-05-01T08:05:00Z",
            recommendation: "Normalize invoice formats and route the corrected template through AgentEvolver validation.",
          },
          {
            discovery_id: "DISC-Q4-MRO-SEASONAL",
            title: "Seasonal MRO delivery recovery pattern",
            sources: ["Supplier profiles", "Purchase orders", "Goods receipt timing"],
            correlation_strength: 0.76,
            impact_estimate: "2-week buffer Q4 prevents expedited MRO replenishment",
            pattern: "q4_mro_delivery_buffer_recovery",
            confidence: 0.76,
            discovered_at: "2026-05-01T08:10:00Z",
            recommendation: "Add Q4 safety stock and pre-book MRO replenishment two weeks earlier.",
          },
        ],
        total_discoveries: 3,
        sources_connected: 4,
        highest_impact: "$420K exposure in 6 weeks",
      },
    });
  });

  await page.route("**/api/s2p/discovery/disruptions", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        disruptions: [
          {
            disruption_id: "TARIFF-SHOCK-2025-01",
            disruption_type: "tariff_shock",
            occurrence: 1,
            recovery_time_days: 90,
            recovery_cost: 15000000,
            improvement_from_first: 0,
            pattern_reuse: "none",
            decisions_applied: 0,
          },
          {
            disruption_id: "TARIFF-SHOCK-2025-09",
            disruption_type: "tariff_shock",
            occurrence: 2,
            recovery_time_days: 14,
            recovery_cost: 2000000,
            improvement_from_first: 0.84,
            pattern_reuse: "verified disruption-response decisions",
            decisions_applied: 47,
          },
          {
            disruption_id: "TARIFF-SHOCK-2026-03",
            disruption_type: "tariff_shock",
            occurrence: 3,
            recovery_time_days: 3,
            recovery_cost: 500000,
            improvement_from_first: 0.97,
            pattern_reuse: "62 decisions plus 3 promoted variants",
            decisions_applied: 62,
          },
        ],
        total_disruptions: 3,
        cumulative_savings: 27500000,
        avg_improvement_pct: 60.3,
        learning_narrative: "Each tariff-shock recovery is faster because S2P centroids accumulated verified disruption-response patterns.",
      },
    });
  });
}

async function openEvidence(page: Page) {
  await mockDiscoveryApis(page);
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expect(page.locator("main h1", { hasText: "Evidence" })).toBeVisible();
}

function panel(page: Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

function discoveryPanel(page: Page) {
  return panel(page, "Cross-System Discoveries");
}

function disruptionPanel(page: Page) {
  return panel(page, "Disruption Recovery Learning");
}

test("Evidence screen shows discovery panel", async ({ page }) => {
  await openEvidence(page);
  const discovery = discoveryPanel(page);

  await expect(discovery).toBeVisible();
  await expect(discovery).toContainText("Pattern discovery");
});

test("discovery panel shows alert count", async ({ page }) => {
  await openEvidence(page);
  const discovery = discoveryPanel(page);

  await expect(discovery).toContainText("Discoveries");
  await expect(discovery).toContainText("3");
});

test("discovery shows source badges", async ({ page }) => {
  await openEvidence(page);
  const discovery = discoveryPanel(page);

  await expect(discovery).toContainText("Celonis");
  await expect(discovery).toContainText("D&B");
  await expect(discovery).toContainText("Commodity index");
});

test("discovery shows impact estimate", async ({ page }) => {
  await openEvidence(page);
  const discovery = discoveryPanel(page);

  await expect(discovery).toContainText("Highest impact");
  await expect(discovery).toContainText("$420K exposure in 6 weeks");
});

test("Evidence screen shows disruption recovery panel", async ({ page }) => {
  await openEvidence(page);
  const disruption = disruptionPanel(page);

  await expect(disruption).toBeVisible();
  await expect(disruption).toContainText("Recovery memory");
});

test("disruption shows decreasing recovery times", async ({ page }) => {
  await openEvidence(page);
  const disruption = disruptionPanel(page);

  await expect(disruption).toContainText("90 days");
  await expect(disruption).toContainText("14 days");
  await expect(disruption).toContainText("3 days");
});

test("disruption shows cumulative savings", async ({ page }) => {
  await openEvidence(page);
  const disruption = disruptionPanel(page);

  await expect(disruption).toContainText("Cumulative savings");
  await expect(disruption).toContainText("$27.5M");
});

test("discovery and disruption panels have no SOC vocabulary", async ({ page }) => {
  await openEvidence(page);
  const discovery = discoveryPanel(page);
  const disruption = disruptionPanel(page);

  await expect(discovery).not.toContainText(/credential_access/i);
  await expect(discovery).not.toContainText(/lateral_movement/i);
  await expect(discovery).not.toContainText(/data_exfiltration/i);
  await expect(disruption).not.toContainText(/credential_access/i);
  await expect(disruption).not.toContainText(/lateral_movement/i);
  await expect(disruption).not.toContainText(/data_exfiltration/i);
}
);
