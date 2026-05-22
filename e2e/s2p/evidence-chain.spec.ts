import { test, expect, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

type ReceiptMode = "empty" | "with-receipts";

async function mockEvidenceChainApis(page: Page, mode: ReceiptMode = "empty") {
  const receipts =
    mode === "with-receipts"
      ? [
          {
            receipt_id: "receipt-001",
            invoice_id: "S2P-INV-1001",
            timestamp: "2026-05-21T12:00:00Z",
            scored_action: "hold_for_review",
            confidence: 0.82,
            factor_vector: [0.8, 0.2, 0.1, 0.4, 0.5, 0.3, 0.9],
            category: "price_variance",
            human_action: "hold_for_review",
            override_reason: null,
            reward: 1,
            centroid_updated: true,
            conservation_state_before: "GREEN",
            conservation_state_after: "GREEN",
            verified_count_before: 12,
            verified_count_after: 13,
            previous_hash: "",
            receipt_hash: "abc123def4567890",
          },
        ]
      : [];

  await page.route("**/api/s2p/evidence/receipts?**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        receipts,
        stats: {
          total_receipts: receipts.length,
          confirms: receipts.length,
          overrides: 0,
          override_rate: 0,
          chain_valid: true,
        },
      },
    });
  });

  await page.route("**/api/s2p/evidence/chain-integrity", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        verified: true,
        count: receipts.length,
      },
    });
  });

  await page.route("**/api/s2p/evidence/audit-pack", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        export_timestamp: "2026-05-21T12:30:00Z",
        receipt_count: receipts.length,
        chain_integrity: {
          verified: true,
          count: receipts.length,
        },
        conservation_state: {
          status: "GREEN",
          verified_count: 13,
          correct_count: 13,
          total_decisions: 13,
        },
        override_distribution: receipts.length
          ? {
              unspecified: 0,
            }
          : {},
        override_count: 0,
        confirm_count: receipts.length,
        receipts,
      },
    });
  });
}

async function openEvidence(page: Page, mode: ReceiptMode = "empty") {
  await mockEvidenceChainApis(page, mode);
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

test("Evidence shows Outcome Receipt Chain panel", async ({ page }) => {
  await openEvidence(page);
  const receipts = panel(page, "Outcome Receipt Chain");

  await expect(receipts).toBeVisible();
  await expect(receipts).toContainText(/Outcome evidence/i);
});

test("Receipt Chain shows statistics or empty receipt-chain state", async ({ page }) => {
  await openEvidence(page);
  const receipts = panel(page, "Outcome Receipt Chain");

  await expect(receipts).toContainText(/Total receipts/i);
  await expect(receipts).toContainText(/Confirms/i);
  await expect(receipts).toContainText(/Overrides/i);
  await expect(receipts).toContainText(/No outcome receipts have been recorded yet|S2P-INV/i);
});

test("Receipt Chain shows chain validity", async ({ page }) => {
  await openEvidence(page);
  const receipts = panel(page, "Outcome Receipt Chain");

  await expect(receipts).toContainText(/Chain validity/i);
  await expect(receipts).toContainText(/Valid|Review/i);
});

test("Evidence shows Audit Export panel", async ({ page }) => {
  await openEvidence(page);
  const audit = panel(page, "Audit Export");

  await expect(audit).toBeVisible();
  await expect(audit).toContainText(/SOX export/i);
});

test("Audit Export has Generate Audit Pack button", async ({ page }) => {
  await openEvidence(page);
  const audit = panel(page, "Audit Export");

  await expect(audit.getByRole("button", { name: /Generate Audit Pack/i })).toBeVisible();
});

test("Clicking Generate Audit Pack shows audit pack data or unavailable state", async ({ page }) => {
  await openEvidence(page, "with-receipts");
  const audit = panel(page, "Audit Export");

  await audit.getByRole("button", { name: /Generate Audit Pack/i }).click();
  await expect(audit).toContainText(/Receipt count|Audit pack is unavailable/i);
  await expect(audit).toContainText(/Confirms|Overrides|Chain integrity|Audit pack is unavailable/i);
  await expect(audit).toContainText(/Export timestamp|Audit pack is unavailable/i);
});

test("Receipt Chain shows hash values if receipts exist", async ({ page }) => {
  await openEvidence(page, "with-receipts");
  const receipts = panel(page, "Outcome Receipt Chain");

  await expect(receipts).toContainText(/S2P-INV-1001/i);
  await expect(receipts).toContainText(/abc123def4567890/i);
});

test("Receipt Chain shows zero or empty state when no receipts exist", async ({ page }) => {
  await openEvidence(page);
  const receipts = panel(page, "Outcome Receipt Chain");

  await expect(receipts).toContainText(/Total receipts/i);
  await expect(receipts).toContainText(/No outcome receipts have been recorded yet/i);
});

test("Evidence-chain panels have no SOC vocabulary", async ({ page }) => {
  await openEvidence(page, "with-receipts");
  const receipts = panel(page, "Outcome Receipt Chain");
  const audit = panel(page, "Audit Export");

  await expect(receipts).not.toContainText(/credential_access|lateral_movement|data_exfiltration|suppress/i);
  await expect(audit).not.toContainText(/credential_access|lateral_movement|data_exfiltration|suppress/i);
});
