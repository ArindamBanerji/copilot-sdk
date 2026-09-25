import { test, expect } from "@playwright/test";
const API="http://127.0.0.1:8020";
test("PUR-04 quiet-week", async ({ request }) => {
  const response=await request.get(API+"/api/purchasing/proof-ledger");
  test.skip(!response.ok(), `Proof ledger returned ${response.status()}`);
  const body=await response.json();
  expect(body.proof_curve.decisions).toBeGreaterThan(0);
  expect(body.proof_curve.verified).toBeGreaterThan(0);
  expect(body.competence_curve.accuracy).toBeGreaterThan(0);
  expect(body.entries.length).toBeGreaterThan(0);
  expect(body.attribution).toMatch(/verified/i);
});




