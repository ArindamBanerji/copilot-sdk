import { expect, test, type Page } from "@playwright/test";
import { clickTab, collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";
import {
  assertLearnSuccess,
  clickScoreAndValidate,
  expectLearningResultOrStableControls,
  panel,
  recommendationControls,
  scoreResultPanel,
  waitForS2PLearnResponse,
  waitForTriageQueue,
} from "./helpers";

test.setTimeout(180_000);

function main(page: Page) {
  return page.locator("main");
}

async function scoreFirstInvoice(page: Page) {
  await clickTab(page, "Exception Triage");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
  await waitForTriageQueue(page, 60_000);
  await clickScoreAndValidate(page);
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
  expect(graphStatus.sqlite_authoritative).toBeFalsy();
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
  const [learnResponse] = await Promise.all([
    waitForS2PLearnResponse(page),
    recommendationControls(page).getByRole("button", { name: /Confirm recommendation/i }).click(),
  ]);
  await assertLearnSuccess(learnResponse);
  await expectLearningResultOrStableControls(page, /Reward|confirm|recorded/i);

  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(main(page)).toContainText(/Exception Queue|Conservation Status/i);
  await expect(main(page)).not.toContainText(/shadow.*error|cutover.*failed|AGE.*failed|Traceback|Unhandled/i);
  await expect(main(page)).not.toContainText(/migration complete|historical.*migrated|product cutover/i);

  expectNoConsoleErrors(errors.filter((error) => !/422 \(Unprocessable Entity\)/i.test(error)));
});
