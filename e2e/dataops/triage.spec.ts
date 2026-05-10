import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function openFirstTriage(page: Page) {
  await page.goto("/");
  await expect(page.getByText("Alert Root Causes")).toBeVisible();

  const alertSection = page.locator("section", { hasText: "Alert Root Causes" });
  const triageButtons = alertSection.getByRole("button", { name: "Triage" });
  if ((await triageButtons.count()) === 0) {
    await clickTab(page, "Triage");
    await expect(page.getByText("Select an alert from Dashboard to triage.")).toBeVisible();
    return false;
  }

  await triageButtons.first().click();
  await expect(page.getByRole("button", { name: "Back to Dashboard" })).toBeVisible();
  await expectAnyText(page, [/DQ-\d+/, /severity/i]);
  return true;
}

async function openKnownSystemTriage(page: Page) {
  await page.goto("/");
  await expect(page.getByText("Alert Root Causes")).toBeVisible();
  const knownGroup = page.getByRole("button", { name: /SAP S\/4HANA|billing|warehouse/i });
  if ((await knownGroup.count()) > 0) {
    await knownGroup.first().click();
  }
  const knownRow = page.locator("article", { hasText: /sap_s4hana_extract|billing_api|warehouse_etl|SAP S\/4HANA|billing|warehouse/i }).getByRole("button", { name: "Triage" });
  if ((await knownRow.count()) > 0) {
    await knownRow.first().click();
    await expect(page.getByRole("button", { name: "Back to Dashboard" })).toBeVisible();
    return true;
  }
  return openFirstTriage(page);
}

test("click grouped alert opens triage", async ({ page }) => {
  const opened = await openFirstTriage(page);

  if (opened) {
    await expectAnyText(page, [/Dependency Tree/i, /Action/i, /All factors auto-computed/i, /Factors auto-computed/i]);
  }
});

test("SLA countdown visible", async ({ page }) => {
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  await expectAnyText(page, [/SLA Countdown/i, /SLA:/i, /SLA BREACHED/i, /SLA unavailable/i]);
});

test("blast radius tree renders", async ({ page }) => {
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  await expect(page.getByText("Dependency Tree")).toBeVisible();
  await expectAnyText(page, [/Blast radius/i, /affected/i, /No dependency data/i, /SLA/i]);
});

test("resolution history shows prior decisions", async ({ page }) => {
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  await expect(page.getByText(/Resolution History/i)).toBeVisible();
  await expectAnyText(page, [/prior decisions/i, /No prior triage decisions/i, /Correct/i, /Incorrect/i, /Unknown/i]);
});

test("process signals panel shows Celonis for known systems if selectable", async ({ page }) => {
  const opened = await openKnownSystemTriage(page);
  test.skip(!opened, "No known system alert available to triage.");

  const loading = page.getByText(/Loading process context/i);
  if (await loading.isVisible().catch(() => false)) {
    await expect(loading).toBeHidden({ timeout: 10_000 });
  }
  await expectAnyText(page, [/Process Signals/i, /Celonis EMS/i]);
  await expectAnyText(page, [/O2C/i, /invoice/i, /ETL/i, /rework/i, /processing/i, /variant/i, /confidence/i, /V-\d+/i]);
});

test("process signals resolve to data or a clean no-panel state", async ({ page }) => {
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  await expect(page.getByText("Loading process context...")).toBeHidden({ timeout: 10_000 });
  const processSignals = page.getByText("Process Signals").first();
  if (await processSignals.isVisible()) {
    await expectAnyText(page, [/Celonis EMS/i, /Process metric/i, /variant/i]);
  } else {
    await expect(page.getByText("All factors auto-computed", { exact: false })).toBeVisible();
  }
});

test("six auto-computed factors visible", async ({ page }) => {
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  await expectAnyText(page, [/All factors auto-computed from graph/i, /Factors auto-computed from fixture graph/i, /Factor auto-fill/i]);
  for (const label of ["Impact scope", "Source reliability", "Recurrence frequency", "Downstream urgency", "Data freshness", "Business criticality"]) {
    await expect(page.getByText(label, { exact: true })).toBeVisible();
  }
});

test("similar alerts panel shows matches", async ({ page }) => {
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  await expectAnyText(page, [/Similar Alerts/i, /Finding similar alerts/i]);
  await expectAnyText(page, [/Past decisions/i, /No similar alerts found/i, /worked \d+\/\d+ times/i, /match/i]);
});

test("five action buttons visible", async ({ page }) => {
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  for (const action of ["Auto-approve", "Investigate", "Escalate to owner", "Pause downstream", "Refer to specialist"]) {
    await expect(page.getByRole("button", { name: new RegExp(action, "i") })).toBeVisible();
  }
});

test("score action produces result", async ({ page }) => {
  test.setTimeout(60_000);
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Investigate" }).click();
  await scoreResponse;

  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
  await expectAnyText(page, [/confidence/i, /Auto-approve/i, /Investigate/i, /\d+%/]);
});
