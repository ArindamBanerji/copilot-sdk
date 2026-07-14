import { test, expect } from "../fixtures/copilot-fixture";
import { collectConsoleErrors, clickTab, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

const BACKEND = process.env.DATAOPS_BACKEND || "http://127.0.0.1:8030";
const states = ["INSTRUMENT_VALIDATED", "ACCUMULATING", "MEASURED"];

async function gotoPanel(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Evidence");
  await waitForAppShell(page);
  await expect(page.getByTestId("cohort-status-panel")).toBeVisible({ timeout: 20_000 });
}

test("dataops cohort status panel renders", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-panel")).toBeVisible();
});

test("dataops cohort status shows state badge", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-state")).toContainText(/Measurement ready|Measuring|Measured/);
});

test("dataops instrument section always visible", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-instrument")).toBeVisible();
});

test("dataops real section visible", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-real")).toBeVisible();
});

test("dataops cohort-status endpoint returns valid shape", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/dataops/cohort-status`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty("state");
  expect(body).toHaveProperty("instrument");
  expect(body).toHaveProperty("real");
  expect(states).toContain(body.state);
});

test("dataops no synthetic lift displayed", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-panel")).not.toContainText(/lift.*\d+.*sample|sample.*lift/i);
});

test("dataops no INSUFFICIENT_DATA message", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-panel")).not.toContainText(/insufficient|no data|not enough/i);
});

test("dataops no console errors on cohort panel", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoPanel(page);
  const unexpected = errors.filter((error) => !/favicon|ResizeObserver|Failed to load/i.test(error));
  expectNoConsoleErrors(unexpected);
});
