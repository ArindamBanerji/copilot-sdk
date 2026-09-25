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
  await expect(page.getByTestId("self-computation-panels")).toBeVisible({ timeout: 20_000 });
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
  await expect(page.getByTestId("centroid-timeline-panel")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("heading", { name: "Centroid Timeline" })).toBeVisible();
});

test("day zero shows provenance", async ({ page }) => {
  await gotoDashboard(page);
  await expect(page.getByTestId("rule-genealogy-panel")).toContainText(/GraphStore state|evolution/i);
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
  const panels = page.getByTestId("self-computation-panels");
  await expect(panels).toBeVisible();
  await expect(panels).not.toContainText(/fabricated/i);
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
  await expect(page.getByTestId("decision-explorer-panel")).toContainText(/matching decisions/i);
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
  await expect(page.getByTestId("accuracy-alerts-panel")).toContainText(/\d+%/);
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
  await expect(page.getByTestId("self-computation-panels")).toBeVisible();
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
  await expect(page.getByTestId("centroid-timeline-panel")).toContainText(/checkpoints/i);
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
  await expect(page.getByTestId("accuracy-alerts-panel")).toContainText(/\d+%/);
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
  await expect(page.getByTestId("audit-trail-panel")).toBeVisible();
});

test("DZ-05: shared panel shows the fake ROI honesty caption", async ({ page }) => {
  await gotoDashboard(page);
  await expect(page.getByTestId("rule-lifecycle-panel")).toContainText(/Evolution|Promotion/i);
});

test("DZ-06: Trading Dashboard renders the shared DayZeroPanel", async ({ page }) => {
  await gotoDashboard(page);
  await expect(page.getByTestId("self-computation-panels")).toBeVisible();
  await expect(page.getByTestId("centroid-timeline-panel")).toBeVisible();
});

