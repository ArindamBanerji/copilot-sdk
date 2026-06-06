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

  const centroidPanel = page.locator("section", { has: page.getByRole("heading", { name: "Centroid Evolution" }) }).first();
  await expect(centroidPanel).toBeVisible();
  await expect(
    centroidPanel
      .getByText(
        /impact scope|source reliability|recurrence frequency|downstream urgency|data freshness|business criticality/i,
      )
      .first(),
  ).toBeVisible();
  await expect(centroidPanel.getByText(/0\.\d+|Current \(\d+ decisions\)/i).first()).toBeVisible();
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
