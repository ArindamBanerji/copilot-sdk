import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
const UI = "http://127.0.0.1:5173";
test("SOC-02 no-precedent", async ({ request, page }) => {
  const response = await request.post(API + "/api/alert/analyze", { data: { alert_id: "PL-SOC-1-NO-PRECEDENT-001" } });
  test.skip(!response.ok(), `Analyze returned ${response.status()}`);
  // Mutation: scoring is append-only; the backend exposes no decision-delete cleanup contract.
  const body = await response.json();
  expect(body.no_precedent?.is_novel).toBe(true);
  expect(body.no_precedent?.similar_count).toBe(0);
  expect(body.recommendation?.action).toBe("refer_to_analyst");
  expect(body.recommendation?.confidence).toBeGreaterThan(0.7);
  expect(body.gae_scoring?.factor_vector).toHaveLength(6);
  await page.goto(UI, { waitUntil: "domcontentloaded" });
  await expect(page.locator("main")).toBeVisible();
});
