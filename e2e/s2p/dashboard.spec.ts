import { test, expect, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

function main(page: Page) {
  return page.locator("main");
}

function panel(page: Page, text: string | RegExp) {
  return page.locator("article").filter({
    has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
      hasText: text,
    }),
  });
}

function pageHeading(page: Page, text: string | RegExp) {
  return page.locator("main h1", { hasText: text });
}

test("Dashboard loads with exception queue", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(panel(page, "Exception Queue")).toContainText(/exception/i);
  await expect(panel(page, "Conservation Status")).toContainText(/conservation/i);
});

test("Exception Triage screen loads", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Exception Triage");

  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
  await expect(main(page)).toContainText(/triage|exception|invoice|Phase 1/i);
});

test("Insight screen loads", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Insight");

  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
  await expect(main(page)).toContainText(/profile|fingerprint|Phase 1/i);
});

test("Evidence screen loads", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Evidence");

  await expect(pageHeading(page, "Evidence")).toBeVisible();
  await expect(main(page)).toContainText(/governance|audit|Phase 1/i);
});

test("Suppliers screen loads with profiles", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Suppliers");

  await expect(page.getByRole("heading", { name: "Suppliers" })).toBeVisible();
  await expect(main(page)).toContainText(/supplier|profile|OTIF/i);
  await expect(panel(page, "Profile source")).toContainText(/Profile source|Exceptions|No supplier data yet|Unable to load supplier profiles/i);
});

test("Performance screen loads", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Performance");

  await expect(page.getByRole("heading", { name: "Performance" })).toBeVisible();
  await expect(main(page)).toContainText(/performance|trajectory|IKS|Phase 1/i);
});
