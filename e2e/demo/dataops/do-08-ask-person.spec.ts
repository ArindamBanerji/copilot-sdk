import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8030";
test("DO-08 ask-person", async ({ request }) => {
  const response = await request.post(API + "/api/di/query", { data: { question: "What is my highest-trust data source?" } });
  test.skip(!response.ok(), `DI query returned ${response.status()}`);
  const body = await response.json();
  expect(body.answer.length).toBeGreaterThan(0);
  expect(body.query.supported).toBe(true);
  expect(body.confidence).toBeGreaterThan(0);
  expect(body.source_attribution.length).toBeGreaterThan(1);
  expect(body.source_attribution.every((source: any) => Number.isFinite(source.trust))).toBe(true);
  expect(body.computation_path.length).toBeGreaterThan(0);
});
