import { test, expect } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";

test.beforeEach(async ({ request }) => {
  const response = await request.get("http://127.0.0.1:8010/health", { timeout: 5_000 }).catch(() => null);
  test.skip(!response?.ok(), "Trading backend not running");
});

async function gotoDashboard(page: import("@playwright/test").Page) {
  // The day-zero contract is independent of live market connectivity. Keep
  // this spec deterministic when the local provider cannot reach its source.
  await page.route("**/api/context/market-snapshot", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        source: "e2e",
        asOf: "2026-01-01T00:00:00Z",
        spy: { ticker: "SPY", price: 500, change30dPct: 1.2 },
        vix: { ticker: "VIX", value: 16.5, price: 16.5 },
        sectors: [],
        provenance: "e2e",
      },
    });
  });
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await waitForAppShell(page);
  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expect(page.getByTestId("day-zero-state")).toHaveText(/INSTRUMENT_VALIDATED|ACCUMULATING|MEASURED/, { timeout: 20_000 });
}

async function mockMeasurementState(page: import("@playwright/test").Page, payload: object) {
  await page.route("**/api/health", async (route) => {
    await route.fulfill({ contentType: "application/json", json: { phase: (payload as { state?: string }).state, measurement_state: payload } });
  });
  await page.route("**/api/conservation/status", async (route) => {
    const state = payload as { state?: string; decisions_verified?: number; accuracy?: number | null; iks?: number | null };
    await route.fulfill({
      contentType: "application/json",
      json: {
        verified_count: state.decisions_verified ?? 0,
        status: state.state === "measured" ? "GREEN" : "AMBER",
        q: state.accuracy ?? 0,
        iks: state.iks ?? null,
      },
    });
  });
  await page.route("**/api/trading/measurement-state", async (route) => {
    await route.fulfill({ contentType: "application/json", json: payload });
  });
}

test("day zero card visible on dashboard", async ({ page }) => {
  await gotoDashboard(page);
  await expect(page.getByTestId("day-zero-card")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("heading", { name: /Instrument Calibrated|Accumulating Evidence|Measured|Measurement State/i })).toBeVisible();
});

test("day zero shows provenance", async ({ page }) => {
  await gotoDashboard(page);
  const card = page.getByTestId("day-zero-card");
  await expect(card.getByText(/Instrument|Accumulating|Learned/i).first()).toBeVisible({ timeout: 20_000 });
});

test("instrument state has no fabricated magnitude and uses plain language", async ({ page }) => {
  await mockMeasurementState(page, {
    state: "instrument_validated",
    decisions_verified: 0,
    decisions_needed: 30,
    arms_measured: 0,
    arms_total: 6,
    accuracy: null,
    iks: null,
    message: "Instrument calibrated. Awaiting first verified decision.",
    provenance: "instrument",
  });
  await gotoDashboard(page);
  const card = page.getByTestId("day-zero-card");
  await expect(card.getByRole("heading", { name: "Instrument Calibrated" })).toBeVisible();
  await expect(card).toContainText("No magnitude claims yet.");
  await expect(card).toContainText("This is what honest looks like on day one.");
  await expect(card.getByText(/^Accuracy$/i)).toHaveCount(0);
  await expect(card.getByText(/^IKS$/i)).toHaveCount(0);
  await expect(card.getByText(/\d+(\.\d+)?%/)).toHaveCount(0);
  await expect(card).not.toContainText(/sample|fabricated/i);
});

test("accumulating state shows verified decision progress", async ({ page }) => {
  await mockMeasurementState(page, {
    state: "accumulating",
    decisions_verified: 12,
    decisions_needed: 18,
    arms_measured: 1,
    arms_total: 6,
    accuracy: null,
    iks: null,
    message: "Accumulating evidence.",
    provenance: "accumulating",
  });
  await gotoDashboard(page);
  await expect(page.getByTestId("day-zero-card")).toContainText("12 / 30 decisions");
});

test("measured state shows accuracy and IKS", async ({ page }) => {
  await mockMeasurementState(page, {
    state: "measured",
    decisions_verified: 60,
    decisions_needed: 0,
    arms_measured: 6,
    arms_total: 6,
    accuracy: 0.84,
    iks: 74.2,
    message: "Measured on verified decisions.",
    provenance: "real_measured",
  });
  await gotoDashboard(page);
  const card = page.getByTestId("day-zero-card");
  await expect(card.getByText(/^Accuracy$/i)).toBeVisible();
  await expect(card.getByText("84.0%")).toBeVisible();
  await expect(card.getByText(/^IKS$/i)).toBeVisible();
});

test("DZ-01: shared panel renders instrument-validated state", async ({ page }) => {
  await mockMeasurementState(page, {
    state: "instrument_validated",
    decisions_verified: 0,
    decisions_needed: 30,
    accuracy: null,
    iks: null,
    provenance: "instrument",
  });
  await gotoDashboard(page);
  const panel = page.getByTestId("day-zero-panel");
  await expect(panel).toBeVisible();
  await expect(panel.getByTestId("day-zero-state")).toHaveText("INSTRUMENT_VALIDATED");
  await expect(panel.getByTestId("measurement-step-instrument_validated")).toHaveAttribute("data-state", "current");
});

test("DZ-02: shared panel renders accumulating state", async ({ page }) => {
  await mockMeasurementState(page, {
    state: "accumulating",
    decisions_verified: 12,
    decisions_needed: 18,
    accuracy: null,
    iks: null,
    provenance: "accumulating",
  });
  await gotoDashboard(page);
  const panel = page.getByTestId("day-zero-panel");
  await expect(panel.getByTestId("day-zero-state")).toHaveText("ACCUMULATING");
  await expect(panel).toContainText("Accumulating. 12 decisions verified. Building judgment.");
});

test("DZ-03: shared panel renders measured state", async ({ page }) => {
  await mockMeasurementState(page, {
    state: "measured",
    decisions_verified: 60,
    decisions_needed: 0,
    accuracy: 0.84,
    iks: 74.2,
    provenance: "real_measured",
  });
  await gotoDashboard(page);
  const panel = page.getByTestId("day-zero-panel");
  await expect(panel.getByTestId("day-zero-state")).toHaveText("MEASURED");
  await expect(panel).toContainText("Measured. IKS = 74.2. Conservation GREEN.");
});

test("DZ-04: shared panel shows evidence tier badge", async ({ page }) => {
  await mockMeasurementState(page, {
    state: "measured",
    decisions_verified: 60,
    decisions_needed: 0,
    accuracy: 0.84,
    iks: 74.2,
    provenance: "real_measured",
  });
  await gotoDashboard(page);
  await expect(page.getByTestId("day-zero-evidence-tier")).toContainText("T_O");
});

test("DZ-05: shared panel shows the fake ROI honesty caption", async ({ page }) => {
  await gotoDashboard(page);
  await expect(page.getByTestId("day-zero-caption")).toContainText(/fake ROI/i);
});

test("DZ-06: Trading Dashboard renders the shared DayZeroPanel", async ({ page }) => {
  await gotoDashboard(page);
  await expect(page.getByTestId("day-zero-panel")).toBeVisible();
  await expect(page.getByText(/V6 · DZ-1 · Day-zero honesty/i)).toBeVisible();
});
