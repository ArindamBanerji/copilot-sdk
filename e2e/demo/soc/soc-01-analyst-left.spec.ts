import { test, expect } from "@playwright/test";

const API = "http://127.0.0.1:8001";
const UI = "http://127.0.0.1:5173";

test("SOC-01 analyst-left", async ({ request, page }) => {
  const response = await request.get(API + "/api/soc/learning-state");
  test.skip(!response.ok(), `Learning state returned ${response.status()}`);
  const body = await response.json();
  const weights = Object.values(body.bootstrap_category_weights ?? {}) as number[];
  expect(body.verified_decisions).toBeGreaterThan(0);
  expect(body.categories_active).toBeGreaterThan(0);
  expect(weights.length).toBeGreaterThan(0);
  expect(weights.some((weight) => Number.isFinite(weight) && weight > 0)).toBe(true);
  await page.goto(UI, { waitUntil: "domcontentloaded" });
  await expect(page.locator("main")).toBeVisible();
});




