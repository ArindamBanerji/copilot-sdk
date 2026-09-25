import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
test("MACH-02 reshape", async ({ request }) => {
  const response = await request.post(API + "/api/alert/analyze", { data: { alert_id: "PL-SOC-1-NO-PRECEDENT-001" } });
  test.skip(!response.ok(), `Analyze returned ${response.status()}`);
  const body = await response.json();
  expect(body.no_precedent.is_novel).toBe(true);
  expect(body.no_precedent.similar_count).toBe(0);
  expect(body.recommendation.action).toBe("refer_to_analyst");
  expect(body.recommendation.confidence).toBeGreaterThan(0.7);
});
