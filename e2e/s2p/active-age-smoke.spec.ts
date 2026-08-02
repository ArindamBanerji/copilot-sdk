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

test("S2P active AGE test-mode smoke keeps UI flows working", async ({ page, request }) => {
  const errors = collectConsoleErrors(page);

  const health = await request.get("http://127.0.0.1:8002/health");
  expect(health.ok()).toBeTruthy();
  const status = await request.get("http://127.0.0.1:8002/api/s2p/graph/status");
  expect(status.ok()).toBeTruthy();
  const graphStatus = await status.json();
  test.skip(graphStatus.active_backend !== "age", `S2P backend is ${graphStatus.active_backend}, not AGE`);
  expect(graphStatus.active_backend).toBe("age");
  expect(graphStatus.age_active).toBe(true);
  expect(graphStatus.sqlite_authoritative).toBe(false);
  expect(["protocol_v2_test", "soc_graph"]).toContain(
    graphStatus.active_graph_name.replace(/_\d+$/, "")
  );
  expect(graphStatus.migration_backfill_status).toBe("not_in_scope");
  expect(graphStatus.receipt_mapping_status).toBe("excluded_first_cutover");
  expect(JSON.stringify(graphStatus)).not.toContain("postgres:postgres@");

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
  await expect(main(page)).not.toContainText(/shadow.*error|cutover.*failed|AGE.*failed|Traceback|Unhandled/i);
  await expect(main(page)).not.toContainText(/migration complete|historical.*migrated|product cutover/i);

  expectNoConsoleErrors(errors.filter((error) => !/422 \(Unprocessable Entity\)/i.test(error)));
});
