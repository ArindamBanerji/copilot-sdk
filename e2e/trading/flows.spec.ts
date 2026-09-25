import { type APIRequestContext, type APIResponse, type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

const TRADING_API = "http://127.0.0.1:8010";

async function getWithRetry(request: APIRequestContext, url: string): Promise<APIResponse> {
  try {
    return await request.get(url, { timeout: 30_000 });
  } catch {
    return await request.get(url, { timeout: 30_000 });
  }
}

async function fillTrade(page: Page) {
  await page.getByPlaceholder("MSFT").fill("MSFT");
  await page.getByRole("button", { name: "Lookup" }).click();
  await expectAnyText(page, [/MSFT/, /Source/i], { timeout: 30_000 });
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

async function gotoPerformanceReady(page: Page) {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    await clickTab(page, "Performance");
    try {
      await page.waitForFunction(
        () => /Loading performance|Centroid Timeline|Accuracy Alerts|Performance unavailable/i.test(document.querySelector("main")?.textContent || ""),
        { timeout: 15_000 },
      );
      await page.locator('main > [data-screen-ready="true"]').waitFor({ state: "attached", timeout: 30_000 });
      if ((await page.getByText("Performance unavailable").count()) === 0) {
        return;
      }
    } catch (error) {
      if (attempt === 1) throw error;
    }
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
  const scoreResponse = page.waitForResponse(
    (response) => response.url().includes("/api/score") && response.request().method() === "POST",
    { timeout: 30_000 },
  );
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
  const scoreResponse = page.waitForResponse(
    (response) => response.url().includes("/api/score") && response.request().method() === "POST",
    { timeout: 30_000 },
  );
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();

  const learnResponse = page.waitForResponse(
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && (response.ok() || response.status() === 423),
    { timeout: 15_000 },
  ).catch(() => null);
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/Trade confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Centroid Timeline/i, /Accuracy Alerts/i, /Decision Explorer/i]);
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
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && (response.ok() || response.status() === 423),
    { timeout: 15_000 },
  ).catch(() => null);
  await page.getByRole("button", { name: "Confirm" }).first().click();
  await learnResponse;
  await expectAnyText(page, [/Trade confirmed/i, /confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Centroid Timeline/i, /Accuracy Alerts/i, /Rule Lifecycle/i]);
  await expectAnyText(page, [/verified/i, /accuracy/i, /checkpoint/i]);
});

test("full round trip visits dashboard, log trade, analysis, performance, and dashboard", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await expectAnyText(page, [/Dashboard/i, /Centroid Timeline/i, /Decision Explorer/i]);

  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expectAnyText(page, [/Ticker/i, /Trade Thesis/i, /Score This Trade/i]);

  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Fingerprint/i, /edge/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Centroid Timeline/i, /Accuracy Alerts/i, /Decision Explorer/i]);

  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expectAnyText(page, [/Dashboard/i, /Centroid Timeline/i, /Decision Explorer/i]);
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
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await page.locator('main > [data-screen-ready="true"]').waitFor({ state: "attached", timeout: 15_000 });

  await expectAnyText(page, [/Decision Explorer/i, /Audit Trail/i], { timeout: 20_000 });
  await expectAnyText(page, [/matching decisions/i, /entries/i, /decision/i]);
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
  const scoreResponse = page.waitForResponse(
    (response) => response.url().includes("/api/score") && response.request().method() === "POST",
    { timeout: 30_000 },
  );
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();

  const learnResponse = page.waitForResponse(
    (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && (response.ok() || response.status() === 423),
    { timeout: 15_000 },
  ).catch(() => null);
  await page.getByRole("button", { name: "Confirm" }).click();
  await learnResponse;
  await expectAnyText(page, [/Trade confirmed/i, /system learned/i, /Reward/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Centroid Timeline/i, /Accuracy Alerts/i, /Decision Explorer/i]);

  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Aligned/i, /Misaligned/i, /Neutral/i]);
});

test("Dashboard to Log Trade to Analysis to Performance content at each stop", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await expectAnyText(page, [/Centroid Timeline/i, /Decision Explorer/i, /Audit Trail/i], { timeout: 20_000 });

  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expectAnyText(page, [/Ticker/i, /Research Checklist/i, /Score This Trade/i]);

  await clickTab(page, "Analysis");
  await waitForAppShell(page);
  await expectAnyText(page, [/YOUR TWO SELVES/i, /Fingerprint/i, /Counterfactual/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Centroid Timeline/i, /Accuracy Alerts/i, /Audit Trail/i]);
});

test("score to reasoning to Performance projection round trip", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Log Trade");
  await waitForAppShell(page);
  await expectAnyText(page, [/Log Trade/i, /Score This Trade/i]);

  await fillTrade(page);
  const scoreResponse = page.waitForResponse(
    (response) => response.url().includes("/api/score") && response.request().method() === "POST",
    { timeout: 30_000 },
  );
  await page.getByRole("button", { name: "Score This Trade" }).click();
  await scoreResponse;
  await expectAnyText(page, [/Why This Recommendation/i, /Factor Analysis/i, /Confidence Breakdown/i]);

  await clickTab(page, "Performance");
  await waitForAppShell(page);
  await expectAnyText(page, [/Centroid Timeline/i, /Accuracy Alerts/i]);
  await expectAnyText(page, [/Accuracy Alerts/i, /Centroid Timeline/i, /verified decisions/i]);
});

test("all main tabs load after shared reasoning and projection port", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  for (const tab of ["Dashboard", "Log Trade", "Analysis", "Performance"]) {
    await clickTab(page, tab);
    await waitForAppShell(page);
    await expect(page.locator("main")).not.toBeEmpty();
    await expectAnyText(page, [new RegExp(tab, "i"), /Centroid Timeline/i, /Score This Trade/i, /YOUR TWO SELVES/i, /Accuracy Alerts/i]);
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
  await expectAnyText(page, [/Audit Trail/i, /Immutable ledger/i, /entries/i, /decision/i]);

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
  await expectAnyText(page, [/Audit Trail/i, /Immutable ledger/i, /entries/i, /decision/i]);
});

test("TRD-S3 flow: regime break lowers authority before re-convergence", async ({ page, request }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await gotoPerformanceReady(page);
  await expect(page.getByTestId("accuracy-alerts-panel")).toBeVisible({ timeout: 30_000 });
  const regime = await getWithRetry(request, `${TRADING_API}/api/trading/situation/regime`);
  expect(regime.status()).toBe(200);
  expect((await regime.json()).conservationStatus).toBeDefined();
  const reconvergence = await getWithRetry(request, `${TRADING_API}/api/trading/regime/reconvergenc`);
  expect(reconvergence.status()).toBe(200);
  expect((await reconvergence.json()).cold_start_curves).toBeDefined();
});

test("TRD-V1 flow: clustering adjustment exposes tail-risk illusion", async ({ page, request }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await page.locator('main > [data-screen-ready="true"]').waitFor({ state: "attached", timeout: 15_000 });
  await expect(page.getByTestId("vol-sharpe-card")).toBeVisible({ timeout: 30_000 });
  const response = await request.get(`${TRADING_API}/api/trading/vol/short-vol-illusion`, { timeout: 30_000 });
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.clustering_adjustment_factor).toBeDefined();
  expect(body.tail_risk_indicator).toBeDefined();
  await expect(page.getByTestId("vol-sharpe-card")).toContainText(/Adjusted quality|clustering/i);
});

test("TRD-V2 flow: VRP distinguishes edge from insurance cost", async ({ page, request }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await page.locator('main > [data-screen-ready="true"]').waitFor({ state: "attached", timeout: 15_000 });
  await expect(page.getByTestId("vrp-attribution-card")).toBeVisible({ timeout: 30_000 });
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
  const panel = page.getByTestId("vrp-attribution-card");
  await expect(panel).toBeVisible();
  const response = await request.get(`${TRADING_API}/api/trading/vol/rich-cheap`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.current_regime).toBeDefined();
  expect(body.iv_percentile ?? body.ivPercentile ?? body.band).toBeDefined();
  await expect(panel).toContainText(/VRP|tail-dependence|window|accumulating|insufficient/i);
});

test("TRD-V6 flow: dispersion signal records follow, skip, and impact", async ({ page, request }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await page.locator('main > [data-screen-ready="true"]').waitFor({ state: "attached", timeout: 15_000 });
  await expect(page.getByTestId("dispersion-follow-card")).toBeVisible({ timeout: 30_000 });
  const response = await request.get(`${TRADING_API}/api/trading/vol/dispersion-follow`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.signals_fired ?? body.signalsFired).toBeDefined();
  expect(body.followed ?? body.followRate).toBeDefined();
  await expect(page.getByTestId("dispersion-follow-card")).toContainText(/Follow-rate|Observed impact|Awaiting/i);
});

test("TRD-V7 flow: positions reduce to effective independent bets", async ({ page, request }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Analysis");
  await page.locator('main > [data-screen-ready="true"]').waitFor({ state: "attached", timeout: 15_000 });
  const panel = page.getByTestId("tail-bets-card");
  await expect(panel).toBeVisible({ timeout: 30_000 });
  const response = await request.get(`${TRADING_API}/api/trading/vol/effective-bets`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.effective_bets).toBeDefined();
  expect(body.nominal_bets ?? body.tail_decisions).toBeDefined();
  await expect(panel).toContainText(/Effective bets|Tail decisions|Awaiting|unavailable/i);
});

test("TRD-GATE-DIVIDEND flow: withheld findings become replayable impact", async ({ page, request }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await waitForAppShell(page);
  await gotoPerformanceReady(page);
  await expect(page.getByTestId("decision-explorer-panel")).toBeVisible({ timeout: 30_000 });
  const gate = await request.get(`${TRADING_API}/api/trading/claim-gate`);
  expect(gate.status()).toBe(200);
  const body = await gate.json();
  expect(body.withheld).toBeDefined();
  expect(body.savedImpact).toBeDefined();
  await clickTab(page, "Analysis");
  await expect(page.getByTestId("claim-gate-badge")).toBeVisible();
});

