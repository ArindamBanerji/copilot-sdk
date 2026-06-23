import { test, expect } from "@playwright/test";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

const BACKEND = process.env.S2P_BACKEND || "http://127.0.0.1:8002";
const states = ["INSTRUMENT_VALIDATED", "ACCUMULATING", "MEASURED"];

async function gotoPanel(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Evidence");
  await waitForAppShell(page);
  await expect(page.getByTestId("cohort-status-panel")).toBeVisible({ timeout: 20_000 });
}

test("S2P cohort status panel renders", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-panel")).toBeVisible();
});

test("S2P cohort status shows state badge", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-state")).toContainText(/Measurement ready|Measuring|Measured/);
});

test("S2P instrument section always visible", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-instrument")).toBeVisible();
});

test("S2P real section visible", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-real")).toBeVisible();
});

test("S2P cohort-status endpoint returns valid shape", async ({ request }) => {
  const response = await request.get(`${BACKEND}/api/s2p/cohort-status`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty("state");
  expect(body).toHaveProperty("instrument");
  expect(body).toHaveProperty("real");
  expect(states).toContain(body.state);
});

test("S2P no synthetic lift displayed", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-panel")).not.toContainText(/lift.*\d+.*sample|sample.*lift/i);
});

test("S2P no INSUFFICIENT_DATA message", async ({ page }) => {
  await gotoPanel(page);
  await expect(page.getByTestId("cohort-status-panel")).not.toContainText(/insufficient|no data|not enough/i);
});

test("S2P no console errors on cohort panel", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await gotoPanel(page);
  const unexpected = errors.filter((error) => !/favicon|ResizeObserver|Failed to load|Failed to fetch|same key|unique.*key/i.test(error));
  expectNoConsoleErrors(unexpected);
});
