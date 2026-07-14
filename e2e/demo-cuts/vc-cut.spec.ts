import { test, expect } from "@playwright/test";
import {
  checkBackendHealth,
  checkPreseedActive,
  copilotUrl,
  navigateToTab,
  type DemoCopilot,
} from "./demo-fixture";

const PROVENANCE_TEXT = /learned|context|proven|sample|scraped_external|real_measured|transfer/i;

async function skipIfBackendDown(copilot: DemoCopilot, request: import("@playwright/test").APIRequestContext) {
  test.skip(!(await checkBackendHealth(request, copilot)), `${copilot} backend is not running`);
}

test.describe.serial("VC Demo Cut - 7 beats", () => {
  test.beforeAll(async ({ request }) => {
    test.skip(!(await checkPreseedActive(request, "trading")), "Demo preseed is not active: Trading IKS is zero");
  });

  test("V1: Trading Analysis shows Trust Radar, sigma values, and provenance", async ({ page, request }) => {
    await skipIfBackendDown("trading", request);
    await page.goto(copilotUrl("trading"));
    await navigateToTab(page, "Analysis");

    await expect(page.getByText(/Signal Trust Analysis|Trust Radar/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/sigma|variance|DK weight/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(PROVENANCE_TEXT).first()).toBeVisible({ timeout: 20_000 });
  });

  test("V2: SOC Runtime Evolution shows rejection, promotion, and testing story", async ({ page, request }) => {
    await skipIfBackendDown("soc", request);
    await page.goto(copilotUrl("soc"));
    await navigateToTab(page, "Runtime Evolution");

    await expect(page.getByText(/rejection|rejected|promoted|promotion|tested|shadow/i).first()).toBeVisible({
      timeout: 20_000,
    });
  });

  test("V3: Purchasing Performance shows transfer panel and locations", async ({ page, request }) => {
    await skipIfBackendDown("purchasing", request);
    await page.goto(copilotUrl("purchasing"));
    await navigateToTab(page, "Performance");

    await expect(page.getByText(/transfer|Downtown discipline becomes the baseline/i).first()).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByText(/Downtown/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/Airport/i).first()).toBeVisible({ timeout: 20_000 });
  });

  test("V4: Trading Analysis soft-checks counterfactual card", async ({ page, request }) => {
    await skipIfBackendDown("trading", request);
    await page.goto(copilotUrl("trading"));
    await navigateToTab(page, "Analysis");

    const counterfactual = page.getByText(/Counterfactual|what if/i).first();
    if ((await counterfactual.count()) > 0) {
      await expect(counterfactual).toBeVisible({ timeout: 10_000 });
      await expect(page.getByText(/\d+(\.\d+)?%|\$\d+|\b\d+\b/).first()).toBeVisible({ timeout: 10_000 });
    } else {
      test.info().annotations.push({
        type: "soft-check",
        description: "Counterfactual card not present; C-3 may not be built yet.",
      });
      await expect(page.getByText(/Signal Trust Analysis|YOUR TWO SELVES/i).first()).toBeVisible({ timeout: 20_000 });
    }
  });

  test("V5: SOC Compounding simulates failure and shows AMBER", async ({ page, request }) => {
    await skipIfBackendDown("soc", request);
    const response = await request.post(`http://127.0.0.1:${8001}/api/eval/simulate-failure`);
    expect(response.ok()).toBeTruthy();

    await page.goto(copilotUrl("soc"));
    await navigateToTab(page, "Compounding");
    await expect(page.getByText(/AMBER|conservation|failure/i).first()).toBeVisible({ timeout: 20_000 });
  });

  test("V6: Trading dashboard loads with provenance and no fabricated language", async ({ page, request }) => {
    await skipIfBackendDown("trading", request);
    await page.goto(copilotUrl("trading"));
    await navigateToTab(page, "Dashboard");

    await expect(page.getByText(PROVENANCE_TEXT).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.locator("main")).not.toContainText(/fabricated|made up|fake/i);
  });

  test("V7: SOC Evidence Room renders evidence and governance content", async ({ page, request }) => {
    await skipIfBackendDown("soc", request);
    await page.goto(copilotUrl("soc"));
    await navigateToTab(page, "Evidence Room");

    await expect(page.getByRole("heading", { name: /Evidence|Governance/i }).first()).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByText(/evidence|governance|audit|receipt|chain/i).first()).toBeVisible({
      timeout: 20_000,
    });
  });
});
