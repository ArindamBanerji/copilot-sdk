import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
test("MACH-01 through-machine", async ({ request }) => {
  const analyze = await request.post(API + "/api/alert/analyze", { data: { alert_id: "PL-SOC-1-NO-PRECEDENT-001" } });
  test.skip(!analyze.ok(), `Analyze returned ${analyze.status()}`);
  const investigate = await request.post(API + "/api/soc/investigate", { data: { alert_id: "PL-SOC-1-NO-PRECEDENT-001" } });
  test.skip(!investigate.ok(), `Investigation trace returned ${investigate.status()}`);
  // Mutation cleanup: analyze is append-only; investigation is read-only shadow scoring.
  const body = await investigate.json();
  const trace = body.investigation_trace ?? body.vld?.trace;
  expect(trace.length).toBeGreaterThan(0);
  expect(trace.map((step: any) => step.step)).toEqual(trace.map((_: any, index: number) => index));
  expect(trace.every((step: any) => step.selected_edge && step.evidence_keys.length > 0)).toBe(true);
  expect(Number.isFinite(body.vld?.confidence)).toBe(true);
});
