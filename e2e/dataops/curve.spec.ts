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
