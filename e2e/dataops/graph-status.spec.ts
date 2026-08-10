import { test, expect } from "../fixtures/copilot-fixture";
import { waitForScreenReady } from "../helpers/ui";

const DATAOPS_API_URL = process.env.DATAOPS_API_URL || "http://127.0.0.1:8030";

test.describe("DataOps scorer graph status", () => {
  test("default live stack reports sqlite scorer graph and healthy UI", async ({ page, request }) => {
    const graphStatus = await request.get(`${DATAOPS_API_URL}/api/dataops/graph/status`);
    expect(graphStatus.status()).toBe(200);
    const graphPayload = await graphStatus.json();
    expect(["sqlite", "age"]).toContain(graphPayload.active_backend);
    expect(["sqlite", "age"]).toContain(graphPayload.requested_backend);
    expect(typeof graphPayload.age_active).toBe("boolean");
    expect(graphPayload.active_domain).toBe("dataops");
    expect(graphPayload.operational_graph_client_status).toBe("separate_dataops_graph_client");

    const health = await request.get(`${DATAOPS_API_URL}/health`);
    expect(health.status()).toBe(200);
    const healthPayload = await health.json();
    expect(healthPayload.domain).toBe("dataops");

    const apiHealth = await request.get(`${DATAOPS_API_URL}/api/health`);
    expect(apiHealth.status()).toBe(200);

    const conservation = await request.get(`${DATAOPS_API_URL}/api/conservation/status`);
    expect(conservation.status()).toBeLessThan(500);

    await page.goto("/");
    await waitForScreenReady(page);
    await expect(page.locator("main")).not.toBeEmpty();
    await expect(page.getByText(/Alert Root Causes|DataOps|Triage/i).first()).toBeVisible();
  });
});
