import { test, expect, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

async function openEvidence(page: Page) {
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expect(page.locator("main h1", { hasText: "Evidence" })).toBeVisible();
}

function panel(page: Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

test("invoice audit trail shows decision chain", async ({ page }) => {
  await openEvidence(page);
  const audit = panel(page, "Invoice audit trail");

  await expect(audit).toContainText(/Decision to outcome chain|audit target/i);
  await expect(audit).toContainText(/No recorded decisions|recommendation|decision/i);
});

test("rule lifecycle shows states", async ({ page }) => {
  await openEvidence(page);
  const rules = panel(page, "Rule lifecycle");

  await expect(rules).toContainText(/Seeded procurement controls/i);
  await expect(rules).toContainText(/proposed|shadow|promoted|rejected/i);
});

test("compliance summary shows percentages", async ({ page }) => {
  await openEvidence(page);
  const compliance = panel(page, "Compliance");

  await expect(compliance).toContainText(/Tax and regulatory/i);
  await expect(compliance).toContainText(/Compliant|Flagged|Total invoices|%/i);
});
