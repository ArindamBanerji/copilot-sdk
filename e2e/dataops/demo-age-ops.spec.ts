import { test, expect } from "../fixtures/copilot-fixture";

const DATAOPS_API_URL = process.env.DATAOPS_API_URL || "http://127.0.0.1:8030";

test.describe("demo AGE ops DataOps smoke", () => {
  test("default demo stack exposes sqlite scorer graph status and renders UI", async ({ page, request }) => {
    const graphStatus = await request.get(`${DATAOPS_API_URL}/api/dataops/graph/status`, { timeout: 30_000 });
    expect(graphStatus.status()).toBe(200);
    const graphPayload = await graphStatus.json();
    expect(graphPayload.requested_backend).toBe("sqlite");
    expect(graphPayload.active_backend).toBe("sqlite");
    expect(graphPayload.age_active).toBe(false);
    expect(graphPayload.active_domain).toBe("dataops");
    expect(graphPayload.operational_graph_client_status).toBe("separate_dataops_graph_client");

    const health = await request.get(`${DATAOPS_API_URL}/health`, { timeout: 30_000 });
    expect(health.status()).toBe(200);
    const healthPayload = await health.json();
    expect(healthPayload.domain).toBe("dataops");

    const conservation = await request.get(`${DATAOPS_API_URL}/api/conservation/status`, { timeout: 30_000 });
    expect(conservation.status()).toBe(200);

    await page.goto("/");
    await expect(page.locator("main")).not.toBeEmpty();
    await expect(page.getByText(/Alert Root Causes|DataOps|Triage/i).first()).toBeVisible();
  });
});
