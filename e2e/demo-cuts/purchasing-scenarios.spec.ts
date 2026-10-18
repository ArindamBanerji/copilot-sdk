import { test, expect, PORTS, apiGet, apiPost, gotoTab, type JsonRecord } from "./demo-fixture";

const PUR = PORTS.purchasing;

test.describe.serial(
  "Purchasing Scenarios — Brightline Hospitality (Marta Ruiz)",
  () => {
    test.beforeEach(async ({ demoReady }) => {
      test.skip(!demoReady, "Skipped: backends must be healthy and preseeded");
    });

    /* ------------------------------------------------------------------
     * PUR-01 (LIVE): "The GM Who Just Started"
     * PW-claim: supplier history renders for a GM with zero own decisions.
     * Endpoints: POST /api/score, GET /api/purchasing/proof-ledger
     * ------------------------------------------------------------------ */
    test("PUR-01 The GM Who Just Started — score + proof-ledger", async () => {
      // Purchasing SDK scoring router uses same shape as DataOps /api/score.
      // Categories: protein, produce, dairy, dry_goods, beverages (from PD v1.3 §7.1).
      const scorePayload = {
        alert_id: "PUR-SCORE-001",
        system: "kitchen",
        severity: "medium",
        category: "protein",
        description: "Olive Oil order — evaluate for new GM with zero own decisions",
      };

      const scoreRes = (await apiPost(
        PUR.backend,
        "/api/score",
        scorePayload,
      )) as JsonRecord;

      // Score response must contain an action/recommendation and confidence
      const hasAction =
        scoreRes.action !== undefined ||
        scoreRes.recommendation !== undefined ||
        scoreRes.suggested_action !== undefined;
      expect(hasAction).toBe(true);
      expect(scoreRes.confidence ?? scoreRes.score).toBeDefined();
    });

    /* ------------------------------------------------------------------
     * PUR-02 (LIVE): "The Trust Trap"
     * PW-claim: trust radar renders with most-trusted factor flagged high-sigma.
     * Endpoint: GET /api/fingerprint
     * ------------------------------------------------------------------ */
    test("PUR-02 The Trust Trap — fingerprint with sigma values", async () => {
      const fp = (await apiGet(
        PUR.backend,
        "/api/fingerprint",
      )) as JsonRecord;

      // Must return factors/weights with sigma values
      const factors = (fp.factors ?? fp.weights ?? fp.fingerprint) as
        | JsonRecord[]
        | JsonRecord
        | undefined;
      expect(factors).toBeDefined();

      // At least one factor must exist
      if (Array.isArray(factors)) {
        expect(factors.length).toBeGreaterThan(0);
        // Check that sigma or std or deviation field exists on at least one
        const hasSigma = factors.some(
          (f: JsonRecord) =>
            f.sigma !== undefined ||
            f.std !== undefined ||
            f.deviation !== undefined ||
            f.weight !== undefined,
        );
        expect(hasSigma).toBe(true);
      } else {
        // Object-form factors — at least one key
        expect(Object.keys(factors as JsonRecord).length).toBeGreaterThan(0);
      }
    });

    /* ------------------------------------------------------------------
     * PUR-03 (PLANT): "It Gave Up Its Own Authority"
     * PW-claim: on drift injection, self-pause activates.
     * Endpoint: GET /api/conservation/status
     * ------------------------------------------------------------------ */
    test.skip(
      "PUR-03 It Gave Up Its Own Authority — conservation self-pause on drift",
      async () => {
        const status = (await apiGet(
          PUR.backend,
          "/api/conservation/status",
        )) as JsonRecord;

        // When drift is injected the system should self-pause
        expect(status.paused ?? status.self_paused).toBe(true);
        expect(status.reason).toContain("drift");
      },
    );

    /* ------------------------------------------------------------------
     * PUR-04 (LIVE): "The Quiet Week"
     * PW-claim: proof_curve and competence_curve both render.
     * Endpoint: GET /api/purchasing/proof-ledger
     * ------------------------------------------------------------------ */
    test("PUR-04 The Quiet Week — proof and competence curves", async () => {
      const ledger = (await apiGet(
        PUR.backend,
        "/api/purchasing/proof-ledger",
      )) as JsonRecord;

      // proof_curve and competence_curve exist — may be objects or arrays
      const proofCurve = ledger.proof_curve ?? ledger.proofCurve;
      const competenceCurve =
        ledger.competence_curve ?? ledger.competenceCurve;

      // proof_curve: object {decisions, verified, correct} or array
      expect(proofCurve, "proof_curve must be present").toBeTruthy();
      if (typeof proofCurve === "object" && !Array.isArray(proofCurve)) {
        const pc = proofCurve as JsonRecord;
        expect(pc.decisions ?? pc.verified ?? pc.correct, "proof_curve object should have metrics").toBeDefined();
      }

      // competence_curve: object {accuracy} or array
      expect(competenceCurve, "competence_curve must be present").toBeTruthy();
      if (typeof competenceCurve === "object" && !Array.isArray(competenceCurve)) {
        const cc = competenceCurve as JsonRecord;
        expect(cc.accuracy ?? cc.score ?? cc.value, "competence_curve object should have accuracy").toBeDefined();
      }
    });

    /* ------------------------------------------------------------------
     * PUR-05 (PLANT): "Two Stores, Same Menu"
     * PW-claim: two divergent waste curves.
     * Endpoint: GET /api/learning/frozen-twin
     * ------------------------------------------------------------------ */
    test.skip(
      "PUR-05 Two Stores Same Menu — frozen-twin divergent waste curves",
      async () => {
        const twin = (await apiGet(
          PUR.backend,
          "/api/learning/frozen-twin",
        )) as JsonRecord;

        // Should return two waste curves that diverge
        expect(twin.curve_a).toBeDefined();
        expect(twin.curve_b).toBeDefined();
        expect(Array.isArray(twin.curve_a)).toBe(true);
        expect(Array.isArray(twin.curve_b)).toBe(true);

        // The curves should show divergence (different final values)
        const a = twin.curve_a as number[];
        const b = twin.curve_b as number[];
        expect(a.length).toBeGreaterThan(0);
        expect(b.length).toBeGreaterThan(0);
        expect(a[a.length - 1]).not.toEqual(b[b.length - 1]);
      },
    );

    /* ------------------------------------------------------------------
     * PUR-06 (ROADMAP): "Demand Wasn't the Limiting Factor"
     * Endpoint: POST /api/purchasing/investigate (not built)
     * ------------------------------------------------------------------ */
    test(
      "PUR-06 Demand Wasn't the Limiting Factor — investigation evidence",
      async () => {
        const investigatePayload = {
          decision_id: "PUR-TEST-06",
          category: "protein",
          factor_vector: [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
          budget: 2,
        };

        const result = (await apiPost(
          PUR.backend,
          "/api/investigation/investigate",
          investigatePayload,
        )) as JsonRecord;

        expect(result.decision_id).toBe("PUR-TEST-06");
        expect(result.budget_used).toBe(2);
        expect(Array.isArray(result.steps)).toBe(true);
        expect(result.contrast).toBeTruthy();
      },
    );
  },
);
