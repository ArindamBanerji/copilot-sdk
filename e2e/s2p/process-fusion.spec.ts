import { expect, test, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

const FRONTEND = process.env.S2P_FRONTEND || "http://127.0.0.1:5177";

async function mockFusion(page: Page) {
  await page.route("**/api/s2p/enterprise/process-fusion", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        where: {
          bottleneck: "Chicago AP team",
          activity: "3-way match",
          avg_duration_hours: 4.2,
          vs_benchmark_hours: 1.1,
        },
        what: {
          pattern: "Chicago AP processes Suppliers X/Y/Z non-standard invoices",
          exception_rate: 0.34,
          vs_org_rate: 0.11,
        },
        why: {
          root_cause: "Suppliers X/Y/Z use non-standard format. Manual matching required.",
          situation_analysis: "Contract terms allow format variation per section 4.2",
        },
        which_decision: {
          recommendation: "Auto-route non-standard formats to specialized queue",
          estimated_impact: "$180K/year in analyst time",
          provenance: "sample",
          confidence: 0.78,
        },
      }),
    });
  });
}

async function openInsight(page: Page) {
  await mockFusion(page);
  await page.goto(FRONTEND);
  await expect(page.getByText(/S2P Copilot|Dashboard/i).first()).toBeVisible({ timeout: 10_000 });
  await clickTab(page, "Insight");
  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
}

test("process fusion panel visible on insight", async ({ page }) => {
  await openInsight(page);

  await expect(page.getByTestId("process-fusion-panel")).toBeVisible();
});

test("process fusion shows four sections", async ({ page }) => {
  await openInsight(page);

  await expect(page.getByTestId("process-fusion-where")).toContainText("WHERE");
  await expect(page.getByTestId("process-fusion-what")).toContainText("WHAT");
  await expect(page.getByTestId("process-fusion-why")).toContainText("WHY");
  await expect(page.getByTestId("process-fusion-which")).toContainText("WHICH DECISION");
});
