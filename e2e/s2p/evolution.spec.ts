import { test, expect, type Page } from "@playwright/test";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";

async function openEvidence(page: Page) {
  await page.goto("/");
  await clickTab(page, "Evidence");
  await expect(page.locator("main h1", { hasText: "Evidence" })).toBeVisible();
  await expect(evolutionRegion(page)).toBeVisible({ timeout: 10_000 });
}

function evolutionRegion(page: Page) {
  return page.getByRole("region", { name: "S2P preset evolution" });
}

test("Evolution panel is visible on Evidence", async ({ page }) => {
  await openEvidence(page);
  const region = evolutionRegion(page);

  await expect(region).toContainText(/Variant Evolution|No S2P variants/i);
  await expect(region).toContainText(/Active.*Evidence|Active.*Routing|No S2P variants|variant/i);
});

test("Rule lifecycle shows states or empty state", async ({ page }) => {
  await openEvidence(page);
  const region = evolutionRegion(page);

  await expect(region).toContainText(/variant|active|No S2P variants/i);
  await expect(region).toContainText(/promoted|shadow|active|No S2P variants/i);
});

test("Evolution history shows events or empty state", async ({ page }) => {
  await openEvidence(page);
  const region = evolutionRegion(page);

  await expect(region).toContainText(/Variant Evolution|Self-tuning/i);
  await expect(region).toContainText(/win|shadow|active|No S2P variants/i);
});

test("Evolution screen has no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);

  await openEvidence(page);
  await expect(evolutionRegion(page)).toContainText(/Variant Evolution|No S2P variants/i);

  expectNoConsoleErrors(errors);
});
