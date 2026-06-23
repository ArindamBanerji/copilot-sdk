import { test, expect } from "../fixtures/copilot-fixture";

const DATAOPS_API_URL = process.env.DATAOPS_API_URL || "http://127.0.0.1:8030";

test.describe("DataOps DI source profile API", () => {
  test("profiles endpoint returns source collection", async ({ request }) => {
    const response = await request.get(`${DATAOPS_API_URL}/api/di/profiles`);
    expect(response.status()).toBe(200);

    const payload = await response.json();
    expect(Array.isArray(payload.sources)).toBeTruthy();
    expect(typeof payload.total).toBe("number");
  });

  test("unknown source profile returns 404", async ({ request }) => {
    const response = await request.get(`${DATAOPS_API_URL}/api/di/profile/nonexistent`);
    expect(response.status()).toBe(404);
  });
});
