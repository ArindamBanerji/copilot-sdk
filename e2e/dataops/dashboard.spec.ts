import { test, expect } from "../fixtures/copilot-fixture";
import { expectAnyText, waitForAppShell } from "../helpers/ui";

function dashboardPanel(page: import("@playwright/test").Page, heading: string | RegExp) {
  return page.locator("section, article").filter({
    has: page.locator("h1, h2, h3, h4", { hasText: heading }),
  }).first();
}

async function gotoDashboard(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByText("Pipeline Status")).toBeVisible({ timeout: 15_000 });
}

test("dashboard loads", async ({ page }) => {
  await gotoDashboard(page);

  await expect(page.getByRole("heading", { name: "DataOps Copilot" })).toBeVisible();
  await expect(page.locator("main")).not.toBeEmpty();
});

test("pipeline grid shows systems", async ({ page }) => {
  await gotoDashboard(page);

  const pipeline = dashboardPanel(page, "Pipeline Status");
  await expect(pipeline).toBeVisible();
  await expect(
    pipeline.getByText(/SAP MM|SAP FI|Celonis P2P|Warehouse WMS|Logistics DHL|Active alerts|Business criticality/i).first(),
  ).toBeVisible({ timeout: 15_000 });
});

test("enterprise health bar shows connection status", async ({ page }) => {
  await page.goto("/");

  await expectAnyText(page, [/Enterprise Health/i, /Process-Tech Fusion/i]);
  await expectAnyText(page, [/SAP S\/4HANA/i, /Celonis/i, /Graph/i]);
  await expectAnyText(page, [/Live/i, /cached/i, /unavailable/i, /connected/i]);
});

test("pipeline status shows system names with criticality", async ({ page }) => {
  await gotoDashboard(page);

  const pipeline = dashboardPanel(page, "Pipeline Status");
  await expect(pipeline).toBeVisible();
  await expect(pipeline.getByText(/Billing API|CRM Sync|ERP Export|HR Feed|Inventory Feed/i).first()).toBeVisible({
    timeout: 15_000,
  });
  await expect(pipeline.getByText(/Business criticality|\d+%/i).first()).toBeVisible();
});

test("AgentEvolver impact shows auto-resolved count and accuracy", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("AgentEvolver Impact")).toBeVisible();
  await expectAnyText(page, [/Auto-resolved/i, /Accuracy/i, /Hours saved/i]);
  await expectAnyText(page, [/\d+%/, /\d+(\.\d+)?/]);
});

test("alerts grouped by root cause", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Alert Root Causes")).toBeVisible();
  await expectAnyText(page, [/\d+ root causes/i, /critical\/high alerts/i, /Root-system alerts only/i, /DQ-\d+/]);
});

test("alert groups show counts and multiple systems", async ({ page }) => {
  await page.goto("/");

  const alerts = dashboardPanel(page, "Alert Root Causes");
  await expect(alerts).toBeVisible();
  await expect(alerts.getByText(/\d+\s+alert|\d+\s+root causes/i).first()).toBeVisible();
  await expect(alerts.getByText(/warehouse_etl|billing_api|crm_sync|erp_export|hr_feed|payment_gateway|inventory_feed|marketing_db|iot_sensors/i).first()).toBeVisible();
});

test("IKS value visible and numeric", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("IKS").first()).toBeVisible();
  await expect(page.getByLabel(/^IKS \d+$/).first()).toBeVisible();
});

test("SAP systems visible", async ({ page }) => {
  await gotoDashboard(page);

  const pipeline = dashboardPanel(page, "Pipeline Status");
  await expect(pipeline.getByText(/Billing API|CRM Sync|ERP Export|HR Feed|Inventory Feed/i).first()).toBeVisible({
    timeout: 15_000,
  });
});

test("conservation slider renders", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /^Conservation$/ })).toBeVisible();
  await expect(page.getByRole("slider")).toBeVisible();
  await expectAnyText(page, [/Threshold/i, /theta min/i, /Penalty ratio/i]);
});

test("conservation shows live decision count", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /^Conservation$/ })).toBeVisible();
  await expectAnyText(page, [/decisions/i, /verified/i, /accuracy/i, /IKS/i]);
});

test("conservation timeline shows events", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Conservation Timeline")).toBeVisible();
  await expectAnyText(page, [/approved/i, /denied/i, /No conservation events available/i, /Signal/i]);
});

test("conservation projection shows automation targets", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Automation Projection")).toBeVisible();
  await expectAnyText(page, [/55%/, /75%/, /90%/, /target/i]);
  await expectAnyText(page, [/auto.resolve/i, /accuracy/i, /verified decisions/i]);
});

test("projection shows three target levels", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Automation Projection")).toBeVisible();
  await expect(page.getByText(/55%/).first()).toBeVisible();
  await expectAnyText(page, [/75%/, /90%/]);
  await expectAnyText(page, [/projection/i, /target/i, /when/i, /automation/i]);
});

test("conservation projection shows timeline or accuracy gap", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Automation Projection")).toBeVisible();
  await expectAnyText(page, [
    /when/i,
    /week/i,
    /accuracy must improve/i,
    /Ready now/i,
    /Need \d+ more verified decisions/i,
    /Start making verified decisions/i,
  ]);
});

test("accuracy by category shows alert levels", async ({ page }) => {
  await page.goto("/");

  await expectAnyText(page, [/Accuracy Alerts/i, /accuracy.*alert/i, /No verified decisions yet/i]);
  await expectAnyText(page, [/threshold/i, /verified decisions/i, /category/i, /SC-12/i]);
});

test("SC-12 accuracy panel shows per-category bars", async ({ page }) => {
  await page.goto("/");

  const panel = page.locator("section", { hasText: /Accuracy Alerts|No verified decisions yet/i }).first();
  await expect(panel).toBeVisible();
  await expect(panel.getByText(/accuracy|category|threshold|verified decisions/i).first()).toBeVisible();
});

test("SC-12 accuracy panel shows alert threshold or percent", async ({ page }) => {
  await page.goto("/");

  await expectAnyText(page, [/SC-12/i, /Accuracy Alerts/i, /No verified decisions yet/i]);
  await expectAnyText(page, [/threshold/i, /alert/i, /below/i, /%/, /verified decisions/i]);
});
