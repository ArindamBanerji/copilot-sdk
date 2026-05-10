import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

async function openFirstAlert(page: Page): Promise<boolean> {
  await page.goto("/");
  await expect(page.getByText("Alert Root Causes")).toBeVisible();
  const alertSection = page.locator("section", { hasText: "Alert Root Causes" });
  const triageButtons = alertSection.getByRole("button", { name: "Triage" });
  if ((await triageButtons.count()) === 0) {
    return false;
  }
  await triageButtons.first().click();
  await expect(page.getByRole("button", { name: "Back to Dashboard" })).toBeVisible();
  await expectAnyText(page, [/DQ-\d+/, /severity/i]);
  return true;
}

async function openKnownSystemAlert(page: Page): Promise<boolean> {
  await page.goto("/");
  await expect(page.getByText("Alert Root Causes")).toBeVisible();
  const group = page.getByRole("button", { name: /SAP S\/4HANA|billing|warehouse/i });
  if ((await group.count()) > 0) {
    await group.first().click();
  }
  const triage = page.locator("article", { hasText: /sap_s4hana_extract|billing_api|warehouse_etl|SAP S\/4HANA|billing|warehouse/i }).getByRole("button", { name: "Triage" });
  if ((await triage.count()) === 0) {
    return false;
  }
  await triage.first().click();
  await expect(page.getByRole("button", { name: "Back to Dashboard" })).toBeVisible();
  return true;
}

test("full triage lifecycle: dashboard, alert, score, confirm, back", async ({ page }) => {
  test.setTimeout(60_000);
  const opened = await openFirstAlert(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Investigate" }).click();
  await scoreResponse;
  const learnResponse = page.waitForResponse((response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok());
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/system learned/i, /Reward/i, /IKS delta/i]);
  await page.getByRole("button", { name: "Back to Dashboard" }).click();
  await expect(page.getByText("Alert Root Causes")).toBeVisible();
});

test("triage with Celonis context for billing, SAP, or warehouse", async ({ page }) => {
  const opened = await openKnownSystemAlert(page);
  test.skip(!opened, "No SAP, billing, or warehouse alert available through grouped UI.");

  await expectAnyText(page, [/Process Signals/i, /Celonis EMS/i, /Loading process context/i]);
  await expectAnyText(page, [/SAP/i, /billing/i, /warehouse/i, /Process metric/i, /variant/i]);
});

test("insight exploration: fingerprint, incident, evidence, curve", async ({ page }) => {
  await page.goto("/");

  await clickTab(page, "Insight");
  await expect(page.getByText("Fingerprint")).toBeVisible();
  await expect(page.getByText("Incident Replay")).toBeVisible();

  await clickTab(page, "Evidence");
  await expect(page.getByText("AgentEvolver Audit Trail")).toBeVisible();
  await expect(page.getByText("Pattern Origin")).toBeVisible();

  await clickTab(page, "Curve");
  await expect(page.getByText("Trajectory")).toBeVisible();
  await expectAnyText(page, [/SAP restructure/i, /Current IKS/i]);
});

test("tab navigation all 5 tabs and no blank screens", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await page.goto("/");

  for (const tab of ["Dashboard", "Triage", "Insight", "Evidence", "Curve"]) {
    await clickTab(page, tab);
    await expect(page.locator("main")).not.toBeEmpty();
    await expectAnyText(page, [new RegExp(tab, "i"), /Loading/i, /Select an alert/i, /Trajectory/i]);
  }

  expectNoConsoleErrors(errors);
});

test("conservation track record visible and interactive", async ({ page }) => {
  await page.goto("/");

  // Conservation section exists on dashboard
  await expect(page.getByText(/conservation|auto.resolve/i).first()).toBeVisible({ timeout: 5000 });

  // Track record events visible (denied/approved from pre-seeded data)
  await expectAnyText(page, [
    /approved/i,
    /denied/i,
    /GREEN/i,
    /AMBER/i,
    /headroom/i,
    /auto.resolve/i,
  ]);
});

test("dashboard alert groups expand and collapse", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Alert Root Causes")).toBeVisible();

  const groupButtons = page.locator("section", { hasText: "Alert Root Causes" }).getByRole("button").filter({ hasText: /alerts|No alerts|root/i });
  test.skip((await groupButtons.count()) === 0, "No alert group buttons available.");

  await groupButtons.first().click();
  await expectAnyText(page, [/Triage/i, /No alerts in this root-cause group/i, /Root-system alerts only/i]);
  await groupButtons.first().click();
  await expect(page.getByText("Alert Root Causes")).toBeVisible();
});
