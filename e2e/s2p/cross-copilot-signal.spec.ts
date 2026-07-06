import { expect, test, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function mockTriageApis(page: Page, withSignal: boolean) {
  await page.route("**/api/s2p/preview/queue", async (route) => {
    await route.fulfill({
      json: {
        exceptions: [
          {
            invoice_id: "S2P-INV-SIGNAL-1",
            event_id: "S2P-INV-SIGNAL-1",
            supplier_id: "Sysco",
            supplier_name: "Sysco",
            amount: 1200,
            category: "price_variance",
            confidence: 0.72
          }
        ],
        total: 1,
        auto_approve_rate: 0,
        confidence_avg: 0.72
      }
    });
  });
  await page.route("**/api/conservation/status", async (route) => {
    await route.fulfill({ json: { status: "GREEN", passed: true } });
  });
  await page.route("**/api/s2p/evidence/template?**", async (route) => {
    await route.fulfill({ json: { category: "price_variance", explanation: "Category explanation" } });
  });
  await page.route("**/api/s2p/situation/**", async (route) => {
    await route.fulfill({
      json: {
        decision_id: "S2P-DEC-SIGNAL-1",
        category: "price_variance",
        context_chain: [],
        nl_explanation: "Signal fixture situation",
        confidence: 0.91,
        factors_used: ["supplier_exception_history"],
        traversal_depth: 0,
        context_available: false,
        warnings: [],
        missing_variables: [],
        provenance: { nl_explanation: "sample", confidence: "learned", overall: "sample" }
      }
    });
  });
  await page.route("**/api/s2p/score", async (route) => {
    await route.fulfill({
      json: {
        event_id: "S2P-INV-SIGNAL-1",
        category: "price_variance",
        action: "hold_for_review",
        action_index: 1,
        confidence: 0.86,
        probabilities: [0.1, 0.7, 0.1, 0.05, 0.05],
        factor_vector: [0.2, 0.3, 0.1, 0.26, 0.2, 0.1, 0.1],
        factor_names: [
          "match_status",
          "amount_variance_ratio",
          "duplicate_score",
          "supplier_exception_history",
          "payment_terms_impact",
          "commodity_index_correlation",
          "tax_regulatory_compliance"
        ],
        decision_id: "S2P-DEC-SIGNAL-1",
        process_context: withSignal
          ? {
              cross_copilot_signal: {
                source: "purchasing",
                supplier: "Sysco",
                reliability: 74,
                delta: -19,
                warning: "Purchasing: reliability dropped 19pp",
                provenance: "signal"
              }
            }
          : null
      }
    });
  });
}

async function openTriage(page: Page) {
  await page.goto("/");
  await clickTab(page, "Exception Triage");
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
}

async function score(page: Page) {
  await openTriage(page);
  await page.getByRole("button", { name: /^Score$/i }).click();
}

test("Signal banner visible when cross_copilot_signal is in context", async ({ page }) => {
  await mockTriageApis(page, true);
  await score(page);

  await expect(page.getByRole("heading", { name: "Cross-Copilot Signal" })).toBeVisible();
  await expect(page.getByText(/Purchasing flagged Sysco/i)).toBeVisible();
  await expect(page.getByText(/signal/i).first()).toBeVisible();
});

test("Signal banner hidden when no signals are returned", async ({ page }) => {
  await mockTriageApis(page, false);
  await score(page);

  await expect(page.getByRole("heading", { name: "Cross-Copilot Signal" })).toHaveCount(0);
});

test("Signal banner shows supplier name", async ({ page }) => {
  await mockTriageApis(page, true);
  await score(page);

  await expect(page.getByText(/Sysco/).first()).toBeVisible();
  await expect(page.getByText(/reliability dropped 19pp/i)).toBeVisible();
});
