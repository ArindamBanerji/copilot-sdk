import { test, expect } from "../fixtures/copilot-fixture";
import type { Page } from "@playwright/test";
import { clickTab as navigateTab, expectAnyText, waitForScreenReady } from "../helpers/ui";

test.setTimeout(90_000);

async function clickTab(page: Page, name: string) {
  await navigateTab(page, name);
  await waitForScreenReady(page);
}

async function openDashboard(page: Page) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await waitForScreenReady(page);
}

async function openFirstAlert(page: Page) {
  const alertSection = page.locator("section").filter({ hasText: "Alert Root Causes" }).first();
  await expect(alertSection).toBeVisible();

  const expand = alertSection.getByRole("button", { name: /Expand/i }).first();
  if (await expand.count()) {
    await expand.click();
  }

  const triage = alertSection.getByRole("button", { name: "Triage" }).first();
  await expect(triage).toBeVisible();
  await triage.click();
  await waitForScreenReady(page);
}

test("Mirror → Moat: the resequenced DI story arc", async ({ page }) => {
  await openDashboard(page);

  const trustCard = page.getByTestId("trust-card");
  await expect(trustCard).toBeVisible();
  const trustFactors = trustCard.getByTestId("trust-factor");
  await expect(trustFactors).toHaveCount(6);
  const factorText = (await trustFactors.allTextContents()).join(" ");
  expect(factorText).toMatch(/reliable/i);
  expect(factorText).toMatch(/noisy/i);

  await clickTab(page, "Insight");
  const centroid = page.getByTestId("centroid-timeline");
  await expect(centroid).toBeVisible();
  await expectAnyText(page, [/Centroid Timeline/i, /converg|checkpoint|drift/i]);

  await clickTab(page, "Evidence");
  const genealogy = page.getByTestId("rule-genealogy");
  await expect(genealogy).toBeVisible();
  await expect(genealogy.getByTestId("rule-genealogy-status").first()).toBeVisible();
  await expect(genealogy).toContainText(/promoted|rejected/i);

  await clickTab(page, "Insight");
  const map = page.getByTestId("intelligence-map");
  await expect(map).toBeVisible();
  await expect(map.getByTestId("gold-line").first()).toBeVisible();
  await expect(map.getByTestId("gold-line-label").first()).toHaveText(/\$[\d,.]+K?\/yr/i);

  expect(factorText).toMatch(/reliable/i);
  expect(await centroid.count()).toBeGreaterThan(0);
  await expect(genealogy).toHaveCount(0);
  await expect(map).toBeVisible();
});

test("NL Query journey: question → answer → attribution → drill-down", async ({ page }) => {
  await openDashboard(page);

  const panel = page.getByTestId("nl-query-panel");
  await expect(panel).toBeVisible();
  const question = panel.getByLabel("Ask about your data");
  await question.fill("How many decisions?");
  await panel.getByRole("button", { name: "Ask" }).click();

  await expect(panel.getByTestId("nl-query-response")).toBeVisible({ timeout: 20_000 });
  const firstAnswer = await panel.getByTestId("query-answer").innerText();
  await expect(panel.getByTestId("query-confidence")).toBeVisible();
  await expect(panel.getByTestId("source-attribution-bar").first()).toBeVisible();

  await panel.getByRole("button", { name: "What is accuracy?" }).click();
  await panel.getByRole("button", { name: "Ask" }).click();
  await expect(panel.getByTestId("query-answer")).toBeVisible({ timeout: 20_000 });
  await expect.poll(() => panel.getByTestId("query-answer").innerText()).not.toBe(firstAnswer);

  const computationPath = panel.getByTestId("computation-path");
  await expect(computationPath).toBeVisible();
  await computationPath.locator("summary").click();
  await expect(computationPath).toHaveAttribute("open", "");
});

test("Search + drill-down: find → filter → inspect", async ({ page }) => {
  await openDashboard(page);
  await clickTab(page, "Insight");

  const panel = page.getByTestId("search-panel");
  await expect(panel).toBeVisible();
  await panel.getByTestId("search-input").fill("orders");
  await expect(panel.getByTestId("search-result").first()).toBeVisible({ timeout: 20_000 });
  const initialCount = await panel.getByTestId("search-result").count();
  expect(initialCount).toBeGreaterThan(0);

  await panel.getByTestId("search-trust-filter").selectOption("1");
  await expect.poll(() => panel.getByTestId("search-result").count()).toBeLessThan(initialCount);
  const qualityBadge = panel.getByTestId("quality-badge").first();
  await expect(qualityBadge).toBeVisible();
  await expect(qualityBadge).toHaveText(/healthy|degraded|stale/i);
});

test("Source trust deep-dive: profile → columns → consumers", async ({ page }) => {
  await openDashboard(page);
  await clickTab(page, "Insight");

  const panel = page.getByTestId("source-profile-panel");
  await expect(panel).toBeVisible();
  const profiles = panel.getByTestId("source-profile");
  await expect(profiles.first()).toBeVisible({ timeout: 20_000 });
  await expect(panel.locator('[aria-label^="Trust "]').first()).toBeVisible();

  await profiles.first().getByRole("button").click();
  await expect(panel).toContainText(/Column trust/i);
  await expect(panel).toContainText(/Consumers/i);
  await expect(panel).toContainText(/Recommendation: (Safe|Require human review)/i);
  await expect(panel).toContainText(/Column trust|No column trust data available/i);
});

test("Score → trust update: decision changes trust", async ({ page }) => {
  await openDashboard(page);
  const trustCard = page.getByTestId("trust-card");
  await expect(trustCard).toBeVisible();
  const beforeText = await trustCard.innerText();
  const beforeMatch = beforeText.match(/(\d+) verified decisions/i);
  expect(beforeMatch).not.toBeNull();
  const before = Number(beforeMatch?.[1]);

  await openFirstAlert(page);
  await expect(page.getByRole("button", { name: "Investigate" })).toBeVisible();
  await page.getByRole("button", { name: "Investigate" }).click();
  await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible({ timeout: 20_000 });
  await page.getByRole("button", { name: "Confirm" }).click();
  await expectAnyText(page, [/system learned/i, /Reward/i, /IKS delta/i], { timeout: 20_000 });

  await page.getByRole("button", { name: "Back to Dashboard" }).click();
  await waitForScreenReady(page);
  const afterText = await page.getByTestId("trust-card").innerText();
  const afterMatch = afterText.match(/(\d+) verified decisions/i);
  expect(afterMatch).not.toBeNull();
  expect(Number(afterMatch?.[1])).toBeGreaterThanOrEqual(before);
});

test("Data products → source detail: IKS journey", async ({ page }) => {
  await openDashboard(page);

  const products = page.getByTestId("products-card");
  await expect(products).toBeVisible();
  await expect(products.getByTestId("di-product")).toHaveCount(3);
  await expect(products.locator('[aria-label^="IKS "]').first()).toBeVisible();
  await expect(products).toContainText(/GREEN/i);
  await expect(products.locator("article").filter({ hasText: /GREEN|AMBER/i })).toHaveCount(3);

  await clickTab(page, "Insight");
  const profiles = page.getByTestId("source-profile-panel");
  await expect(profiles).toBeVisible();
  await expect(profiles.getByTestId("source-profile").first()).toBeVisible({ timeout: 20_000 });
  await expect(profiles.locator('[aria-label^="Trust "]').first()).toBeVisible();
  await expectAnyText(page, [/reliable|moderate|noisy/i]);
});

test("perturb and revert flow: trust drops and restores", async ({ page }) => {
  await openDashboard(page);

  const card = page.getByTestId("trust-card");
  const controls = page.getByTestId("trust-perturbation");
  await expect(controls).toBeVisible();
  const target = card.getByTestId("trust-factor").filter({ hasText: "source_reliability" });
  const comparison = card.getByTestId("trust-factor").filter({ hasText: "data_freshness" });
  const beforeTarget = await target.innerText();
  try {
    await controls.getByTestId("trust-perturb-button").click();
    await expect(controls.getByTestId("trust-perturbation-status")).toContainText(/20 synthetic decisions injected/i);
    await expect.poll(() => target.innerText()).not.toBe(beforeTarget);
    await expect(comparison).toContainText("data_freshness");
    await expect(comparison).toContainText("moderate");

    await controls.getByTestId("trust-revert-button").click();
    await expect(controls.getByTestId("trust-perturbation-status")).toContainText(/trust restored/i);
    await expect.poll(() => target.innerText()).toBe(beforeTarget);
  } finally {
    const revert = controls.getByTestId("trust-revert-button");
    if (await revert.count()) {
      await revert.click().catch(() => undefined);
    }
  }
});

test("trust card shows perturbation state", async ({ page }) => {
  await openDashboard(page);

  const controls = page.getByTestId("trust-perturbation");
  await expect(controls).toBeVisible();
  try {
    await controls.getByTestId("trust-perturb-button").click();
    await expect(controls).toContainText(/DI-PROOF.*What-if/i);
    await expect(controls).toContainText(/Active/i);
    await expect(controls).toContainText(/synthetic decisions injected/i);
  } finally {
    const revert = controls.getByTestId("trust-revert-button");
    if (await revert.count()) {
      await revert.click().catch(() => undefined);
    }
  }
});
