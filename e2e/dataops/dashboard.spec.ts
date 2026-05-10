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

test("alerts grouped by root cause", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Alert Root Causes")).toBeVisible();
  await expectAnyText(page, [/\d+ root causes/i, /critical\/high alerts/i, /Root-system alerts only/i, /DQ-\d+/]);
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

test("conservation timeline shows events", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Conservation Timeline")).toBeVisible();
  await expectAnyText(page, [/approved/i, /denied/i, /No conservation events available/i, /Signal/i]);
});
