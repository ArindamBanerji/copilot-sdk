import { test, expect } from "@playwright/test";
import { clickTab, expectAnyText } from "../helpers/ui";

test("dashboard shows financial impact", async ({ page }) => {
  await page.goto("/");

  await expectAnyText(page, [/Financial impact/i, /PVG savings/i]);
  await expectAnyText(page, [/leakage prevented/i, /cycle time saved/i, /auto approve efficiency/i, /unavailable/i]);
});

test("insight shows leakage detection", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Insight");

  await expect(page.getByRole("heading", { name: "Insight" })).toBeVisible();
  await expectAnyText(page, [/Leakage detection/i, /PVG at-risk invoices/i]);
  await expectAnyText(page, [/Total at risk/i, /No invoices currently meet/i, /Leakage data is unavailable/i, /S2P-INV/i]);
});

test("performance shows cycle-time signal or unavailable state", async ({ page }) => {
  await page.goto("/");
  await clickTab(page, "Performance");

  await expect(page.getByRole("heading", { name: "Performance" })).toBeVisible();
  await expectAnyText(page, [/Cycle-time/i, /Process bottleneck/i]);
  await expectAnyText(page, [/Total median minutes/i, /Bottleneck/i, /Celonis data not configured/i, /Cycle-time data is unavailable/i]);
});

test("PVG screens have no SOC vocabulary", async ({ page }) => {
  await page.goto("/");
  for (const tab of ["Dashboard", "Insight", "Performance"]) {
    await clickTab(page, tab);
    await expect(page.getByText(/credential_access/i)).toHaveCount(0);
    await expect(page.getByText(/lateral_movement/i)).toHaveCount(0);
    await expect(page.getByText(/data_exfiltration/i)).toHaveCount(0);
    await expect(page.getByText(/suppress/i)).toHaveCount(0);
  }
});
