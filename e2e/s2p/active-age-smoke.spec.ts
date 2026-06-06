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

async function scoreFirstInvoice(page: Page) {
  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
  await expect(panel(page, "Invoice Selector")).toContainText(/S2P-INV|queued/i);
  await panel(page, "Selected Invoice").getByRole("button", { name: /^Score$/i }).click();
  await expect(scoreResultPanel(page)).toContainText(/Recommendation|Confidence/i);
}

test("S2P active AGE test-mode smoke keeps UI flows working", async ({ page, request }) => {
  const errors = collectConsoleErrors(page);

  const health = await request.get("http://127.0.0.1:8002/health");
  expect(health.ok()).toBeTruthy();
  const status = await request.get("http://127.0.0.1:8002/api/s2p/graph/status");
  expect(status.ok()).toBeTruthy();
  const graphStatus = await status.json();
  expect(graphStatus.active_backend).toBe("age");
  expect(graphStatus.age_active).toBe(true);
  expect(graphStatus.sqlite_authoritative).toBe(false);
  expect(graphStatus.active_graph_name).toMatch(/^protocol_v2_test/);
  expect(graphStatus.active_graph_name).not.toBe("soc_graph");
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
  await recommendationControls(page).getByRole("button", { name: /Confirm recommendation/i }).click();
  await expect(panel(page, "Learning Result")).toContainText(/Reward|confirm|recorded/i, { timeout: 15_000 });

  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(main(page)).toContainText(/Exception Queue|Conservation Status/i);
  await expect(main(page)).not.toContainText(/shadow.*error|cutover.*failed|AGE.*failed|Traceback|Unhandled/i);
  await expect(main(page)).not.toContainText(/migration complete|historical.*migrated|product cutover/i);

  expectNoConsoleErrors(errors);
});
