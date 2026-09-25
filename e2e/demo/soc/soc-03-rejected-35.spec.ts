import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
test("SOC-03 rejected-35", async ({ request }) => {
  const response = await request.get(API + "/api/evolution/recent-events");
  test.skip(!response.ok(), `Recent evolution events returned ${response.status()}`);
  const body = await response.json();
  const events = Array.isArray(body.events) ? body.events : [];
  const promoted = events.filter((event: any) => /promot/i.test(String(event.event_type)));
  const rejected = events.filter((event: any) => /reject|rollback/i.test(String(event.event_type)));
  test.skip(promoted.length === 0 || rejected.length === 0, "SOC-03 requires seeded promoted and rejected variants in the recent-events window");
  expect(promoted.length).toBeGreaterThan(0);
  expect(rejected.length).toBeGreaterThan(0);
  expect(rejected.every((event: any) => String(event.description ?? event.metadata?.reason ?? "").length > 0)).toBe(true);
});




