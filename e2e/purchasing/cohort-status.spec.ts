import { test, expect } from "../fixtures/copilot-fixture";
import { collectConsoleErrors, clickTab, expectNoConsoleErrors, waitForScreenReady } from "../helpers/ui";

const BACKEND = process.env.PURCHASING_BACKEND || "http://127.0.0.1:8020";
const states = ["INSTRUMENT_VALIDATED", "ACCUMULATING", "MEASURED"];

async function gotoPanel(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
  await expect(page.getByTestId("cohort-status-panel")).toBeVisible({ timeout: 20_000 });
}

test("purchasing cohort status panel renders", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-panel")).toBeVisible();
});

test("purchasing cohort status shows state badge", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-state")).toContainText(/Measurement ready|Measuring|Measured/);
});

test("purchasing instrument section always visible", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-instrument")).toBeVisible();
});

test("purchasing real section visible", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-real")).toBeVisible();
});

test("purchasing cohort-status endpoint returns valid shape", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/purchasing/cohort-status`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty("state");
  expect(body).toHaveProperty("instrument");
  expect(body).toHaveProperty("real");
  expect(states).toContain(body.state);
});

test("purchasing no synthetic lift displayed", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-panel")).not.toContainText(/lift.*\d+.*sample|sample.*lift/i);
});

test("purchasing no INSUFFICIENT_DATA message", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-panel")).not.toContainText(/insufficient|no data|not enough/i);
});

test("purchasing no console errors on cohort panel", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoPanel(page);
  const unexpected = errors.filter((error) => !/favicon|ResizeObserver|Failed to load/i.test(error));
  expectNoConsoleErrors(unexpected);
});
