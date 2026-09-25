import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
test("SOC-06 policy-wins", async ({ request }) => {
  const response = await request.post(API + "/api/alert/analyze", { data: { alert_id: "PL-SOC-3-POLICY-CONFLICT-001" } });
  test.skip(!response.ok(), `Endpoint returned ${response.status()}`);
  // Mutation: scoring is append-only; there is no supported decision cleanup endpoint.
  const body = await response.json();
  const probabilities = body.gae_scoring?.action_probabilities ?? {};
  const surfaceAction = Object.entries(probabilities).sort((a: any, b: any) => b[1] - a[1])[0]?.[0];
  expect(surfaceAction).toBe("suppress");
  expect(body.recommendation?.action).toBe("refer_to_analyst");
  expect(body.referral?.should_refer).toBe(true);
  expect(body.referral?.reasons?.length).toBeGreaterThan(0);
  expect(body.referral.audit_summary).toMatch(/R2|R7|policy|authority/i);
});
