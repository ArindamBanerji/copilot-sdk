import { expect, test } from "../fixtures/copilot-fixture";
import { clickTab } from "../helpers/ui";

async function gotoTradingTab(page: import("@playwright/test").Page, tab: string) {
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60_000 });
  await clickTab(page, tab);
}

test.describe("Trading new surfaces", () => {
  test.describe.configure({ timeout: 90_000 });

  test("Rejection Moment renders its counters and reason area", async ({ page }) => {
    await gotoTradingTab(page, "Performance");
    const panel = page.getByTestId("rejection-moment-panel");
    await expect(panel).toBeVisible({ timeout: 60_000 });
    await expect(panel).toContainText(/Rejection Moment|Tested|Promoted|Rejected/i);
    await expect(panel).toContainText(/Recent rejections|Recent promotions/i);
  });

  test("Counterfactual panel renders its perturbation control", async ({ page }) => {
    await gotoTradingTab(page, "Analysis");
    const panel = page.getByTestId("counterfactual-card");
    await expect(panel).toBeVisible({ timeout: 60_000 });
    await expect(panel.getByTestId("counterfactual-factor-slider")).toBeVisible({ timeout: 60_000 });
  });

  test("Day-zero panel exposes measurement state and provenance", async ({ page }) => {
    await gotoTradingTab(page, "Dashboard");
    const panel = page.getByTestId("day-zero-card");
    await expect(panel).toBeVisible({ timeout: 60_000 });
    await expect(panel).toContainText(/Instrument Calibrated|Accumulating Evidence|Measured|Measurement State/i);
    await expect(panel).toContainText(/Instrument|Accumulating|Learned/i);
  });

  test("evolution summary exposes the telemetry contract", async ({ request }) => {
    const response = await request.get("http://127.0.0.1:8010/api/self/evolution/summary");
    expect(response.status()).toBe(200);
    const payload = await response.json();
    expect(payload.schema_version).toBe(1);
    expect(payload.evolution_enabled).toBeDefined();
    expect(payload.recent_events).toBeDefined();
  });

  test("diagnostics, conservation, transfers, and history endpoints respond", async ({ request }) => {
    const diagnostics = await request.get("http://127.0.0.1:8010/api/self/diagnostics");
    expect(diagnostics.status()).toBe(200);
    const diagnosticPayload = await diagnostics.json();
    expect(diagnosticPayload.epsilon_firm).toBeDefined();
    expect(diagnosticPayload.iks).toBeDefined();
    expect(diagnosticPayload.measurement_state).toBeDefined();

    const conservation = await request.get("http://127.0.0.1:8010/api/conservation/status");
    expect(conservation.status()).toBe(200);
    const conservationPayload = await conservation.json();
    expect(conservationPayload.status).toBeDefined();
    expect(typeof conservationPayload.reason).toBe("string");
    expect(conservationPayload.headroom).toBeDefined();

    const transfers = await request.get("http://127.0.0.1:8010/api/self/transfers");
    expect(transfers.status()).toBe(200);
    expect(Array.isArray((await transfers.json()).transfers)).toBe(true);

    const history = await request.get("http://127.0.0.1:8010/api/self/centroid-history?limit=1");
    expect(history.status()).toBe(200);
    expect((await history.json()).checkpoints).toBeDefined();
  });

  test("measurement spine flow crosses Dashboard, Analysis, and Performance", async ({ page }) => {
    await gotoTradingTab(page, "Dashboard");
    await expect(page.getByTestId("day-zero-card")).toBeVisible({ timeout: 60_000 });
    await gotoTradingTab(page, "Analysis");
    await expect(page.getByTestId("counterfactual-card")).toBeVisible({ timeout: 60_000 });
    await gotoTradingTab(page, "Performance");
    await expect(page.getByTestId("rejection-moment-panel")).toBeVisible({ timeout: 60_000 });
  });
});
