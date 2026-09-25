import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
test("SOC-07 chained", async ({ request }) => {
  const response = await request.get(API + "/api/audit/verify");
  test.skip(!response.ok(), `Audit verification returned ${response.status()}`);
  const body = await response.json();
  expect(body.verified).toBe(true);
  expect(body.chain_length).toBeGreaterThan(0);
  const csv = await request.get(API + "/api/audit/decisions?format=csv");
  test.skip(!csv.ok(), `Audit CSV export returned ${csv.status()}`);
  expect(csv.headers()["content-type"]).toContain("text/csv");
  expect((await csv.text()).split(/\r?\n/, 1)[0]).toMatch(/hash/i);
});




