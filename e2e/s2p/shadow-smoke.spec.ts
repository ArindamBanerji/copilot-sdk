import { expect, test, type Page } from "@playwright/test";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";

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

function scoreResultPanel(page: Page) {
  return page.locator("article", { hasText: "Action index" });
}

function recommendationControls(page: Page) {
  return page.locator("article", { has: page.getByRole("button", { name: /Confirm recommendation/i }) });
}

function waitForScoreResponse(page: Page) {
  return page.waitForResponse((response) =>
    response.url().includes("/score") &&
    response.request().method() === "POST" &&
    response.status() === 200
  );
}

function waitForLearnResponse(page: Page) {
  return page.waitForResponse((response) =>
    (response.url().includes("/api/learn") || response.url().includes("/api/s2p/outcome")) &&
    response.request().method() === "POST" &&
    response.ok()
  );
}

async function ensureSelectedInvoice(page: Page) {
  const selected = panel(page, "Selected Invoice");
  if (!(await selected.getByText(/Supplier|Amount|Category/i).count())) {
    const invoiceButtons = panel(page, "Invoice Selector").getByRole("button").filter({ hasText: /S2P-INV/i });
    if ((await invoiceButtons.count()) > 0) {
      await invoiceButtons.first().click();
    }
  }
  await expect(selected).toContainText(/Supplier|Amount|Category/i, { timeout: 20_000 });
}

async function expectLearningResultOrStableControls(page: Page) {
  const learning = panel(page, "Learning Result");
  try {
    await expect(learning).toContainText(/Reward|confirm|recorded/i, { timeout: 15_000 });
  } catch {
    await expect(recommendationControls(page)).toBeVisible();
    await expect(main(page)).not.toContainText(/Traceback|Unhandled|500 Internal/i);
  }
}

async function scoreFirstInvoice(page: Page) {
  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
  await expect(panel(page, "Invoice Selector")).toContainText(/S2P-INV|queued/i);
  await ensureSelectedInvoice(page);
  const selected = panel(page, "Selected Invoice");
  const scoreButton = selected.getByRole("button", { name: /^Score$/i });
  await expect(scoreButton).toBeEnabled({ timeout: 20_000 });
  await Promise.all([
    waitForScoreResponse(page),
    scoreButton.click(),
  ]);
  await expect(scoreResultPanel(page)).toContainText(/Recommendation|Confidence/i);
}

test("S2P AGE shadow smoke keeps UI flows working", async ({ page, request }) => {
  const errors = collectConsoleErrors(page);

  let health;
  try {
    health = await request.get("http://127.0.0.1:8002/health", { timeout: 5_000 });
  } catch {
    test.skip(true, "S2P backend health check timed out");
    return;
  }
  expect(health.ok()).toBeTruthy();

  const graphStatus = await request.get("http://127.0.0.1:8002/api/s2p/graph/status", { timeout: 5_000 }).catch(() => null);
  if (!graphStatus?.ok()) {
    test.skip(true, "S2P AGE graph status endpoint not available");
    return;
  }
  const graphPayload = await graphStatus.json();
  if (graphPayload.age_active !== true) {
    test.skip(true, "S2P AGE is not active");
    return;
  }

  await expect.poll(async () => (await request.get("/")).status()).toBe(200);

  await page.goto("/");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(panel(page, "Exception Queue")).toContainText(/exception/i);
  await expect(panel(page, "Conservation Status")).toContainText(/conservation|GREEN|AMBER|RED/i);

  await scoreFirstInvoice(page);
  await expect(scoreResultPanel(page)).toContainText(/auto approve|hold for review|escalate to buyer|flag leakage|refer to specialist/i);
  await Promise.all([
    waitForLearnResponse(page),
    recommendationControls(page).getByRole("button", { name: /Confirm recommendation/i }).click(),
  ]);
  await expectLearningResultOrStableControls(page);

  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(main(page)).toContainText(/Exception Queue|Conservation Status/i);
  await expect(main(page)).not.toContainText(/shadow.*error|AGE shadow.*failed|Traceback|Unhandled/i);

  expectNoConsoleErrors(errors.filter((error) => !/422 \(Unprocessable Entity\)/i.test(error)));
});
