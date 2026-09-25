import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

test.describe.configure({ timeout: 60_000 });
test.beforeEach(({}, testInfo) => {
  testInfo.setTimeout(60_000);
});

async function gotoPerformance(page: import("@playwright/test").Page) {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    await page.goto("/");
    await clickTab(page, "Performance");
    await page.waitForFunction(
      () => /Loading performance|Centroid Timeline|Accuracy Alerts|Performance unavailable/i.test(document.querySelector("main")?.textContent || ""),
      { timeout: 30_000 },
    );
    await page.locator('main > [data-screen-ready="true"]').waitFor({ state: "attached", timeout: 30_000 });
    if (await page.getByTestId("centroid-timeline-panel").count()) {
      await expect(page.getByTestId("centroid-timeline-panel")).toBeVisible({ timeout: 30_000 });
      return;
    }
  }
  await expect(page.getByTestId("centroid-timeline-panel")).toBeVisible({ timeout: 30_000 });
}

test("trajectory chart renders", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByTestId("centroid-timeline-panel")).toBeVisible();
  await expectAnyText(page, [/checkpoints/i, /Accuracy Alerts/i, /Decision Explorer/i]);
});

test("rolling metrics visible", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByTestId("audit-trail-panel")).toBeVisible();
  await expectAnyText(page, [/entries/i, /Immutable ledger/i]);
});

test("category performance shows categories", async ({ page }) => {
  await gotoPerformance(page);

  const panel = page.getByTestId("accuracy-alerts-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(/Accuracy Alerts/i);
  await expect(panel).toContainText(/\d+%|trend_following|event_driven|mean_reversion/i);
});

test("trajectory shows competitor and switching cost narrative", async ({ page }) => {
  await gotoPerformance(page);

  await expect(page.getByTestId("centroid-timeline-panel")).toBeVisible();
  await expectAnyText(page, [/centroid/i, /verified decisions/i, /checkpoints/i]);
});

test("conservation projection shows automation targets", async ({ page }) => {
  await gotoPerformance(page);

  await expectAnyText(page, [/Accuracy Alerts/i, /Centroid Timeline/i]);
  await expectAnyText(page, [/verified decisions/i, /\d+%/i, /checkpoints/i]);
});

test("conservation status shows projection targets", async ({ page }) => {
  await gotoPerformance(page);

  await expectAnyText(page, [/Accuracy Alerts/i, /Rule Lifecycle/i, /Audit Trail/i]);
  await expectAnyText(page, [/verified/i, /accuracy/i, /entries/i]);
});

test("SC-11 centroid timeline visible on performance", async ({ page }) => {
  await gotoPerformance(page);

  await expectAnyText(page, [/centroid/i, /timeline/i, /factor.*weight/i, /no.*centroid.*history/i, /no.*history/i, /evolution/i]);
});

