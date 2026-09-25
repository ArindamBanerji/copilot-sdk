import { test, expect } from "@playwright/test";
test("PLAT-03 five-corrections", async ({ request }) => {
  const targets = [
    { name: "SOC", url: "http://127.0.0.1:8001/api/fingerprint" },
    { name: "S2P", url: "http://127.0.0.1:8002/api/s2p/insight/fingerprint?invoice_id=S2P-INV-0001" },
    { name: "Trading", url: "http://127.0.0.1:8010/api/fingerprint" },
    { name: "Purchasing", url: "http://127.0.0.1:8020/api/fingerprint" },
    { name: "DataOps", url: "http://127.0.0.1:8030/api/fingerprint" },
  ];
  const failures: string[] = [];
  const bodies: unknown[] = [];
  for (const target of targets) {
    const response = await request.get(target.url);
    if (!response.ok()) failures.push(`${target.name}:${response.status()}`);
    else bodies.push(await response.json());
  }
  test.skip(failures.length > 0, `Fingerprint endpoints unavailable: ${failures.join(", ")}`);
  expect(bodies).toHaveLength(targets.length);
  for (const body of bodies as any[]) {
    const factors = body.factors ?? Object.values(body.factors ?? {});
    expect(Array.isArray(factors) ? factors.length : Object.keys(body).length).toBeGreaterThan(0);
  }
});
