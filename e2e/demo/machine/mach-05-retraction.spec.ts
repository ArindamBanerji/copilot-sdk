import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8010";
test("MACH-05 retraction", async ({ request }) => {
  const response = await request.get(API + "/api/platform/concepts/retraction-list");
  test.skip(!response.ok(), `Concepts endpoint returned ${response.status()}`);
  const body = await response.json();
  expect(body.concept_id).toBe("retraction-list");
  expect(body.content.retractions.length).toBeGreaterThan(0);
  expect(body.content.retractions.map((item: any) => item.status)).toEqual(expect.arrayContaining(["WITHDRAWN", "HYPOTHESIS", "CORRECTED"]));
  expect(body.content.retractions.every((item: any) => item.reason && item.experiment)).toBe(true);
});
