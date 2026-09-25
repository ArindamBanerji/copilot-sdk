import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8001";
function readTrace(body: any): any[] {
  const trace = body.investigation_trace ?? body.vld?.trace ?? [];
  return Array.isArray(trace) ? trace : [];
}
function decisionId(body: any): string | undefined {
  return body.decision_id ?? body.recommendation?.decision_id ?? body.gae_scoring?.decision_id;
}
function action(body: any): string | undefined {
  return body.action ?? body.recommendation?.action ?? body.gae_scoring?.action;
}

test("MACH-03 verified-outcome changes same-alert investigation trace", async ({ request }) => {
  const alertId = "PL-SOC-1-NO-PRECEDENT-001";
  const first = await request.post(API + "/api/soc/investigate", { data: { alert_id: alertId } });
  test.skip(!first.ok(), `First investigation returned ${first.status()}`);
  const firstBody = await first.json();
  const before = readTrace(firstBody);
  test.skip(before.length === 0, "Investigation response has no trace to compare");

  const analyzed = await request.post(API + "/api/alert/analyze", { data: { alert_id: alertId } });
  test.skip(!analyzed.ok(), `Analyze returned ${analyzed.status()}`);
  const analyzedBody = await analyzed.json();
  const id = decisionId(analyzedBody);
  const selectedAction = action(analyzedBody);
  test.skip(!id, "Analyze response has no decision_id for verified-outcome injection");
  test.skip(!selectedAction, "Analyze response has no action for verified-outcome injection");

  const outcome = await request.post(API + "/api/alert/outcome", {
    data: {
      alert_id: alertId,
      decision_id: id,
      outcome: "correct",
      analyst_action: selectedAction,
      override_comment: "MACH-03 verified parameter-moved demo outcome",
    },
  });
  test.skip(!outcome.ok(), `Outcome returned ${outcome.status()}`);

  const second = await request.post(API + "/api/soc/investigate", { data: { alert_id: alertId } });
  test.skip(!second.ok(), `Second investigation returned ${second.status()}`);
  const afterBody = await second.json();
  const after = readTrace(afterBody);
  test.skip(after.length === 0, "Second investigation response has no trace to compare");
  test.skip(JSON.stringify(before) === JSON.stringify(after), "Verified outcome did not change the investigation trace");
  expect(after).not.toEqual(before);
});
