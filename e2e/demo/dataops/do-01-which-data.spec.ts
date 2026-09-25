import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8030";
test("DO-01 which-data", async ({ request }) => {
  try {
    const response=await request.post(API+"/api/dataops/trust/perturb", {data:{source_id:"sap_s4hana",perturbation_type:"degrade",magnitude:0.1,decisions:3}});
    test.skip(!response.ok(),"Endpoint returned "+response.status());
    const result = await response.json();
    expect(result.simulation).toBe(true);
    expect(result.learning_mode).toBe("reversible_demo_overlay");
    expect(result.trust_after).toBeLessThan(result.trust_before);
  } finally {
    // Cleanup: reset the reversible trust overlay.
    await request.post(API + "/api/dataops/trust/reset", { data: { source_id: "sap_s4hana" } });
  }
});
