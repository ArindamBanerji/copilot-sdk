import { test, expect, type Page } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

async function openEvidence(page: Page) {
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expect(page.getByRole("heading", { name: "Evidence", exact: true })).toBeVisible();
}

test("invoice audit trail shows decision chain", async ({ page }) => {
  await openEvidence(page);

  await expectAnyText(page, [/Invoice audit trail/i, /Decision to outcome chain/i, /audit target/i]);
  await expectAnyText(page, [/No recorded decisions/i, /recommendation/i, /decision/i]);
});

test("rule lifecycle shows states", async ({ page }) => {
  await openEvidence(page);

  await expectAnyText(page, [/Rule lifecycle/i, /Seeded procurement controls/i]);
  await expectAnyText(page, [/proposed/i, /shadow/i, /promoted/i, /rejected/i]);
});

test("compliance summary shows percentages", async ({ page }) => {
  await openEvidence(page);

  await expectAnyText(page, [/Compliance/i, /Tax and regulatory/i]);
  await expectAnyText(page, [/Compliant/i, /Flagged/i, /Total invoices/i, /%/i]);
});
