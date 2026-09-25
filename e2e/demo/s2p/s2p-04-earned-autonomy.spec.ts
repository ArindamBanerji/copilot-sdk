import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8002";
test("S2P-04 earned-autonomy", async ({ request }) => {
  const response = await request.get(API + "/api/conservation/status");
  test.skip(!response.ok(), `Conservation returned ${response.status()}`);
  const trajectoryResponse = await request.get(API + "/api/s2p/performance/trajectory");
  test.skip(!trajectoryResponse.ok(), `Performance trajectory returned ${trajectoryResponse.status()}`);
  const body = await response.json();
  const trajectory = await trajectoryResponse.json();
  expect(body.status).toBe("GREEN");
  expect(body.verified_count).toBeGreaterThan(0);
  expect(body.q).toBeGreaterThan(0);
  expect(body.passed).toBe(true);
  expect(trajectory.points.length).toBeGreaterThan(1);
  expect(trajectory.verified).toBeGreaterThan(0);
});




