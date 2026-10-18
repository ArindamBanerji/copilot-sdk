/**
 * Fork Scenarios (FORK-01) — per demo_scenarios_catalog_v6.md
 * Open-source developer tests: clone-and-run, fingerprint, gate.
 * Backend: Trading 8010
 */
import { test, expect, PORTS, apiGet, apiPost, gotoTab, type JsonRecord } from "./demo-fixture";

const TRD = PORTS.trading;

test.describe.serial("Fork Scenarios — Open Source Developer", () => {
  test.beforeEach(async ({ demoReady }) => {
    test.skip(!demoReady, "Skipped: backends must be healthy and preseeded");
  });

  // ─── FORK-01 (LIVE) ──────────────────────────────────────────────
  // "Clone It, Run the Gate" — /api/fingerprint + /api/conservation/status.
  // PW-claim: fingerprint + gate render on fresh clone.
  // ─────────────────────────────────────────────────────────────────
  test("FORK-01 Clone It Run the Gate — fingerprint + conservation", async () => {
    // Part 1: fingerprint must return factors
    const fingerprint = (await apiGet(
      TRD.backend,
      "/api/fingerprint",
    )) as JsonRecord;

    expect(fingerprint, "fingerprint must return data").toBeTruthy();

    const factors =
      fingerprint.factors ?? fingerprint.fingerprint ?? fingerprint.data;
    expect(factors, "fingerprint should contain factors").toBeTruthy();

    if (Array.isArray(factors)) {
      expect(
        factors.length,
        "fingerprint should have multiple factors",
      ).toBeGreaterThan(0);

      // Each factor should have a name/key and a value/weight
      for (const f of factors) {
        const factor = f as JsonRecord;
        const hasName =
          factor.name !== undefined ||
          factor.key !== undefined ||
          factor.factor !== undefined;
        expect(
          hasName,
          `factor should have a name: ${JSON.stringify(factor)}`,
        ).toBe(true);
      }
    }

    // Part 2: conservation gate must return status
    const conservation = (await apiGet(
      TRD.backend,
      "/api/conservation/status",
    )) as JsonRecord;

    expect(conservation, "conservation/status must return data").toBeTruthy();

    const hasStatus =
      conservation.status !== undefined ||
      conservation.verified_count !== undefined ||
      conservation.conservation_status !== undefined ||
      conservation.q !== undefined;
    expect(
      hasStatus,
      "conservation response should have status or verified_count",
    ).toBe(true);
  });
});
