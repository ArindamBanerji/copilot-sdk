import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell, waitForScreenReady } from "../helpers/ui";

type TrustFactor = { name?: unknown; weight?: unknown; dk_weight?: unknown };

function trustLevel(weight: number): "high" | "medium" | "low" {
  if (weight > 0.7) return "high";
  if (weight >= 0.3) return "medium";
  return "low";
}

function selectedTrustLevels(factors: TrustFactor[]) {
  const sorted = factors
    .map((factor) => Number(factor.dk_weight ?? factor.weight))
    .filter((weight) => Number.isFinite(weight))
    .sort((left, right) => right - left);
  const selected = sorted.length <= 5 ? sorted : [...sorted.slice(0, 3), ...sorted.slice(-2)];
  return selected.map(trustLevel);
}

test("dashboard loads without blank screen", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expect(page.getByRole("heading", { name: "Trading Copilot" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.locator("main")).not.toBeEmpty();
});

test("shows portfolio summary", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expect(page.getByText("Centroid Timeline")).toBeVisible();
  await expect(page.getByText(/open positions/i).first()).toBeVisible();
  await expect(page.getByText("Win Rate", { exact: true }).first()).toBeVisible();
  await expectAnyText(page, [/\$\d[\d,]*/, /\d+(\.\d+)?%/, /-/]);
});

test("IKS is visible with numeric value", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expect(page.getByText("IKS").first()).toBeVisible();
  await expect(page.getByLabel(/^IKS \d+$/).first()).toBeVisible();
});

test("shows graph-backed decision context", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expect(page.getByTestId("decision-explorer-panel")).toBeVisible();
  await expect(page.getByTestId("rule-lifecycle-panel")).toBeVisible();
});

test("shows graph-backed dashboard panels", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expect(page.getByTestId("centroid-timeline-panel")).toBeVisible();
  await expect(page.getByTestId("accuracy-alerts-panel")).toBeVisible();
  await expect(page.getByTestId("decision-explorer-panel")).toBeVisible();
});

test("paper badge is visible", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);

  await expectAnyText(page, [/paper/i, /with fingerprint/i, /without/i]);
  await clickTab(page, "Dashboard");
  await waitForScreenReady(page);
  await waitForAppShell(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});

test("graph-backed trust context is visible on dashboard", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await expect(page.getByTestId("decision-explorer-panel")).toBeVisible();
  await expect(page.getByTestId("audit-trail-panel")).toBeVisible();
});

test("fingerprint endpoint exposes learned factors", async ({ page }) => {
  const fingerprint = await page.request.get("http://127.0.0.1:8010/api/fingerprint");
  expect(fingerprint.status()).toBe(200);
  const body = await fingerprint.json();
  expect(Array.isArray(body.factors)).toBeTruthy();
  expect(body.factors.length).toBeGreaterThan(0);
});

test("fingerprint factors include trust weights", async ({ request }) => {
  const fingerprint = await request.get("http://127.0.0.1:8010/api/fingerprint");
  expect(fingerprint.status()).toBe(200);
  const levels = selectedTrustLevels(((await fingerprint.json()).factors ?? []) as TrustFactor[]);
  expect(levels.length).toBeGreaterThan(0);
});

test("dashboard shows graph-backed factor contrast panels", async ({ page }) => {
  await page.goto("/");
  await waitForScreenReady(page);
  await expect(page.getByTestId("accuracy-alerts-panel")).toBeVisible();
  await expect(page.getByTestId("rule-lifecycle-panel")).toBeVisible();
});

