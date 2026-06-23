import { expect, test, type Page } from "@playwright/test";

async function mockDashboardApis(page: Page) {
  await page.route("**/api/s2p/preview/queue", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        exceptions: [],
        total: 0,
        auto_approve_rate: 0.18,
        confidence_avg: 0.82,
      },
    });
  });

  await page.route("**/api/s2p/preview/conservation", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        status: "GREEN",
        accuracy: 0.98,
        verified_decisions: 44,
      },
    });
  });

  await page.route("**/api/s2p/auto-approve/stats", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        total_auto_approved: 7,
        total_spot_checked: 12,
        spot_check_accuracy: 0.75,
        current_auto_approve_rate: 0.33,
        source: "in_memory_demo_stats",
        per_category: {
          price_variance: {
            approved: 3,
            held: 4,
            threshold: 0.91,
          },
          format_compliance: {
            approved: 4,
            held: 1,
            threshold: 0.8,
          },
        },
      },
    });
  });

  await page.route("**/api/s2p/auto-approve/expansion-proof?*", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        category: "price_variance",
        current_threshold: 0.91,
        proposed_threshold: 0.86,
        verified_decisions: 30,
        accuracy: 0.94,
        conservation_status: "GREEN",
        safe_to_expand: false,
        evidence: "price_variance has 30 verified decisions and GREEN conservation, but accuracy is below the expansion floor.",
        rollback_available: true,
      },
    });
  });
}

async function openDashboard(page: Page) {
  await mockDashboardApis(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

function autoApprovePanel(page: Page) {
  return page.locator("article", { hasText: "Auto-Approve Status" });
}

function expansionProofPanel(page: Page) {
  return autoApprovePanel(page)
    .locator("div", { has: page.getByRole("heading", { name: "Price Variance expansion proof" }) })
    .filter({ hasText: "Current threshold" });
}

test("dashboard shows auto-approve panel", async ({ page }) => {
  await openDashboard(page);
  const panel = autoApprovePanel(page);

  await expect(panel).toBeVisible();
  await expect(panel).toContainText(/Auto-approve rate|Loading auto-approve telemetry/i);
});

test("auto-approve panel displays per-category thresholds", async ({ page }) => {
  await openDashboard(page);
  const panel = autoApprovePanel(page);

  await expect(panel.getByRole("cell", { name: "Price Variance" })).toBeVisible();
  await expect(panel.getByRole("cell", { name: "Format Compliance" })).toBeVisible();
  await expect(panel).toContainText("91%");
  await expect(panel).toContainText("80%");
});

test("auto-approve panel shows spot-check count and accuracy", async ({ page }) => {
  await openDashboard(page);
  const panel = autoApprovePanel(page);

  await expect(panel).toContainText("Spot checks");
  await expect(panel).toContainText("12");
  await expect(panel).toContainText("Spot-check accuracy");
  await expect(panel).toContainText("75%");
});

test("auto-approve expansion proof button is visible", async ({ page }) => {
  await openDashboard(page);
  const panel = autoApprovePanel(page);

  await expect(panel.getByRole("button", { name: "View Expansion Proof" })).toBeVisible();
});

test("clicking expansion proof shows proof evidence", async ({ page }) => {
  await openDashboard(page);
  const panel = autoApprovePanel(page);

  await panel.getByRole("button", { name: "View Expansion Proof" }).click();

  const proof = expansionProofPanel(page);
  await expect(proof).toBeVisible();
  await expect(proof).toContainText("Current threshold");
  await expect(proof).toContainText("Proposed threshold");
  await expect(proof).toContainText("Verified decisions");
  await expect(proof).toContainText("GREEN");
  await expect(proof).toContainText(/accuracy is below the expansion floor/i);
  await expect(proof).toContainText("Available");
});
