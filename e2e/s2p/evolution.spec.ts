import { test, expect, type Page } from "@playwright/test";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";

async function openEvidence(page: Page) {
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expect(page.getByRole("heading", { name: "Evidence", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "S2P evolution" })).toBeVisible({ timeout: 10_000 });
}

test("Evolution panel is visible on Evidence", async ({ page }) => {
  await openEvidence(page);

  await expectAnyText(page, [/AgentEvolver/i, /S2P evolution/i]);
  await expectAnyText(page, [/Evolution variants/i, /No evolution data yet/i, /No evolution history yet/i]);
});

test("Rule lifecycle shows states or empty state", async ({ page }) => {
  await openEvidence(page);

  await expectAnyText(page, [/variants/i, /All S2P categories/i, /No evolution data yet/i]);
  await expectAnyText(page, [/promoted/i, /shadow/i, /created/i, /No promoted rules yet/i, /No evolution data yet/i]);
});

test("Evolution history shows events or empty state", async ({ page }) => {
  await openEvidence(page);

  await expectAnyText(page, [/Evolution history/i]);
  await expectAnyText(page, [/win/i, /regression/i, /shadow/i, /No evolution history yet/i]);
});

test("Evolution screen has no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);

  await openEvidence(page);
  await expectAnyText(page, [/S2P evolution/i, /No evolution data yet/i]);

  expectNoConsoleErrors(errors);
});
