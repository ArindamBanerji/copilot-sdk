import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8010";
test("PLAT-05 two-questions", async ({ request }) => {
  const response = await request.get(API + "/api/platform/concepts/two-questions");
  test.skip(!response.ok(), `Concepts endpoint returned ${response.status()}`);
  const body = await response.json();
  expect(body.concept_id).toBe("two-questions");
  expect(body.content.questions).toHaveLength(2);
  expect(body.content.questions[0].question).toMatch(/surface tell/i);
  expect(body.content.questions[1].question).toMatch(/investigation change/i);
  expect(body.content.source).toMatch(/K14.*240/i);
});
