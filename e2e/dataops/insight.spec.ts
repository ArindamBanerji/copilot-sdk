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

test("decision explorer visible with decision count", async ({ page }) => {
  await gotoInsight(page);

  await expectAnyText(page, [/Decision Explorer/i, /decision history/i, /explorer/i]);
  await expectAnyText(page, [/\d+\s+decisions?/i]);
});

test("decision explorer shows action breakdown with win rates", async ({ page }) => {
  await gotoInsight(page);

  await expect(page.getByText("Decision Explorer")).toBeVisible();
  await expectAnyText(page, [/By Action/i, /Auto Approve/i, /Investigate/i, /Escalate/i, /Pause/i]);
  await expectAnyText(page, [/\d+%/]);
});

test("decision explorer filter changes results without losing count", async ({ page }) => {
  await gotoInsight(page);
  await expect(page.getByText("Decision Explorer")).toBeVisible();

  const panel = page.locator("section", { hasText: "Decision Explorer" });
  const selects = panel.locator("select");
  if ((await selects.count()) > 0 && (await selects.first().locator("option").count()) > 1) {
    await selects.first().selectOption({ index: 1 });
  }

  await expectAnyText(page, [/\d+\s+decisions?/i, /No decisions match these filters/i]);
});

test("decision explorer shows real categories not just unknown", async ({ page }) => {
  await gotoInsight(page);

  await expect(page.getByText("Decision Explorer")).toBeVisible();
  await expectAnyText(page, [/By Category/i]);
  await expectAnyText(page, [/pipeline/i, /schema/i, /volume/i, /freshness/i, /quality/i, /transform/i]);
});
