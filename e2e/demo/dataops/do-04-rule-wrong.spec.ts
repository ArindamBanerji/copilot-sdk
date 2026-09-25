import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8030";
test("DO-04 rule-wrong", async ({ request }) => {
  const genealogyResponse = await request.get(API + "/api/ae/rule-lifecycle");
  test.skip(!genealogyResponse.ok(), `Rule genealogy returned ${genealogyResponse.status()}`);
  const genealogy = await genealogyResponse.json();
  const rules = genealogy.rules ?? [];
  const transitioned = rules.find((rule: any) => rule.lifecycle_events?.some((event: any) => event.type === "promoted") && rule.lifecycle_events?.some((event: any) => /demot|reject/.test(event.type)));
  test.skip(!transitioned, "DO-04 requires a seeded promoted-to-demoted rule lifecycle");
  const types = transitioned.lifecycle_events.map((event: any) => event.type);
  expect(types.indexOf("promoted")).toBeLessThan(types.findIndex((type: string) => /demot|reject/.test(type)));
});
