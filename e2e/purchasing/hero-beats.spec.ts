import { expect, test } from "../fixtures/copilot-fixture";
import { clickTab, waitForScreenReady } from "../helpers/ui";

async function openTab(page: import("@playwright/test").Page, tab: string) {
  await page.goto("/");
  await waitForScreenReady(page);
  await clickTab(page, tab);
  await waitForScreenReady(page);
}

test("PM-01: gated signal reliability renders", async ({ page }) => {
  await openTab(page, "Analysis");
  await expect(page.getByTestId("gated-signal-reliability-panel")).toBeVisible();
});

test("PM-02: gated signal panel uses kitchen language", async ({ page }) => {
  await openTab(page, "Analysis");
  const panel = page.getByTestId("gated-signal-reliability-panel");
  await expect(panel).toContainText(/Kitchen|supplier|delivery|waste/i);
  await expect(panel).not.toContainText(/trap|padding|stress|fraud/i);
});

test("PM-03: mirror open shows correction survival", async ({ page }) => {
  await openTab(page, "Analysis");
  await expect(page.getByTestId("mirror-open-panel")).toContainText(/supplier|Survived correction/i);
});

test("PM-04: proof ledger renders two curves", async ({ page }) => {
  await openTab(page, "Performance");
  const panel = page.getByTestId("proof-ledger-panel");
  await expect(panel).toBeVisible();
  await expect(panel.getByTestId("proof-curve")).toBeVisible();
  await expect(panel.getByTestId("competence-curve")).toBeVisible();
});

test("PM-05: proof ledger supports a zero-dollar week", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("proof-ledger-zero-week")).toContainText(/\$0|zero/i);
});

test("PM-06: self-pause shows manager drift state", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("self-pause-panel")).toContainText(/authority|Conservation|Monitoring|paused/i);
});

test("PM-07: time-to-competence ramp renders", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("time-to-competence-panel")).toContainText(/Last GM|This kitchen|competence/i);
  await expect(page.getByTestId("competence-ramp")).toBeVisible();
});

test("PM-08: not-yet panel renders honest empty state", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  const panel = page.getByTestId("not-yet-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(/Not yet|supplier factor|incremental|Coverage/i);
});

test("PM-09: continuity close renders retained judgment", async ({ page }) => {
  await openTab(page, "Performance");
  await expect(page.getByTestId("continuity-close-panel")).toContainText(/Everything in this kitchen|Judgment retained/i);
});

test("PM-10: Purchasing hero surfaces are present across the flow", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await expect(page.getByTestId("not-yet-panel")).toBeVisible();
  await clickTab(page, "Analysis");
  await waitForScreenReady(page);
  await expect(page.getByTestId("mirror-open-panel")).toBeVisible();
  await expect(page.getByTestId("gated-signal-reliability-panel")).toBeVisible();
  await clickTab(page, "Performance");
  await waitForScreenReady(page);
  await expect(page.getByTestId("proof-ledger-panel")).toBeVisible();
  await expect(page.getByTestId("continuity-close-panel")).toBeVisible();
});
