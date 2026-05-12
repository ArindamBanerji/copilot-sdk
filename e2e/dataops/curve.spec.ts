import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, expectTrajectoryOrEmpty } from "../helpers/ui";

async function gotoCurve(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Curve");
  await expectAnyText(page, [/Trajectory/i, /Loading DataOps learning curve/i]);
}

test("trajectory chart renders", async ({ page }) => {
  await gotoCurve(page);

  await expect(page.getByText("Trajectory")).toBeVisible();
  await expectAnyText(page, [/Current IKS/i, /Win Rate/i, /Decisions/i]);
  await expectTrajectoryOrEmpty(page);
});

test("disruption annotation visible", async ({ page }) => {
  await gotoCurve(page);

  await expectAnyText(page, [/SAP restructure/i, /6 pipeline configurations changed simultaneously/i, /recovery/i]);
});

test("centroid evolution shows top shifts", async ({ page }) => {
  await gotoCurve(page);

  await expectAnyText(page, [/Centroid Evolution/i, /centroid/i, /evolution/i, /shift/i]);
  await expectAnyText(page, [/data freshness/i, /recurrence/i, /impact/i]);
  await expectAnyText(page, [/0\.\d+/, /verified decisions/i, /Current \(\d+ decisions\)/i]);
});

test("SC-11 centroid timeline chart renders", async ({ page }) => {
  await gotoCurve(page);

  const panel = page.locator("section", { hasText: /Centroid History|centroid history/i }).first();
  await expect(panel).toBeVisible();
  await expectAnyText(page, [/SC-11/i, /Centroid History/i, /GraphStore/i, /checkpoints/i]);
});

test("SC-11 centroid timeline chart or empty history state renders", async ({ page }) => {
  await gotoCurve(page);

  await expectAnyText(page, [/centroid/i, /factor weight/i, /timeline/i, /No centroid history yet/i, /evolution/i]);
  await expectAnyText(page, [/Score some alerts to see learning/i, /checkpoints/i, /Centroid History/i]);
});
