import { test, expect } from "../fixtures/copilot-fixture";
import { expectAnyText } from "../helpers/ui";

test("dashboard loads", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "DataOps Copilot" })).toBeVisible();
  await expect(page.getByText("Pipeline Status")).toBeVisible();
  await expect(page.locator("main")).not.toBeEmpty();
});

test("pipeline grid shows systems", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Pipeline Status")).toBeVisible();
  await expectAnyText(page, [/SAP S\/4HANA/i, /billing/i, /warehouse/i, /Active alerts/i, /Business criticality/i]);
});

test("enterprise health bar shows connection status", async ({ page }) => {
  await page.goto("/");

  await expectAnyText(page, [/Enterprise Health/i, /Process-Tech Fusion/i]);
  await expectAnyText(page, [/SAP S\/4HANA/i, /Celonis/i, /Graph/i]);
  await expectAnyText(page, [/Live/i, /cached/i, /unavailable/i, /connected/i]);
});

test("pipeline status shows system names with criticality", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Pipeline Status")).toBeVisible();
  await expectAnyText(page, [/Warehouse ETL/i, /Payment Gateway/i, /CRM Sync/i, /SAP S\/4HANA Extract/i]);
  await expectAnyText(page, [/Business criticality/i, /\d+%/]);
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

  await expect(page.getByText("Alert Root Causes")).toBeVisible();
  await expectAnyText(page, [/\d+\s+alert/i, /\d+\s+root causes/i]);
  await expectAnyText(page, [/SAP S\/4HANA/i, /CRM/i, /HR Feed/i, /IoT/i, /Warehouse/i, /Billing/i]);
});

test("IKS value visible and numeric", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("IKS").first()).toBeVisible();
  await expect(page.getByLabel(/^IKS \d+$/).first()).toBeVisible();
});

test("SAP S/4HANA visible", async ({ page }) => {
  await page.goto("/");

  await expectAnyText(page, [/SAP S\/4HANA Extract/i, /sap_s4hana_extract/i]);
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

  await expectAnyText(page, [/Accuracy by Category/i, /accuracy.*category/i]);
  await expectAnyText(page, [/pipeline/i, /freshness/i, /schema/i]);
  await expectAnyText(page, [/critical/i, /warning/i, /\bok\b/i, /declining/i]);
});
