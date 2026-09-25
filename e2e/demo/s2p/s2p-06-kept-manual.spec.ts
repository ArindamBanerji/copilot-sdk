import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8002";
test("S2P-06 kept-manual", async ({ request }) => {
  const response=await request.get(API+"/api/s2p/evidence/compliance");
  test.skip(!response.ok(),"Endpoint returned "+response.status());
  const body = await response.json();
  expect(body.flagged_count).toBeGreaterThan(0);
  expect(body.flagged_invoices.length).toBeGreaterThan(0);
  const manual = body.flagged_invoices.find((invoice: any) => invoice.tax_regulatory_compliance < 0.7);
  expect(manual).toBeDefined();
  expect(manual.recommended_action).not.toMatch(/auto_approve/i);
});
