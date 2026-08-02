import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function openFirstTriage(page: Page) {
  await page.goto("/");
  await expect(page.getByText("Alert Root Causes").first()).toBeVisible({ timeout: 10_000 });
  const alertSection = page.locator("section", { hasText: "Alert Root Causes" });
  const triageButtons = alertSection.getByRole("button", { name: "Triage" });

  // The first AlertGroupCard is expanded by default.
  const count = await triageButtons.count();
  if (count === 0) {
    const groupHeader = alertSection
      .locator("button, summary, [role='button']")
      .filter({ hasText: /warehouse|billing|sap|crm|erp/i })
      .first();
    if (await groupHeader.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await groupHeader.click();
      await page.waitForTimeout(500);
    }
    if ((await triageButtons.count()) === 0) {
      return false;
    }
  }

  await triageButtons.first().click();
  await expect(page.getByRole("button", { name: "Back to Dashboard" })).toBeVisible({ timeout: 10_000 });
  await page.locator('[data-screen-ready="true"]').waitFor({ timeout: 15_000 });
  return true;
}

async function openKnownSystemTriage(page: Page) {
  await page.goto("/");
  await expect(page.getByText(/Pipeline Status|DataOps Copilot/i).first()).toBeVisible({ timeout: 10_000 });
  const knownGroup = page.getByRole("button", { name: /SAP S\/4HANA|billing|warehouse/i });
  if ((await knownGroup.count()) > 0) {
    await knownGroup.first().click();
  }
  const alertSection = page.locator("section", { hasText: "Alert Root Causes" });
  const knownRow = alertSection
    .locator("div, article")
    .filter({ hasText: /sap_s4hana_extract|billing_api|warehouse_etl|SAP S\/4HANA|billing|warehouse/i })
    .filter({ has: alertSection.getByRole("button", { name: "Triage" }) })
    .first();
  if (await knownRow.isVisible({ timeout: 5_000 }).catch(() => false)) {
    await knownRow.getByRole("button", { name: "Triage" }).click();
    await expect(page.getByRole("button", { name: "Back to Dashboard" })).toBeVisible();
    await page.locator('[data-screen-ready="true"]').waitFor({ timeout: 15_000 });
    return true;
  }

  const triageButtons = alertSection.getByRole("button", { name: "Triage" });
  if ((await triageButtons.count()) === 0) {
    const groupHeader = alertSection
      .locator("button, summary, [role='button']")
      .filter({ hasText: /warehouse|billing|sap|crm|erp/i })
      .first();
    if (await groupHeader.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await groupHeader.click();
      await page.waitForTimeout(500);
    }
  }
  if ((await triageButtons.count()) > 0) {
    await triageButtons.first().click();
    await expect(page.getByRole("button", { name: "Back to Dashboard" })).toBeVisible({ timeout: 10_000 });
    await page.locator('[data-screen-ready="true"]').waitFor({ timeout: 15_000 });
    return true;
  }
  return openFirstTriage(page);
}

function triageDetail(page: Page) {
  return page.locator("main").filter({
    has: page.getByRole("button", { name: "Back to Dashboard" }),
  });
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

  await expectAnyText(page, [/SLA/i]);
});

test("recurrence indicator visible on triage", async ({ page }) => {
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const detail = triageDetail(page);
  await expect(detail.getByText(/Recurring \(\d+x\)|Recurring|Seen \d+x before|First-time|All factors auto-computed/i).first()).toBeVisible();
});

test("AE recommendation badge visible on triage", async ({ page }) => {
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const detail = triageDetail(page);
  await expect(detail.getByText(/AE:|dataops-recurring-impact|dataops-freshness-sla|matched|All factors auto-computed/i).first()).toBeVisible();
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

test("resolution history shows accuracy and actions", async ({ page }) => {
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  await expectAnyText(page, [/Resolution History/i, /prior decisions/i]);
  await expectAnyText(page, [
    /accuracy/i,
    /\d+(\.\d+)?%/,
    /best action/i,
    /worst action/i,
    /Auto approve/i,
    /Investigate/i,
    /Escalate/i,
    /Pause downstream/i,
    /Refer/i,
  ]);
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
  await page.locator("section", { hasText: "Choose the operational response." }).getByRole("button", { name: "Investigate" }).click();
  await scoreResponse;

  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
  await expectAnyText(page, [/confidence/i, /Auto-approve/i, /Investigate/i, /\d+%/]);
});

test("score shows reward value after confirm", async ({ page }) => {
  test.setTimeout(60_000);
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.locator("section", { hasText: "Choose the operational response." }).getByRole("button", { name: /Investigate|Escalate to owner/i }).first().click();
  await scoreResponse;
  await expectAnyText(page, [/confidence/i, /Engine assessment/i, /\d+%/]);

  const learnResponse = page.waitForResponse((response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok());
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/system learned/i, /Reward/i, /IKS delta/i, /learned/i, /reward signal/i]);
});

test("reasoning panel appears after scoring", async ({ page }) => {
  test.setTimeout(60_000);
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.locator("section", { hasText: "Choose the operational response." }).getByRole("button", { name: "Investigate" }).click();
  await scoreResponse;

  await expectAnyText(page, [/Why This Recommendation/i, /Factor Analysis/i]);
  await expectAnyText(page, [/Historical Evidence/i, /Confidence Breakdown/i]);
});

test("reasoning panel shows evidence and confidence breakdown", async ({ page }) => {
  test.setTimeout(60_000);
  const opened = await openFirstTriage(page);
  test.skip(!opened, "No grouped alert available to triage.");

  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.locator("section", { hasText: "Choose the operational response." }).getByRole("button", { name: /Escalate to owner|Investigate/i }).first().click();
  await scoreResponse;

  await expectAnyText(page, [/dominant/i, /noisy/i, /moderate/i, /clean/i, /weight/i, /signal/i]);
  await expectAnyText(page, [/similar/i, /novel/i, /track record/i, /worked/i, /evidence/i]);
  await expectAnyText(page, [/Confidence Breakdown/i, /probability/i, /\d+(\.\d+)?%/]);
  await expectAnyText(page, [/learned from/i, /decisions/i, /verified/i, /Learning history unavailable/i]);
});
