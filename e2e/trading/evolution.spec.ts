import { test, expect } from "../fixtures/copilot-fixture";

test("evolution variants API exposes Trading presentation variants", async ({ request }) => {
  const response = await request.get("http://localhost:8010/api/evolution/variants");
  expect(response.ok()).toBeTruthy();

  const payload = await response.json();
  expect(payload.domain).toBe("trading");
  expect(payload.variants.length).toBeGreaterThan(0);
  expect(payload.variants[0].variant_id).toMatch(/^(EXECUTION_THRESHOLD|REVENGE_COOLDOWN)_v\d+$/);
});

test("evolution variants include Trading-specific dimensions", async ({ request }) => {
  const response = await request.get("http://localhost:8010/api/evolution/variants");
  const payload = await response.json();
  const dimensions = payload.variants.flatMap((variant: { dimensions: Record<string, string> }) =>
    Object.keys(variant.dimensions),
  );

  expect(dimensions).toContain("family");
  expect(dimensions).toContain("version");
});

test("evolution variants remain presentation-only", async ({ request }) => {
  const response = await request.get("http://localhost:8010/api/evolution/variants");
  const text = JSON.stringify(await response.json()).toLowerCase();

  expect(text).not.toMatch(/\b(buy|sell|hold)\b/);
  expect(text).not.toMatch(/you should|financial advice/);
});
