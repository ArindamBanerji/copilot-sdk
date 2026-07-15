import type { APIRequestContext, Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { PURCHASING_FACTORS } from "../fixtures/purchasing-factors";
import { clickTab, waitForAppShell } from "../helpers/ui";

const API_BASE = "http://127.0.0.1:8020";
const ACTIONS = ["order_as_planned", "order_more", "order_less", "skip"];

async function scoreDecision(request: APIRequestContext) {
  const response = await request.post(`${API_BASE}/api/score`, {
    data: { category: "protein", factors: PURCHASING_FACTORS },
  });
  expect(response.status()).toBe(200);
  return response.json();
}

function differentAction(action: string) {
  return ACTIONS.find((candidate) => candidate !== action) ?? "order_as_planned";
}

async function scoreInUi(page: Page) {
  const scoreButton = page.getByRole("button", { name: "Score This Order" });
  await expect(scoreButton).toBeEnabled({ timeout: 20_000 });
  const response = page.waitForResponse(
    (r) => r.url().includes("/api/score") && r.request().method() === "POST" && r.ok(),
  );
  await scoreButton.click();
  await response;
}

test("Verify confirms a decision", async ({ request }) => {
  const scored = await scoreDecision(request);
  const response = await request.post(`${API_BASE}/api/purchasing/verify`, {
    data: {
      decision_id: scored.decision_id,
      actual_action: scored.action,
      reason_code: "supplier_preference",
    },
  });

  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data).toHaveProperty("conservation_status");
  expect(data).toHaveProperty("is_override");
  expect(data.is_override).toBe(false);
});

test("Verify override marks is_override true", async ({ request }) => {
  const scored = await scoreDecision(request);
  const response = await request.post(`${API_BASE}/api/purchasing/verify`, {
    data: {
      decision_id: scored.decision_id,
      actual_action: differentAction(scored.action),
      reason_code: "price_override",
    },
  });

  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.is_override).toBe(true);
});

test("Verify invalid decision returns 404", async ({ request }) => {
  const response = await request.post(`${API_BASE}/api/purchasing/verify`, {
    data: {
      decision_id: "NONEXISTENT",
      actual_action: "order_as_planned",
      reason_code: "other",
    },
  });

  expect(response.status()).toBe(404);
});

test("Verify invalid reason code returns 400", async ({ request }) => {
  const scored = await scoreDecision(request);
  const response = await request.post(`${API_BASE}/api/purchasing/verify`, {
    data: {
      decision_id: scored.decision_id,
      actual_action: "order_as_planned",
      reason_code: "INVALID_CODE",
    },
  });

  expect(response.status()).toBe(400);
});

test("Double verify returns 409", async ({ request }) => {
  const scored = await scoreDecision(request);
  await request.post(`${API_BASE}/api/purchasing/verify`, {
    data: {
      decision_id: scored.decision_id,
      actual_action: scored.action,
      reason_code: "supplier_preference",
    },
  });
  const response = await request.post(`${API_BASE}/api/purchasing/verify`, {
    data: {
      decision_id: scored.decision_id,
      actual_action: scored.action,
      reason_code: "supplier_preference",
    },
  });

  expect(response.status()).toBe(409);
});

test("Reason codes endpoint returns 7 codes", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/verify/reason-codes`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.count).toBe(7);
});

test("Verify kitchen language in reason codes", async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/purchasing/verify/reason-codes`);
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.count).toBe(7);
  const text = JSON.stringify(data);
  expect(text).not.toContain("Vendor");
  expect(text).not.toContain("PurchaseOrder");
});

test("Reason selector visible after scoring", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Order");
  await scoreInUi(page);

  await expect(page.getByTestId("reason-selector")).toBeVisible({ timeout: 20_000 });
});

test("Conservation status shown after verify", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Order");
  await scoreInUi(page);

  await page.getByTestId("reason-selector").selectOption("supplier_preference");
  const response = page.waitForResponse(
    (r) => r.url().includes("/api/purchasing/verify") && r.request().method() === "POST" && r.ok(),
  );
  await page.getByRole("button", { name: "Confirm" }).click();
  await response;

  await expect(page.getByTestId("verify-conservation")).toBeVisible({ timeout: 20_000 });
});
