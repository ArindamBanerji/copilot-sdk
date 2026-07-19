import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

const BACKEND = process.env.TRADING_BACKEND || "http://127.0.0.1:8010";

const factors = {
  signal_alignment: 0.7,
  market_regime: 0.6,
  position_sizing: 0.65,
  timing_quality: 0.55,
  risk_reward_actual: 0.7,
  emotional_indicator: 0.45,
  signal_confidence: 0.6,
  options_delta_exposure: 0.5,
  options_iv_percentile: 0.5,
  options_gamma_risk: 0.5,
};

async function openLogTrade(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();
}

test("pre-score panel renders on Log Trade screen", async ({ page }) => {
  await openLogTrade(page);

  await expect(page.getByTestId("pre-score-panel")).toBeVisible({ timeout: 20_000 });
});

test("preview button exists", async ({ page }) => {
  await openLogTrade(page);

  await expect(page.getByTestId("pre-score-button")).toBeVisible({ timeout: 20_000 });
});

test("pre-score endpoint returns valid response", async ({ request }) => {
  const response = await request.post(`${BACKEND}/api/trading/pre-score`, {
    data: { category: "trend_following", factors },
  });
  expect(response.status()).toBe(200);
  const body = await response.json();

  expect(body).toHaveProperty("recommended_action");
  expect(body).toHaveProperty("confidence");
  expect(body).toHaveProperty("similar_trades");
  expect(body).toHaveProperty("category_accuracy");
  expect(body).toHaveProperty("warning");
});

test("pre-score endpoint rejects invalid category", async ({ request }) => {
  const response = await request.post(`${BACKEND}/api/trading/pre-score`, {
    data: { category: "invalid", factors },
  });

  expect(response.status()).toBe(400);
});

test("pre-score endpoint rejects missing factors", async ({ request }) => {
  const response = await request.post(`${BACKEND}/api/trading/pre-score`, {
    data: { category: "trend_following", factors: {} },
  });

  expect(response.status()).toBe(400);
});

test("pre-score endpoint returns no decision", async ({ request }) => {
  const response = await request.post(`${BACKEND}/api/trading/pre-score`, {
    data: { category: "trend_following", factors },
  });
  expect(response.status()).toBe(200);
  const body = await response.json();

  expect(body.preview).toBe(true);
  expect(body.message).toMatch(/no decision recorded/i);
  expect(body).not.toHaveProperty("decision_id");
});

test("preview indicator shows non-recording message", async ({ page }) => {
  await openLogTrade(page);

  await expect(page.getByTestId("pre-score-indicator")).toContainText(/preview|no decision/i);
});

test("similar trades section renders", async ({ page }) => {
  await openLogTrade(page);

  const response = page.waitForResponse((item) => item.url().includes("/api/trading/pre-score") && item.request().method() === "POST");
  await page.getByTestId("pre-score-button").click();
  await response;

  await expect(page.getByTestId("pre-score-similar")).toBeVisible({ timeout: 20_000 });
});

test("accuracy stat displayed", async ({ page }) => {
  await openLogTrade(page);

  const response = page.waitForResponse((item) => item.url().includes("/api/trading/pre-score") && item.request().method() === "POST");
  await page.getByTestId("pre-score-button").click();
  await response;

  await expect(page.getByTestId("pre-score-accuracy")).toBeVisible({ timeout: 20_000 });
});

test("no console errors on pre-score panel", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await openLogTrade(page);
  await expect(page.getByTestId("pre-score-panel")).toBeVisible({ timeout: 20_000 });

  expectNoConsoleErrors(errors);
});
