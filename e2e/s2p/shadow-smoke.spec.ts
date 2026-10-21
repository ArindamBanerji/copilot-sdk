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
  await waitForTriageQueue(page);
  await clickScoreAndValidate(page);
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
  await expect(main(page)).not.toContainText(/shadow.*error|AGE shadow.*failed|Traceback|Unhandled/i);

  expectNoConsoleErrors(errors.filter((error) => !/422 \(Unprocessable Entity\)/i.test(error)));
});
