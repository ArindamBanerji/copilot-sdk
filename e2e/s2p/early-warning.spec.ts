import { expect, test, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function mockInsightApis(page: Page) {
  await page.route("**/api/s2p/preview/queue", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        exceptions: [
          {
            invoice_id: "INV-S2P-001",
            supplier_id: "SUP-005",
            supplier_name: "Yangtze Raw Materials",
            category: "price_variance",
            amount: 36750,
          },
        ],
        total: 1,
        auto_approve_rate: 0.18,
        confidence_avg: 0.82,
      },
    });
  });

  await page.route("**/api/s2p/suppliers/early-warnings", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        warnings: [
          {
            supplier_id: "SUP-005",
            supplier_name: "Yangtze Raw Materials",
            risk_score: 0.78,
            confidence: 0.78,
            pattern: "financial_stress_delivery_failure",
            recommendation: "Qualify backup supplier and review payment exposure before the next renewal cycle.",
            lead_time_weeks: 6,
            signals: [
              {
                signal_name: "OTIF",
                current_value: 0.84,
                baseline_value: 0.94,
                delta_pct: -10.64,
                direction: "declining",
                severity: "warning",
              },
              {
                signal_name: "exception_rate",
                current_value: 0.14,
                baseline_value: 0.08,
                delta_pct: 75,
                direction: "declining",
                severity: "critical",
              },
              {
                signal_name: "financial_health",
                current_value: 0.62,
                baseline_value: 0.82,
                delta_pct: -24.39,
                direction: "declining",
                severity: "warning",
              },
            ],
          },
        ],
        monitored_suppliers: 10,
        active_warnings: 1,
        patterns_detected: 1,
      },
    });
  });
}

async function openInsight(page: Page) {
  await mockInsightApis(page);
  await page.goto("/");
  await clickTab(page, "Insight");
  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
}

function earlyWarningPanel(page: Page) {
  return page.locator("article").filter({
    has: page.locator("h2", { hasText: "Early Warning Signals" }),
  });
}

test("Insight screen shows early warning panel", async ({ page }) => {
  await openInsight(page);
  const panel = earlyWarningPanel(page);

  await expect(panel).toBeVisible();
  await expect(panel).toContainText("Supplier trend risk");
});

test("early warning shows active warning count", async ({ page }) => {
  await openInsight(page);
  const panel = earlyWarningPanel(page);

  await expect(panel).toContainText("Active warnings");
  await expect(panel).toContainText("1 active");
  await expect(panel).toContainText("Monitored suppliers");
});

test("high risk supplier shows risk score", async ({ page }) => {
  await openInsight(page);
  const panel = earlyWarningPanel(page);

  await expect(panel).toContainText("Yangtze Raw Materials");
  await expect(panel).toContainText("Risk 78%");
  await expect(panel).toContainText("Confidence 78%");
});

test("warning shows signal breakdown", async ({ page }) => {
  await openInsight(page);
  const panel = earlyWarningPanel(page);

  await expect(panel).toContainText("OTIF");
  await expect(panel).toContainText("Exception Rate");
  await expect(panel).toContainText("Financial Health");
  await expect(panel).toContainText("Critical");
});

test("warning shows recommendation", async ({ page }) => {
  await openInsight(page);
  const panel = earlyWarningPanel(page);

  await expect(panel).toContainText("Qualify backup supplier");
  await expect(panel).toContainText("6w lead time");
});

test("early warning panel shows pattern label", async ({ page }) => {
  await openInsight(page);
  const panel = earlyWarningPanel(page);

  await expect(panel).toContainText("Financial Stress Delivery Failure");
});

test("early warning panel has no SOC vocabulary", async ({ page }) => {
  await openInsight(page);
  const panel = earlyWarningPanel(page);

  await expect(panel).not.toContainText(/credential_access/i);
  await expect(panel).not.toContainText(/lateral_movement/i);
  await expect(panel).not.toContainText(/data_exfiltration/i);
  await expect(panel).not.toContainText(/suppress/i);
});
