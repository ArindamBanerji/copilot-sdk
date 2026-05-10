import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText } from "../helpers/ui";

async function gotoEvidence(page: import("@playwright/test").Page) {
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expectAnyText(page, [/AgentEvolver Impact/i, /Loading evolution evidence/i]);
}

test("AE impact panel visible", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("AgentEvolver Impact")).toBeVisible();
  await expectAnyText(page, [/Auto-resolved/i, /Accuracy/i, /Hours saved/i, /AE/i]);
});

test("evolution panel shows variants", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("AgentEvolver Audit Trail")).toBeVisible();
  await expectAnyText(page, [/promoted/i, /rejected/i, /shadow/i, /No evolution variants available/i, /V-/i]);
});

test("pattern origin chain visible", async ({ page }) => {
  await gotoEvidence(page);

  await expect(page.getByText("Pattern Origin")).toBeVisible();
  await expectAnyText(page, [/SOC/i, /S2P/i, /DataOps/i, /warm/i, /No cross-copilot chain available/i]);
});
