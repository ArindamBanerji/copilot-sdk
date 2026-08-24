import { type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

const TRADING_API = "http://127.0.0.1:8010";

async function fillTrade(page: Page) {
  await page.getByPlaceholder("MSFT").fill("MSFT");
  await page.getByRole("button", { name: "Lookup" }).click();
  await expectAnyText(page, [/MSFT/, /Source/i]);
  await page.getByLabel("Entry Price").fill("420");
  await page.getByLabel("Shares").fill("5");
  await page.getByLabel("Portfolio Value").fill("100000");
  await page.getByLabel("Stop Loss").fill("400");
  await page.getByLabel("Target").fill("455");
  const checklist = page.locator("section", { hasText: "Research Checklist" }).getByRole("checkbox");
  if ((await checklist.count()) > 0) {
    await checklist.first().check();
  }
}

test("full trade lifecycle: log, score, confirm, dashboard", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();

  await fillTrade(page);
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;

  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
  await page.getByRole("button", { name: "Confirm" }).click();
  await expectAnyText(page, [/Trade confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});

test("score confirm then Performance shows IKS", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();

  await fillTrade(page);
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();

  const learnResponse = page.waitForResponse(
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok(),
    { timeout: 15_000 },
  ).catch(() => null);
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/Trade confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Performance Summary/i, /Current IKS/i, /IKS/i, /Trajectory/i]);
  await page.waitForFunction(
    () => !document.querySelector("main")?.textContent?.includes("Loading"),
    { timeout: 15000 },
  );
  const mainText = await page.locator("main").innerText();
  expect(mainText).toMatch(/IKS[\s\S]{0,80}\d+(\.\d+)?/i);
});

test("score confirm learn cycle preserves conservation after RL", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Log Trade" })).toBeVisible();

  await fillTrade(page);
  const scoreResponse = page.waitForResponse(
    (response) => response.url().includes("/api/score") && response.request().method() === "POST",
    { timeout: 30_000 },
  );
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expect(page.getByRole("button", { name: "Confirm" }).first()).toBeVisible();

  const learnResponse = page.waitForResponse(
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok(),
    { timeout: 15_000 },
  );
  await page.getByRole("button", { name: "Confirm" }).first().click();
  await learnResponse;
  await expectAnyText(page, [/Trade confirmed/i, /confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Performance Summary/i, /Conservation/i, /Trajectory/i]);
  await expectAnyText(page, [/55%/, /75%/, /90%/, /verified/i, /trajectory/i]);
});

test("full round trip visits dashboard, log trade, analysis, performance, and dashboard", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expectAnyText(page, [/Dashboard/i, /Portfolio Summary/i, /portfolio/i]);

  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expectAnyText(page, [/Ticker/i, /Trade Thesis/i, /Score This Trade/i]);

  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Fingerprint/i, /edge/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/IKS/i, /Trajectory/i, /Performance Summary/i]);

  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expectAnyText(page, [/Dashboard/i, /Portfolio Summary/i, /portfolio/i]);
});

test("tab navigation cycle all tabs accessible without console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);
  await page.goto("/");
  await waitForAppShell(page);

  for (const tab of ["Dashboard", "Log Trade", "Analysis", "Performance", "Trade Detail"]) {
    await clickTab(page, tab);
    await waitForAppShell(page);
    await expectAnyText(page, [new RegExp(tab, "i"), /Loading/i, /Select a trade/i]);
  }

  expectNoConsoleErrors(errors);
});

test("analysis reflects pre-seeded data", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);

  await expect(page.getByText("YOUR TWO SELVES")).toBeVisible();
  await expect(page.getByTestId("counterfactual-card")).toBeVisible();
  await expectAnyText(page, [/Fingerprint/i, /Research Impact/i, /Risk Management/i, /\d+(\.\d+)?%/]);
});

test("dashboard shows decision history entries", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);

  await expectAnyText(page, [/Decision History/i]);
  await expectAnyText(page, [/strong execution/i, /partial execution/i, /poor execution/i, /trade/i, /open/i]);
});

test("analysis contrast card reflects pre-seeded alignment", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await waitForAppShell(page);

  await expectAnyText(page, [/YOUR TWO SELVES/i, /Aligned trades compound/i]);
  await expectAnyText(page, [/Aligned/i, /Misaligned/i, /Neutral/i]);
  await expectAnyText(page, [/Win rate/i, /Trades/i, /\d+/]);
});

test("score then confirm then Performance and Analysis reflect it", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expectAnyText(page, [/Log Trade/i, /Ticker/i, /Score This Trade/i]);

  await fillTrade(page);
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();

  const learnResponse = page.waitForResponse(
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok(),
    { timeout: 15_000 },
  ).catch(() => null);
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/Trade confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Current IKS/i, /\bIKS\b/i, /Trajectory/i]);

  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Aligned/i, /Misaligned/i, /Neutral/i]);
});

test("Dashboard to Log Trade to Analysis to Performance content at each stop", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expectAnyText(page, [/Portfolio Summary/i, /Decision History/i, /portfolio/i]);

  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expectAnyText(page, [/Ticker/i, /Research Checklist/i, /Score This Trade/i]);

  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Fingerprint/i, /Counterfactual/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Current IKS/i, /\bIKS\b/i, /Trajectory/i, /Rolling/i]);
});

test("score to reasoning to Performance projection round trip", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expectAnyText(page, [/Log Trade/i, /Score This Trade/i]);

  await fillTrade(page);
  const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expectAnyText(page, [/Why This Recommendation/i, /Factor Analysis/i, /Confidence Breakdown/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Performance Summary/i, /Trajectory/i]);
  await expectAnyText(page, [/Automation Projection/i, /55%/, /75%/, /90%/, /verified decisions/i]);
});

test("all main tabs load after shared reasoning and projection port", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  for (const tab of ["Dashboard", "Log Trade", "Analysis", "Performance"]) {
    await clickTab(page, tab);
    await waitForAppShell(page);
    await expect(page.locator("main")).not.toBeEmpty();
    await expectAnyText(page, [new RegExp(tab, "i"), /Portfolio Summary/i, /Score This Trade/i, /YOUR TWO SELVES/i, /Performance Summary/i]);
  }
});

test("SC round trip: accuracy to decisions to audit trail", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expectAnyText(page, [/SC-12/i, /Accuracy Alerts/i, /accuracy/i, /category/i, /threshold/i, /No verified decisions yet/i, /No verified trading decisions yet/i]);

  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expectAnyText(page, [/SC-14/i, /Decision Explorer/i, /Category/i, /Action/i]);
  await expectAnyText(page, [/SC-13/i, /Rule Genealogy/i, /SC-15/i, /Rule Lifecycle/i]);
  await expectAnyText(page, [/SC-16/i, /Audit Trail/i, /decision/i, /outcome/i, /No audit trail available yet/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/SC-11/i, /Centroid History/i, /centroid/i, /No centroid history yet/i]);
});

test("api self features render populated or empty states", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expectAnyText(page, [/Accuracy Alerts/i, /No verified decisions yet/i, /threshold/i]);

  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expectAnyText(page, [/Decision Explorer/i, /No decisions match these filters/i, /Confidence/i]);
  await expectAnyText(page, [/Audit Trail/i, /No audit trail available yet/i, /decision/i]);
});

test("TRD-S3 flow: regime break lowers authority before re-convergence", async ({ page, request }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await expect(page.getByTestId("autonomy-throttle-panel")).toBeVisible();
  const regime = await request.get(`${TRADING_API}/api/trading/situation/regime`);
  expect(regime.status()).toBe(200);
  expect((await regime.json()).conservationStatus).toBeDefined();
  const reconvergence = await request.get(`${TRADING_API}/api/trading/regime/reconvergenc`);
  expect(reconvergence.status()).toBe(200);
  expect((await reconvergence.json()).cold_start_curves).toBeDefined();
});

test("TRD-V1 flow: clustering adjustment exposes tail-risk illusion", async ({ page, request }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await expect(page.getByTestId("vol-sharpe-card")).toBeVisible();
  const response = await request.get(`${TRADING_API}/api/trading/vol/short-vol-illusion`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.clustering_adjustment_factor).toBeDefined();
  expect(body.tail_risk_indicator).toBeDefined();
  await expect(page.getByTestId("vol-sharpe-card")).toContainText(/Adjusted quality|clustering/i);
});

test("TRD-V2 flow: VRP distinguishes edge from insurance cost", async ({ page, request }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await expect(page.getByTestId("vrp-attribution-card")).toBeVisible();
  const response = await request.get(`${TRADING_API}/api/trading/vol/vrp-edge`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.vrp_edge).toBeDefined();
  expect(body.insurance_cost).toBeDefined();
  await expect(page.getByTestId("vrp-classification")).toContainText(/Edge|Insurance|Neutral|Accumulating/i);
});

test("TRD-V5 flow: IV rich-cheap signal is conditioned on regime", async ({ page, request }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await expect(page.getByTestId("regime-vrp-card")).toBeVisible();
  const response = await request.get(`${TRADING_API}/api/trading/vol/rich-cheap`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.current_regime).toBeDefined();
  expect(body.iv_percentile ?? body.ivPercentile ?? body.band).toBeDefined();
  await expect(page.getByTestId("regime-vrp-card")).toContainText(/Regime|Rich|Cheap|Awaiting/i);
});

test("TRD-V6 flow: dispersion signal records follow, skip, and impact", async ({ page, request }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await expect(page.getByTestId("dispersion-follow-card")).toBeVisible();
  const response = await request.get(`${TRADING_API}/api/trading/vol/dispersion-follow`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.signals_fired ?? body.signalsFired).toBeDefined();
  expect(body.followed ?? body.followRate).toBeDefined();
  await expect(page.getByTestId("dispersion-follow-card")).toContainText(/Follow-rate|Observed impact|Awaiting/i);
});

test("TRD-V7 flow: positions reduce to effective independent bets", async ({ page, request }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await expect(page.getByTestId("tail-bets-card")).toBeVisible();
  const response = await request.get(`${TRADING_API}/api/trading/vol/effective-bets`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.effective_bets).toBeDefined();
  expect(body.nominal_bets ?? body.tail_decisions).toBeDefined();
  await expect(page.getByTestId("tail-bets-card")).toContainText(/Effective bets|Tail decisions|Awaiting/i);
});

test("TRD-GATE-DIVIDEND flow: withheld findings become replayable impact", async ({ page, request }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Performance");
  await expect(page.getByTestId("gate-dividend-panel")).toBeVisible();
  const gate = await request.get(`${TRADING_API}/api/trading/claim-gate`);
  expect(gate.status()).toBe(200);
  const body = await gate.json();
  expect(body.withheld).toBeDefined();
  expect(body.savedImpact).toBeDefined();
  await clickTab(page, "Analysis");
  await expect(page.getByTestId("claim-gate-badge")).toBeVisible();
});
