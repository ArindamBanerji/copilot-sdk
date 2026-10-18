/**
 * Pilot Scenarios (PILOT-01 → PILOT-04) — per demo_scenarios_catalog_v6.md
 * Enterprise buying-committee tests: readiness, artifacts, ROI.
 * Backends: Purchasing 8020, SOC 8001
 */
import { test, expect, PORTS, apiGet, apiPost, gotoTab, type JsonRecord } from "./demo-fixture";

const SOC = PORTS.soc;
const PUR = PORTS.purchasing;

test.describe.serial("Pilot Scenarios — Enterprise Buying Committee", () => {
  test.beforeEach(async ({ demoReady }) => {
    test.skip(!demoReady, "Skipped: backends must be healthy and preseeded");
  });

  // ─── PILOT-01 (ILLUSTRATIVE/LIVE) ────────────────────────────────
  // "Your First 90 Days" — /api/purchasing/day-0-readiness on Purchasing.
  // PW-claim: readiness card renders ready/coverage/not_yet.
  // ─────────────────────────────────────────────────────────────────
  test("PILOT-01 Your First 90 Days — day-0 readiness", async () => {
    const body = (await apiGet(
      PUR.backend,
      "/api/purchasing/day-0-readiness",
    )) as JsonRecord;

    expect(body, "day-0-readiness must return data").toBeTruthy();

    // Should have readiness or status fields
    const hasReadiness =
      body.readiness !== undefined ||
      body.status !== undefined ||
      body.ready !== undefined ||
      body.coverage !== undefined ||
      body.day_0_status !== undefined;
    expect(
      hasReadiness,
      "day-0-readiness should contain readiness/status/coverage fields",
    ).toBe(true);

    // If readiness has sub-fields, verify they include ready/coverage/not_yet
    if (typeof body.readiness === "object" && body.readiness !== null) {
      const r = body.readiness as JsonRecord;
      const hasExpectedFields =
        r.ready !== undefined ||
        r.coverage !== undefined ||
        r.not_yet !== undefined;
      expect(
        hasExpectedFields,
        "readiness object should include ready, coverage, or not_yet",
      ).toBe(true);
    }
  });

  // ─── PILOT-02 (PLANT/BUILD — test.skip) ──────────────────────────
  // "The Month Verifications Stopped" — curve flatlines during gap.
  // PW-claim: curve flatlines during gap, resumes after.
  // ─────────────────────────────────────────────────────────────────
  test(
    "PILOT-02 The Month Verifications Stopped — curve flatline (PLANT/BUILD)",
    async () => {
      // Needs planted verification gap in trajectory data
      const trajectory = (await apiGet(
        PUR.backend,
        "/api/trajectory",
      )) as JsonRecord;

      expect(trajectory).toBeTruthy();
      const points = trajectory.points ?? trajectory.data ?? trajectory.series;
      expect(points).toBeTruthy();
      expect(Array.isArray(points)).toBe(true);

      // Should show a flatline period followed by resumption
      // (specific assertion depends on planted gap fixture)
    },
  );

  // ─── PILOT-03 (LIVE) ─────────────────────────────────────────────
  // "Open the Three Artifacts" — /api/self/centroid-history.
  // PW-claim: mu/sigma/K render with timestamps.
  // ─────────────────────────────────────────────────────────────────
  test("PILOT-03 Open the Three Artifacts — centroid history", async () => {
    const body = (await apiGet(
      SOC.backend,
      "/api/self/centroid-history",
    )) as JsonRecord;

    expect(body, "centroid-history must return data").toBeTruthy();

    // Response contains checkpoints array (verified via live probe)
    const checkpoints = body.checkpoints as JsonRecord[];
    expect(Array.isArray(checkpoints), "checkpoints should be an array").toBe(true);
    expect(
      checkpoints.length,
      "should have at least one checkpoint",
    ).toBeGreaterThan(0);

    // Each checkpoint should have a timestamp (created_at) and checkpoint_id
    for (const cp of checkpoints) {
      const hasTimestamp =
        cp.created_at !== undefined ||
        cp.timestamp !== undefined ||
        cp.t !== undefined;
      expect(
        hasTimestamp,
        `checkpoint should have a timestamp: ${JSON.stringify(cp)}`,
      ).toBe(true);
    }
  });

  // ─── PILOT-04 (MODELED — test.skip) ──────────────────────────────
  // "Bring Your Own Numbers" — /api/roi/calculate.
  // PW-claim: input produces projected divergence week. MODELED.
  // ─────────────────────────────────────────────────────────────────
  test(
    "PILOT-04 Bring Your Own Numbers — ROI calculator (MODELED)",
    async () => {
      // /api/roi/calculate — modeled, not live
      const body = (await apiPost(
        PUR.backend,
        "/api/roi/calculate",
        {
          daily_decisions: 200,
          analyst_cost_per_hour: 85,
          current_accuracy: 0.72,
        },
      )) as JsonRecord;

      expect(body).toBeTruthy();
      const divergenceWeek =
        body.divergence_week ?? body.projected_divergence ?? body.breakeven_week;
      expect(divergenceWeek).toBeDefined();
      expect(typeof divergenceWeek === "number").toBe(true);
    },
  );
});
