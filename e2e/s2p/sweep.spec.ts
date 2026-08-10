import { test, expect } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";
import { waitForTriageQueue } from "./helpers";

const API = "http://127.0.0.1:8002";

async function openTab(page: import("@playwright/test").Page, name: string) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, name);
  await waitForAppShell(page);
}

async function openScoredTriage(page: import("@playwright/test").Page) {
  await openTab(page, "Exception Triage");
  await waitForTriageQueue(page);
  const selected = page.locator("article").filter({ hasText: /Selected Invoice/i });
  await expect(selected).toContainText(/Supplier|Amount|Category/i, { timeout: 20_000 });
  await selected.getByRole("button", { name: /^Score$/i }).click();
  await expect(page.getByTestId("rule-vs-reasoning-panel")).toBeVisible({ timeout: 20_000 });
}

test.describe("S2P sweep — point tests", () => {
  test("Exception Triage mounts rule-vs-reasoning and situation panels", async ({ page }) => {
    await openScoredTriage(page);
    await expect(page.getByTestId("rule-vs-reasoning-panel")).toBeVisible();
    await expect(page.getByTestId("rule-vs-reasoning-contrast")).toBeVisible();
    await expect(page.getByTestId("situation-panel")).toBeVisible();
  });

  test("Insight mounts centroid explorer", async ({ page }) => {
    await openTab(page, "Insight");
    await expect(page.getByText(/Decision proximity explanation|Centroid explorer/i).first()).toBeVisible();
  });

  test("Insight process fusion labels illustrative provenance", async ({ page }) => {
    await openTab(page, "Insight");
    await expect(page.getByTestId("process-fusion-panel")).toContainText(/Source: illustrative process events/i);
  });

  test("Evidence mounts audit, lifecycle, and compliance surfaces", async ({ page }) => {
    await openTab(page, "Evidence");
    await expect(page.getByText(/Audit trail|Rule lifecycle|compliance/i).first()).toBeVisible();
  });

  test("shared S2P endpoints expose explainable state", async ({ request }) => {
    const diagnostics = await request.get(`${API}/api/self/diagnostics`);
    const conservation = await request.get(`${API}/api/conservation/status`);
    const evolution = await request.get(`${API}/api/self/evolution/summary`);
    expect(diagnostics.status()).toBe(200);
    expect(conservation.status()).toBe(200);
    expect(evolution.status()).toBe(200);
    expect((await diagnostics.json()).epsilon_firm).toBeDefined();
    expect((await conservation.json()).reason).toBeDefined();
    expect((await evolution.json()).schema_version).toBe(1);
  });

  test("S2P control surfaces are reachable", async ({ request }) => {
    expect((await request.get(`${API}/api/self/trust-traps`)).status()).toBe(200);
    expect((await request.get(`${API}/api/s2p/preview/queue`)).status()).toBe(200);
    const health = await request.get(`${API}/health`);
    expect(health.status()).toBe(200);
  });
});

test.describe("S2P sweep — demo flows", () => {
  test("governed triage: Exception Triage → score → rule/reasoning contrast", async ({ page }) => {
    await openScoredTriage(page);
    await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
    await expect(page.getByTestId("rule-vs-reasoning-panel")).toBeVisible();
    await expect(page.getByTestId("rule-vs-reasoning-panel")).toContainText(/Rule-Based|Situation-Aware/i);
  });

  test("decision evidence: Insight → Evidence → supplier audit context", async ({ page }) => {
    await openTab(page, "Insight");
    await expect(page.getByText(/Decision proximity explanation|Centroid explorer/i).first()).toBeVisible();
    await clickTab(page, "Evidence");
    await waitForAppShell(page);
    await expect(page.getByText(/Audit trail|Rule lifecycle|Receipt chain|compliance/i).first()).toBeVisible();
  });

  test("full S2P tab navigation remains error-free", async ({ page }) => {
    await page.goto("/");
    for (const tab of ["Dashboard", "Exception Triage", "Insight", "Evidence", "Suppliers", "Performance"]) {
      await clickTab(page, tab);
      await waitForAppShell(page);
      await expect(page.locator("body")).not.toContainText(/Unhandled error|TypeError|Application error/i);
    }
  });
});
