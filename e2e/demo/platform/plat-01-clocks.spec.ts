import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8010";
test("PLAT-01 clocks", async ({ request }) => {
  const response = await request.get(API + "/api/platform/concepts/four-clocks");
  test.skip(!response.ok(), `Concepts endpoint returned ${response.status()}`);
  const body = await response.json();
  expect(body.concept_id).toBe("four-clocks");
  expect(body.content.clocks).toHaveLength(4);
  expect(body.content.clocks.map((clock: any) => clock.name)).toEqual(["State Clock", "Event Clock", "Decision Clock", "Insight Clock"]);
  expect(body.content.note).toMatch(/capital investment/i);
});
