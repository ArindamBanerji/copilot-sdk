import { expect, test, type Page } from "@playwright/test";

const BACKEND = process.env.S2P_BACKEND ?? "http://127.0.0.1:8002";

test.beforeEach(async ({ request }) => {
  const response = await request.get(`${BACKEND}/health`, { timeout: 5_000 }).catch(() => null);
  test.skip(!response?.ok(), "S2P backend not running");
});

async function gotoDashboard(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

async function mockMeasurementState(page: Page, payload: object) {
  await page.route("**/api/s2p/measurement-state", async (route) => {
    await route.fulfill({ contentType: "application/json", json: payload });
  });
}

test("S2P dashboard shows the day-zero card", async ({ page }) => {
  await gotoDashboard(page);
  const card = page.getByTestId("day-zero-card");
  await expect(card).toBeVisible();
  await expect(card.getByRole("heading", { name: /Instrument Calibrated|Accumulating Evidence|Measured|Measurement State/i })).toBeVisible();
});

test("S2P day-zero state avoids magnitude claims and uses plain language", async ({ page }) => {
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
  await expect(card).toContainText("No magnitude claims yet.");
  await expect(card).toContainText("This is what honest looks like on day one.");
  await expect(card.getByText(/^Accuracy$/i)).toHaveCount(0);
  await expect(card.getByText(/^IKS$/i)).toHaveCount(0);
  await expect(card.getByText(/\d+(\.\d+)?%/)).toHaveCount(0);
  await expect(card).not.toContainText(/sample|fabricated/i);
});

test("S2P measured state shows accuracy and IKS", async ({ page }) => {
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
  await expect(card.getByText("84.0%")).toBeVisible();
  await expect(card.getByText(/^IKS$/i)).toBeVisible();
});
