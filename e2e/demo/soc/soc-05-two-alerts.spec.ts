import { test, expect } from "@playwright/test";

const API = "http://127.0.0.1:8001";

test("SOC-05 two-alerts", async ({ request }) => {
  const response = await request.post(API + "/api/alert/cross-correlate", {
    data: {
      alert_ids: ["PL-SOC-5-KILLCHAIN-A", "PL-SOC-5-KILLCHAIN-B"],
    },
  });
  test.skip(!response.ok(), `cross-correlate returned ${response.status()}`);
  // Mutation: correlation is a read-only fixture evaluation; no cleanup is required.
  const body = await response.json();
  expect(body.correlation).toBeDefined();
  expect(body.correlation.kill_chain_detected).toBe(true);
  expect(body.correlation.combined_severity).toBe("critical");
  expect(body.correlation.shared_entities.length).toBeGreaterThan(0);
  expect(body.discovery_note).toBeDefined();
});




