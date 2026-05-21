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

test("dashboard shows auto-approve panel", async ({ page }) => {
  await openDashboard(page);

  await expect(page.getByRole("heading", { name: "Auto-Approve Status" })).toBeVisible();
  await expect(page.getByText("Auto-approve rate")).toBeVisible();
});

test("auto-approve panel displays per-category thresholds", async ({ page }) => {
  await openDashboard(page);

  await expect(page.getByText("Price Variance")).toBeVisible();
  await expect(page.getByText("Format Compliance")).toBeVisible();
  await expect(page.getByText("91%")).toBeVisible();
  await expect(page.getByText("80%")).toBeVisible();
});

test("auto-approve panel shows spot-check count and accuracy", async ({ page }) => {
  await openDashboard(page);

  await expect(page.getByText("Spot checks")).toBeVisible();
  await expect(page.getByText("12")).toBeVisible();
  await expect(page.getByText("Spot-check accuracy")).toBeVisible();
  await expect(page.getByText("75%")).toBeVisible();
});

test("auto-approve expansion proof button is visible", async ({ page }) => {
  await openDashboard(page);

  await expect(page.getByRole("button", { name: "View Expansion Proof" })).toBeVisible();
});

test("clicking expansion proof shows proof evidence", async ({ page }) => {
  await openDashboard(page);

  await page.getByRole("button", { name: "View Expansion Proof" }).click();

  await expect(page.getByRole("heading", { name: "Price Variance expansion proof" })).toBeVisible();
  await expect(page.getByText("Current threshold")).toBeVisible();
  await expect(page.getByText("Proposed threshold")).toBeVisible();
  await expect(page.getByText("Verified decisions")).toBeVisible();
  await expect(page.getByText("GREEN")).toBeVisible();
  await expect(page.getByText(/accuracy is below the expansion floor/i)).toBeVisible();
  await expect(page.getByText("Available")).toBeVisible();
});
