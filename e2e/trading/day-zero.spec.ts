import { test, expect } from "@playwright/test";
import { clickTab, waitForAppShell } from "../helpers/ui";

test.beforeEach(async ({ request }) => {
  const response = await request.get("http://127.0.0.1:8010/health", { timeout: 5_000 }).catch(() => null);
  test.skip(!response?.ok(), "Trading backend not running");
});

async function gotoDashboard(page: import("@playwright/test").Page) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await waitForAppShell(page);
  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
}

async function mockMeasurementState(page: import("@playwright/test").Page, payload: object) {
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
