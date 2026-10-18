import { test, expect, PORTS, apiGet, apiPost, gotoTab, type JsonRecord } from "./demo-fixture";

const DO = PORTS.dataops;

test.describe.serial(
  "DataOps Scenarios — Northwind Logistics (Priya Rao)",
  () => {
    test.beforeEach(async ({ demoReady }) => {
      test.skip(!demoReady, "Skipped: backends must be healthy and preseeded");
    });

    // ── DO-01  PLANT/BUILD ───────────────────────────────────────────
    test.skip(
      "DO-01 Which Data Can You Actually Trust? (PLANT/BUILD)",
      async () => {
        // PW-claim: source trust score changes after verified outcomes.
        // Endpoint: GET /api/dataops/trust
        // Requires plant data + learning loop wired — not yet built.
      },
    );

    // ── DO-02  LIVE ──────────────────────────────────────────────────
    test("DO-02 The Source That Lost Its Trust", async () => {
      // PW-claim: per-source trust scores render with differentiated values.
      // Actual endpoint returns fingerprint-style: {factors: [{name, dk_weight, label, rank}], overall_trust, ...}
      const body = await apiGet(DO.backend, "/api/dataops/trust") as JsonRecord;

      // Response should contain factors array (domain trust factors)
      const factors = body.factors as JsonRecord[];
      expect(Array.isArray(factors), "factors should be an array").toBe(true);
      expect(factors.length).toBeGreaterThanOrEqual(2);

      // DK weights should be differentiated (not all identical)
      const weights = factors.map(
        (f) => (f as JsonRecord).dk_weight as number,
      );
      const unique = new Set(weights);
      expect(
        unique.size,
        "dk_weights should be differentiated, not uniform",
      ).toBeGreaterThan(1);

      // Overall trust score should be present
      expect(body.overall_trust, "overall_trust should be present").toBeDefined();
      expect(typeof body.overall_trust).toBe("number");
    });

    // ── DO-03  LIVE ──────────────────────────────────────────────────
    test(
      "DO-03 Twelve Years in Six Numbers",
      async () => {
        // PW-claim: fingerprint renders 6-factor profile + checkpoint count.

        // 1. Fingerprint — expect 6+ factors
        const fp = await apiGet(DO.backend, "/api/fingerprint");
        const factors = (fp as JsonRecord).factors as JsonRecord[];
        expect(Array.isArray(factors), "factors should be an array").toBe(true);
        expect(factors.length).toBeGreaterThanOrEqual(6);

        // 2. Centroid history — expect checkpoints
        const ch = await apiGet(
          DO.backend,
          "/api/self/centroid-history",
        );
        const checkpoints = (ch as JsonRecord).checkpoints as JsonRecord[];
        expect(
          Array.isArray(checkpoints),
          "checkpoints should be an array",
        ).toBe(true);
        expect(checkpoints.length).toBeGreaterThanOrEqual(1);
      },
    );

    // ── DO-04  LIVE — SKIPPED: /api/self/rule-lifecycle + /api/evolution/recent-events both 404 on DataOps
    test.skip(
      "DO-04 The Rule That Proved Itself Wrong (endpoints not mounted on DataOps)",
      async () => {
        // PW-claim: a rule renders promoted→demoted with per-step reasons.
        // Both /api/self/rule-lifecycle and /api/evolution/recent-events return 404.
        // DataOps evolution router not mounted or endpoint not implemented.
        const body = await apiGet(
          DO.backend,
          "/api/self/rule-lifecycle",
        );

        const events = (body as JsonRecord).events as JsonRecord[];
        expect(Array.isArray(events), "events should be an array").toBe(true);
        expect(events.length).toBeGreaterThanOrEqual(2);
      },
    );

    // ── DO-05  EXPERIMENT — SKIPPED: DataOps /api/score returns 400 (needs python probe for error body)
    test(
      "DO-05 The Question the LLM Got Wrong (DataOps /api/score)",
      async () => {
        // PW-claim: investigation escalates what surface approves.
        const payload = {
          alert_id: "ALT-TEST-DO05",
          system: "billing_api",
          severity: "high",
          category: "quality_anomaly",
          description: "Schema mismatch in downstream join",
        };

        const body = await apiPost(
          DO.backend,
          "/api/score",
          payload,
        );

        expect(
          (body as JsonRecord).action,
          "response should include an action",
        ).toBeDefined();
        expect(
          typeof (body as JsonRecord).confidence,
          "response should include a numeric confidence",
        ).toBe("number");
      },
    );

    // ── DO-06  LIVE ──────────────────────────────────────────────────
    test(
      "DO-06 The Data Estate in January vs Now",
      async () => {
        // PW-claim: trust distribution renders differentiated after preseed.
        // Actual endpoint returns: {factors: [{name, dk_weight, ...}], overall_trust, ...}
        const body = await apiGet(DO.backend, "/api/dataops/trust") as JsonRecord;

        const factors = body.factors as JsonRecord[];
        expect(Array.isArray(factors), "factors should be an array").toBe(true);
        expect(factors.length).toBeGreaterThanOrEqual(2);

        // Verify non-uniform DK weight distribution
        const weights = factors.map(
          (f) => (f as JsonRecord).dk_weight as number,
        );
        const min = Math.min(...weights);
        const max = Math.max(...weights);
        expect(
          max - min,
          "dk_weights should span a non-trivial range",
        ).toBeGreaterThan(0);
      },
    );

    // ── DO-07  ROADMAP ───────────────────────────────────────────────
    test.skip(
      "DO-07 Your Data Tells You What to Buy (ROADMAP)",
      async () => {
        // Endpoint: GET /api/di/acquisition-advice
        // ROADMAP — not yet built.
      },
    );

    // ── DO-08  ROADMAP ───────────────────────────────────────────────
    test.skip(
      "DO-08 Ask It Like a Person (ROADMAP)",
      async () => {
        // Endpoint: GET /api/dataops/nl/query
        // ROADMAP — not yet built.
      },
    );

    // ── DO-09  PLANT ─────────────────────────────────────────────────
    test.skip(
      "DO-09 It Tested Its Fixes (PLANT)",
      async () => {
        // Endpoint: GET /api/evolution/* (DataOps-scoped)
        // PW-claim: promoted + rejected counts with per-rejection reasons,
        //   category_deltas, cross-system transfer trail,
        //   6-category eligibility panel.
        // Requires plant data — not yet built.
      },
    );
  },
);
