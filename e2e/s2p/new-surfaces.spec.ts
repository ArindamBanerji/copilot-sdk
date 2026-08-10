import { expect, test, type Page } from "@playwright/test";
import { clickTab } from "../helpers/ui";

const S2P_API = "http://127.0.0.1:8002";

async function requireS2P(page: Page) {
  const health = await page.request.get(`${S2P_API}/health`, { timeout: 5_000 }).catch(() => null);
  test.skip(!health?.ok(), "S2P backend is not running");
}

async function openScoredTriage(page: Page) {
  await requireS2P(page);
  await page.goto("/");
  await clickTab(page, "Exception Triage");
  await expect(page.getByRole("heading", { name: "Exception Triage" })).toBeVisible();
  const selected = page.locator("article").filter({ hasText: /Selected Invoice/i });
  await expect(selected).toContainText(/Supplier|Amount|Category/i, { timeout: 20_000 });
  const scoreResponse = page.waitForResponse(
    (response) => response.url().includes("/score") && response.request().method() === "POST" && response.status() === 200,
    { timeout: 30_000 },
  );
  await selected.getByRole("button", { name: /^Score$/i }).click();
  await scoreResponse;
  await expect(page.getByTestId("rule-vs-reasoning-panel")).toBeVisible({ timeout: 20_000 });
}

test.describe("S2P new surfaces", () => {
  test("Rule vs Reasoning contrast renders both decision columns", async ({ page }) => {
    await openScoredTriage(page);
    const panel = page.getByTestId("rule-vs-reasoning-panel");
    await expect(panel).toContainText(/Rule vs reasoning/i);
    await expect(panel).toContainText(/Rule-Based/i);
    await expect(panel).toContainText(/Situation-Aware/i);
  });

  test("S2P measurement endpoints return explainable payloads", async ({ page }) => {
    await requireS2P(page);
    const diagnostics = await page.request.get(`${S2P_API}/api/self/diagnostics`);
    expect(diagnostics.status()).toBe(200);
    expect((await diagnostics.json()).epsilon_firm).toBeDefined();

    const conservation = await page.request.get(`${S2P_API}/api/conservation/status`);
    expect(conservation.status()).toBe(200);
    const conservationPayload = await conservation.json();
    expect(conservationPayload.status).toBeDefined();
    expect(typeof conservationPayload.reason).toBe("string");

    const evolution = await page.request.get(`${S2P_API}/api/self/evolution/summary`);
    expect(evolution.status()).toBe(200);
    expect((await evolution.json()).schema_version).toBe(1);
  });

  test("S2P triage flow reaches governed contrast after scoring", async ({ page }) => {
    await openScoredTriage(page);
    await expect(page.getByTestId("situation-panel")).toBeVisible();
    await expect(page.getByTestId("rule-vs-reasoning-panel")).toContainText(/Confidence:|Situation reasoning/i);
  });
});
