import { expect, test } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";

async function openAnalysis(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await expect(page.getByTestId("governed-vs-ungoverned-panel")).toBeVisible();
}

test("GU-01 renders governed and ungoverned columns", async ({ page }) => {
  await openAnalysis(page);
  await expect(page.getByTestId("ungoverned-path")).toBeVisible();
  await expect(page.getByTestId("governed-path")).toBeVisible();
});

test("GU-02 raw path shows score and action without gates", async ({ page }) => {
  await openAnalysis(page);
  const panel = page.getByTestId("ungoverned-path");
  await expect(panel).toContainText("Raw scorer output");
  await expect(panel).toContainText("No conservation, evidence, or promotion checks");
});

test("GU-03 governed path shows all gate dimensions", async ({ page }) => {
  await openAnalysis(page);
  const panel = page.getByTestId("governed-path");
  await expect(panel).toContainText(/Conservation/i);
  await expect(panel).toContainText(/Evidence/i);
  await expect(panel).toContainText(/Promotion/i);
  await expect(panel).toContainText(/Gate/i);
});

test("GU-04 divergence is highlighted when governance changes the action", async ({ page }) => {
  await openAnalysis(page);
  const panel = page.getByTestId("governed-vs-ungoverned-panel");
  await expect(panel).toContainText(/Decision diverges|Same input/i);
});

test("GU-05 panel is mounted on Trading Analysis", async ({ page }) => {
  await openAnalysis(page);
  await expect(page.getByText("DIFF-1")).toBeVisible();
});

test("GU-06 comparison caption is present", async ({ page }) => {
  await openAnalysis(page);
  await expect(page.getByTestId("governance-caption")).toContainText("Same input. Same model. Different decision");
});
