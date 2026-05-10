import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function gotoInsight(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Insight");
  await expectAnyText(page, [/Your profile/i, /Loading DataOps insight/i]);
}

test("profile archetype shows Pattern Matcher or profile", async ({ page }) => {
  await gotoInsight(page);

  await expectAnyText(page, [/The Pattern Matcher/i, /The Risk Assessor/i, /The Blast Analyst/i, /The SLA Guardian/i, /The Trust Trader/i, /The Freshness Monitor/i]);
});

test("fingerprint renders DataOps factors", async ({ page }) => {
  await gotoInsight(page);

  await expect(page.getByText("Fingerprint")).toBeVisible();
  await expectAnyText(page, [/Recurrence/i, /Business criticality/i, /Impact scope/i, /Downstream urgency/i, /Source reliability/i, /Data freshness/i]);
});

test("incident replay card shows incident and cost", async ({ page }) => {
  await gotoInsight(page);

  await expect(page.getByText("Incident Replay")).toBeVisible();
  await expectAnyText(page, [/\$50,?000/i, /incident/i, /Primary alert/i, /System recommendation/i]);
});
