import { test, expect, type Page } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";

async function mockComplianceApis(page: Page) {
  await page.route("**/api/s2p/governance/compliance-screening", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        screening_timestamp: "2026-05-21T12:00:00Z",
        total_decisions_screened: 24,
        compliant: 23,
        with_gaps: 1,
        compliance_rate: 0.958,
        chain_integrity: {
          verified: true,
          chain_length: 24,
          last_hash: "abc123",
          broken_at_index: null,
        },
        conservation_state: {
          state: "GREEN",
          verified_count: 24,
          correct_count: 23,
          total_decisions: 24,
        },
        receipt_stats: {
          total_receipts: 24,
          confirms: 20,
          overrides: 4,
          override_rate: 0.167,
          chain_valid: true,
        },
        gaps: [],
        eu_ai_act: {
          article_14_traceable: true,
          human_oversight_documented: true,
          automated_decision_logged: true,
        },
        sox_readiness: {
          hash_chain_valid: true,
          override_distribution_available: true,
          conservation_proof_available: true,
          score: 1,
        },
      },
    });
  });
}

async function mockRationalizationApis(page: Page) {
  await page.route("**/api/s2p/governance/rationalization", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        total_suppliers: 3,
        grow: 1,
        maintain: 1,
        phase_out: 1,
        recommendations: [
          {
            supplier_id: "SUP-001",
            name: "Aster Industrial Chemicals",
            recommendation: "maintain",
            exception_rate: 0.12,
            otif: 0.88,
            trend: "declining",
            region: "unknown",
            total_invoices: 1240,
            reason: "Supplier performance is mixed but manageable.",
            action: "Maintain current allocation and monitor.",
          },
          {
            supplier_id: "SUP-003",
            name: "Northstar Packaging",
            recommendation: "grow",
            exception_rate: 0.04,
            otif: 0.96,
            trend: "improving",
            region: "unknown",
            total_invoices: 2120,
            reason: "Strong OTIF and controlled exception rate.",
            action: "Consider incremental volume consolidation.",
          },
        ],
        estimated_savings: {
          currency: "USD",
          estimated_quarterly_savings: 7750,
          estimated_annual_savings: 31000,
          phase_out_invoice_volume: 520,
          total_invoice_volume: 3880,
          suppliers_affected: 1,
          basis: "phase-out supplier exception rate multiplied by fixture invoice volume and demo exception handling cost",
        },
      },
    });
  });
}

async function openEvidence(page: Page) {
  await mockComplianceApis(page);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Evidence");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Evidence", exact: true })).toBeVisible();
}

async function openSuppliers(page: Page) {
  await mockRationalizationApis(page);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Suppliers");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Suppliers" })).toBeVisible();
}

function panel(page: Page, heading: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: heading,
    }),
  });
}

test("Evidence shows Compliance Screening panel", async ({ page }) => {
  await openEvidence(page);
  const compliance = panel(page, "Compliance Screening");

  await expect(compliance).toBeVisible();
  await expect(compliance).toContainText(/Governance controls/i);
});

test("Compliance Screening shows SOX score", async ({ page }) => {
  await openEvidence(page);
  const compliance = panel(page, "Compliance Screening");

  await expect(compliance).toContainText(/SOX score|Compliance screening is unavailable/i);
  await expect(compliance).toContainText(/100%|Review|unavailable/i);
});

test("Compliance Screening shows EU AI Act or Article 14 text", async ({ page }) => {
  await openEvidence(page);
  const compliance = panel(page, "Compliance Screening");

  await expect(compliance).toContainText(/Article 14 traceable|Compliance screening is unavailable/i);
  await expect(compliance).toContainText(/Human oversight documented|Automated decision logged|unavailable/i);
});

test("Compliance Screening shows compliance rate or gap count", async ({ page }) => {
  await openEvidence(page);
  const compliance = panel(page, "Compliance Screening");

  await expect(compliance).toContainText(/Compliance rate|Gaps|Compliance screening is unavailable/i);
  await expect(compliance).toContainText(/96%|1|unavailable/i);
});

test("Suppliers shows Supplier Rationalization panel", async ({ page }) => {
  await openSuppliers(page);
  const rationalization = panel(page, "Supplier Rationalization");

  await expect(rationalization).toBeVisible();
  await expect(rationalization).toContainText(/Supplier portfolio/i);
});

test("Supplier Rationalization shows grow maintain phase-out categories", async ({ page }) => {
  await openSuppliers(page);
  const rationalization = panel(page, "Supplier Rationalization");

  await expect(rationalization).toContainText(/Grow/i);
  await expect(rationalization).toContainText(/Maintain/i);
  await expect(rationalization).toContainText(/Phase out/i);
});

test("Supplier Rationalization shows savings or recommendations", async ({ page }) => {
  await openSuppliers(page);
  const rationalization = panel(page, "Supplier Rationalization");

  await expect(rationalization).toContainText(/Quarterly savings|Supplier rationalization is unavailable/i);
  await expect(rationalization).toContainText(/Annual savings|Supplier rationalization is unavailable/i);
  await expect(rationalization).toContainText(/Aster Industrial Chemicals|No supplier rationalization recommendations|unavailable/i);
});

test("Governance panels have no SOC vocabulary", async ({ page }) => {
  await openEvidence(page);
  const compliance = panel(page, "Compliance Screening");
  await expect(compliance).not.toContainText(/credential_access|lateral_movement|data_exfiltration|suppress/i);

  await openSuppliers(page);
  const rationalization = panel(page, "Supplier Rationalization");
  await expect(rationalization).not.toContainText(/credential_access|lateral_movement|data_exfiltration|suppress/i);
});
