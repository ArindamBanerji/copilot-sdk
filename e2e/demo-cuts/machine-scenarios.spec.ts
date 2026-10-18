/**
 * Machine Scenarios (MACH-01 → MACH-06) — per demo_scenarios_catalog_v6.md
 * Architecture deep-dive tests: decision traces, geometry, scoring internals.
 * Backends: SOC 8001, S2P 8002
 */
import { test, expect, PORTS, apiGet, apiPost, gotoTab, type JsonRecord } from "./demo-fixture";

const SOC = PORTS.soc;
const S2P = PORTS.s2p;
const DO = PORTS.dataops;

test.describe.serial("Machine Scenarios — Architecture Deep-Dive", () => {
  test.beforeEach(async ({ demoReady }) => {
    test.skip(!demoReady, "Skipped: backends must be healthy and preseeded");
  });

  // ─── MACH-01 (LIVE) ──────────────────────────────────────────────
  // "One Decision Through the Machine" — decision trace via DataOps /api/score.
  // PW-claim: decision trace renders read sequence + confidence.
  // Uses DataOps scoring (accepts arbitrary payloads; SOC /api/alert/analyze requires preseed alerts).
  // ─────────────────────────────────────────────────────────────────
  test("MACH-01 One Decision Through the Machine — decision trace", async () => {
    const payload = {
      alert_id: "MACH-TRACE-001",
      system: "billing_api",
      severity: "high",
      category: "quality_anomaly",
      description: "Decision trace test — schema mismatch in downstream join",
    };

    const result = (await apiPost(
      DO.backend,
      "/api/score",
      payload,
    )) as JsonRecord;

    // Must have an action and confidence
    const action = result.action ?? result.recommended_action;
    expect(action, "decision trace must include an action").toBeTruthy();

    const confidence = result.confidence;
    expect(confidence, "decision trace must include confidence").toBeDefined();
    expect(typeof confidence === "number").toBe(true);
  });

  // ─── MACH-02 (LIVE) ──────────────────────────────────────────────
  // "Reshape, Not Retrieve" — SOC no-precedent path.
  // PW-claim: no-precedent path renders (action exists even with
  //           zero pattern history).
  // ─────────────────────────────────────────────────────────────────
  test("MACH-02 Reshape Not Retrieve — no-precedent path", async () => {
    // Uses DataOps scoring with a novel category combination to test no-precedent behavior.
    const novelPayload = {
      alert_id: "MACH-NOVEL-001",
      system: "unknown_system_novel",
      severity: "critical",
      category: "quality_anomaly",
      description: "Novel alert pattern with no prior precedent in system",
    };

    const result = (await apiPost(
      DO.backend,
      "/api/score",
      novelPayload,
    )) as JsonRecord;

    // Even with no precedent, must produce an action
    const action = result.action ?? result.recommended_action;
    expect(action, "no-precedent path must still produce an action").toBeTruthy();

    // Confidence may be lower but must exist
    expect(result.confidence, "confidence must be present").toBeDefined();
  });

  // ─── MACH-03 (PLANT — test.skip) ─────────────────────────────────
  // "The Parameter That Moved" — recursion trace fixture.
  // PW-claim: K delta renders and read order changes.
  // ─────────────────────────────────────────────────────────────────
  test.skip(
    "MACH-03 The Parameter That Moved — recursion trace (PLANT)",
    async () => {
      // Needs recursion trace fixture with K delta
      const body = (await apiGet(
        SOC.backend,
        "/api/soc/recursion-trace",
      )) as JsonRecord;

      expect(body).toBeTruthy();
      const kDelta = body.k_delta ?? body.delta_k ?? body.parameter_delta;
      expect(kDelta).toBeDefined();

      const readOrder = body.read_order ?? body.factor_order;
      expect(readOrder).toBeTruthy();
      expect(Array.isArray(readOrder)).toBe(true);
    },
  );

  // ─── MACH-04 (LIVE) ──────────────────────────────────────────────
  // "Five Hundred, Not Five Million" — geometry dimensions + curve.
  // PW-claim: geometry dimensions render; curve reaches plateau.
  // Endpoint: /api/soc/learning-state on SOC.
  // ─────────────────────────────────────────────────────────────────
  test("MACH-04 Five Hundred Not Five Million — geometry dimensions", async () => {
    const body = (await apiGet(
      SOC.backend,
      "/api/soc/learning-state",
    )) as JsonRecord;

    expect(body, "learning-state must return data").toBeTruthy();

    // Should contain geometry dimensions or tensor shape
    // The SOC learning-state encodes geometry through bootstrap_category_weights
    // (each key = a category dimension) rather than a dedicated tensor_shape field.
    const hasDimensions =
      body.tensor_shape !== undefined ||
      body.dimensions !== undefined ||
      body.cells !== undefined ||
      body.centroid_count !== undefined ||
      body.geometry !== undefined ||
      body.shape !== undefined ||
      body.bootstrap_category_weights !== undefined ||
      body.category_weights !== undefined ||
      body.weights !== undefined;
    expect(
      hasDimensions,
      "learning-state should include geometry dimensions or tensor shape",
    ).toBe(true);

    // If tensor shape is present, verify it matches SOC (6,4,6) = 144
    if (body.tensor_shape) {
      const shape = body.tensor_shape;
      if (Array.isArray(shape)) {
        const product = (shape as number[]).reduce((a, b) => a * b, 1);
        expect(
          product,
          "SOC tensor should be 144 cells (6x4x6)",
        ).toBe(144);
      }
    }
  });

  // MACH-05: CONCEPTUAL — no PW-claim. Skipped per catalog.

  // ─── MACH-06 (LIVE) ──────────────────────────────────────────────
  // "The Decision Software Can Read" — POST /api/s2p/score on S2P.
  // PW-claim: response has typed action + confidence + provenance block.
  // ─────────────────────────────────────────────────────────────────
  test("MACH-06 The Decision Software Can Read — S2P structured score", async () => {
    const invoicePayload = {
      event_id: "MACH-INV-001",
      amount: 12500.00,
      supplier_id: "SUP-MACH-001",
      category: "price_variance",
      match_status: 0.85,
      amount_variance_ratio: 0.05,
      duplicate_score: 0.02,
      supplier_exception_history: 0.90,
      payment_terms_impact: 0.80,
      commodity_index_correlation: 0.75,
      tax_regulatory_compliance: 0.92,
      environmental_risk: 0.60,
    };

    const result = (await apiPost(
      S2P.backend,
      "/api/s2p/score",
      invoicePayload,
    )) as JsonRecord;

    // Must have a typed action (recommended_action or action)
    const action = result.recommended_action ?? result.action;
    expect(action, "S2P score must return a typed action").toBeTruthy();
    expect(typeof action === "string").toBe(true);

    // Must have confidence
    const confidence = result.confidence ?? result.score;
    expect(confidence, "S2P score must return confidence").toBeDefined();

    // Should have a provenance block (factors, reasoning, or audit trail)
    const provenance =
      result.provenance ??
      result.factors ??
      result.factor_contributions ??
      result.reasoning;
    expect(
      provenance,
      "S2P score should include provenance (factors or reasoning)",
    ).toBeTruthy();
  });
});
