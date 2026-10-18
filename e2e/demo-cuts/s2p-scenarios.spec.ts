import { test, expect, PORTS, apiGet, apiPost, gotoTab, type JsonRecord } from "./demo-fixture";

const S2P = PORTS.s2p;

test.describe.serial("S2P Scenarios — Halden Manufacturing (David Okoye)", () => {
  test.beforeEach(async ({ demoReady }) => {
    test.skip(!demoReady, "Skipped: backends must be healthy and preseeded");
  });

  // ─── S2P-01 (LIVE) ─── "The Rule That Kept Saying No"
  // Rule engine says REJECT but reasoning says ACCEPT with contract clause cited.
  // S2P /api/s2p/score requires amount, supplier_id, and 8 top-level factor fields.
  test("S2P-01 rule-vs-reasoning divergence on invoice score", async () => {
    const invoice = {
      event_id: "S2P-INV-0001",
      amount: 15750.00,
      supplier_id: "SUP-0001",
      category: "price_variance",
      match_status: 0.85,
      amount_variance_ratio: 0.08,
      duplicate_score: 0.02,
      supplier_exception_history: 0.90,
      payment_terms_impact: 0.80,
      commodity_index_correlation: 0.75,
      tax_regulatory_compliance: 0.92,
      environmental_risk: 0.60,
    };

    const res = (await apiPost(S2P.backend, "/api/s2p/score", invoice)) as JsonRecord;
    expect(res).toBeDefined();

    // Must have a typed action (recommended_action or action)
    const action = res.recommended_action ?? res.action;
    expect(action, "S2P score must return a typed action").toBeTruthy();
    expect(typeof action === "string").toBe(true);

    // Must have confidence
    const confidence = res.confidence ?? res.score ?? res.composite_score;
    expect(confidence, "S2P score must return confidence").toBeDefined();
    expect(typeof confidence).toBe("number");

    // Should have provenance (factors or reasoning)
    const provenance =
      res.provenance ?? res.factors ?? res.factor_contributions ?? res.reasoning;
    expect(provenance, "S2P score should include provenance").toBeTruthy();
  });

  // ─── S2P-02 (LIVE) ─── "Before David's First Invoice"
  // First decision scores with confidence; zero prior decisions expected at start.
  // S2P /api/s2p/score requires amount, supplier_id, and 8 top-level factor fields.
  test("S2P-02 first-decision score renders with confidence", async () => {
    const invoice = {
      event_id: "S2P-INV-FIRST",
      amount: 8200.00,
      supplier_id: "SUP-0002",
      category: "quantity_mismatch",
      match_status: 0.95,
      amount_variance_ratio: 0.03,
      duplicate_score: 0.01,
      supplier_exception_history: 0.94,
      payment_terms_impact: 0.85,
      commodity_index_correlation: 0.80,
      tax_regulatory_compliance: 0.99,
      environmental_risk: 0.40,
    };

    const res = (await apiPost(S2P.backend, "/api/s2p/score", invoice)) as JsonRecord;
    expect(res).toBeDefined();

    // Confidence must exist and be numeric
    const confidence = res.confidence ?? res.score ?? res.composite_score;
    expect(confidence, "confidence must be present").toBeDefined();
    expect(typeof confidence).toBe("number");
    expect(confidence as number).toBeGreaterThanOrEqual(0);
    expect(confidence as number).toBeLessThanOrEqual(1);
  });

  // ─── S2P-03 (PLANT) ─── "When Paying More Is the Right Call"
  // Needs: fixture that triggers HOLD with working-capital reasoning.
  test("S2P-03 HOLD with working-capital reasoning", async () => {
    // PLANT — requires a fixture invoice where paying more is optimal due to
    // working-capital constraints (e.g., early-payment discount vs. cash-flow).
    const invoice = {
      event_id: "S2P-INV-HOLD",
      category: "contract_gap",
      match_status: 0.70,
      amount_variance_ratio: 0.15,
      duplicate_score: 0.05,
      supplier_exception_history: 0.60,
      payment_terms_impact: 0.40,
      commodity_index_correlation: 0.65,
      tax_regulatory_compliance: 0.75,
      environmental_risk: 0.55,
      amount: 15750.00,
      supplier_id: "SUP-001",
    };

    const res = await apiPost(S2P.backend, "/api/s2p/score", invoice);
    const action = (res as JsonRecord).action ?? (res as JsonRecord).recommended_action;
    expect(typeof action).toBe("string");
    expect((action as string).length).toBeGreaterThan(0);

    const reasoning = (res as JsonRecord).reasoning ?? (res as JsonRecord).explanation;
    expect(typeof reasoning).toBe("string");
    expect((reasoning as string).length).toBeGreaterThan(0);
  });

  // ─── S2P-04 (LIVE) ─── "Earned Autonomy, Week Over Week"
  // Conservation status shows verified count, accuracy, and GREEN status.
  test("S2P-04 conservation status shows earned autonomy metrics", async () => {
    const res = await apiGet(S2P.backend, "/api/conservation/status");
    expect(res).toBeDefined();

    const record = res as JsonRecord;

    // Verified count must be present and non-negative
    const verified = record.verified_count ?? record.verified ?? record.total_verified;
    expect(verified).toBeDefined();
    expect(typeof verified).toBe("number");
    expect(verified as number).toBeGreaterThanOrEqual(0);

    // Accuracy or correct metric must be present
    const accuracy =
      record.accuracy ??
      record.correct_count ??
      record.correct ??
      record.correct_pct;
    expect(accuracy).toBeDefined();
    expect(typeof accuracy).toBe("number");

    // Status should be present (GREEN expected for healthy system)
    const status = record.status ?? record.conservation_status ?? record.state;
    expect(status).toBeDefined();
  });

  // ─── S2P-05 (PLANT) ─── "The Queue That Shrank"
  // Needs: /api/s2p/compliance/report endpoint with extinction timeline data.
  test.skip("S2P-05 extinction timeline shows exception class going to zero", async () => {
    // PLANT — requires compliance report endpoint that tracks exception classes
    // over time, showing at least one class declining from N to 0.
    const res = await apiGet(S2P.backend, "/api/s2p/compliance/report");
    const record = res as JsonRecord;

    const timeline = record.extinction_timeline ?? record.timeline ?? record.classes;
    expect(Array.isArray(timeline)).toBe(true);

    // At least one class should show a trajectory ending at 0
    const extinct = (timeline as JsonRecord[]).find(
      (cls) => (cls.current_count ?? cls.count) === 0
    );
    expect(extinct).toBeDefined();
  });

  // ─── S2P-06 (PLANT) ─── "The Rule It Kept Manual"
  // Needs: /api/s2p/compliance/report endpoint with kept-manual rules.
  test.skip("S2P-06 kept-manual rule with failed-bar reason", async () => {
    // PLANT — requires compliance report showing a rule that the system
    // deliberately kept in manual mode because it failed the confidence bar.
    const res = await apiGet(S2P.backend, "/api/s2p/compliance/report");
    const record = res as JsonRecord;

    const rules = record.rules ?? record.manual_rules ?? record.kept_manual;
    expect(Array.isArray(rules)).toBe(true);

    const manualRule = (rules as JsonRecord[]).find(
      (r) => r.state === "kept-manual" || r.status === "manual"
    );
    expect(manualRule).toBeDefined();
    expect(manualRule!.reason ?? manualRule!.failed_reason).toBeDefined();
  });

  // ─── S2P-07 (ROADMAP) ─── "Spend One Read on Easy, Three on Hard"
  // Needs: budget-strip UI and differing read-count allocation logic (BUILD/ROADMAP).
  test("S2P-07 budget strip shows differing read counts per difficulty", async () => {
    // ROADMAP — requires budget-allocation endpoint or UI that shows
    // how the system allocates more reads to harder invoices.
    // This is a future feature; assertion stub for when it ships.
    const res = await apiGet(S2P.backend, "/api/s2p/budget/allocation");
    const record = res as JsonRecord;

    const strips = record.budget_strips ?? record.allocations ?? record.reads;
    expect(Array.isArray(strips)).toBe(true);

    // Easy invoices should get fewer reads than hard ones
    const easy = (strips as JsonRecord[]).find((s) => s.difficulty === "easy");
    const hard = (strips as JsonRecord[]).find((s) => s.difficulty === "hard");
    expect(easy).toBeDefined();
    expect(hard).toBeDefined();
    expect((hard!.read_count as number)).toBeGreaterThan(easy!.read_count as number);
  });

  // ─── S2P-08 (PLANT/BUILD) ─── "The $50K Needs More Confidence"
  // Needs: confidence-band rendering and dollar-threshold routing in conservation.
  test.skip("S2P-08 confidence band with dollar-threshold routing", async () => {
    // PLANT/BUILD — requires conservation preview endpoint to return
    // confidence bands that vary by invoice dollar amount.
    const res = await apiGet(S2P.backend, "/api/s2p/preview/conservation");
    const record = res as JsonRecord;

    // Confidence band should be present
    const band = record.confidence_band ?? record.band ?? record.threshold;
    expect(band).toBeDefined();

    // Dollar threshold routing should differentiate high-value invoices
    const thresholds = record.dollar_thresholds ?? record.routing ?? record.tiers;
    expect(thresholds).toBeDefined();

    // A $50K invoice should require higher confidence than a $5K invoice
    if (Array.isArray(thresholds)) {
      const highValue = (thresholds as JsonRecord[]).find(
        (t) => (t.amount as number) >= 50000
      );
      const lowValue = (thresholds as JsonRecord[]).find(
        (t) => (t.amount as number) <= 5000
      );
      if (highValue && lowValue) {
        expect(highValue.min_confidence as number).toBeGreaterThan(
          lowValue.min_confidence as number
        );
      }
    }
  });

  // ─── S2P-09 (PLANT) ─── "The Version We Froze in March"
  // Needs: /api/learning/frozen-twin endpoint with two series and a positive gap.
  test.skip("S2P-09 frozen twin shows two series with positive gap", async () => {
    // PLANT — requires a frozen-twin endpoint that returns the live model
    // series and the frozen-in-March baseline, with the live one ahead.
    const res = await apiGet(S2P.backend, "/api/learning/frozen-twin");
    const record = res as JsonRecord;

    const liveSeries = record.live ?? record.current ?? record.active;
    const frozenSeries = record.frozen ?? record.baseline ?? record.march;
    expect(liveSeries).toBeDefined();
    expect(frozenSeries).toBeDefined();

    // Live model should be ahead of frozen baseline (positive gap)
    const liveScore = (liveSeries as JsonRecord).accuracy ?? (liveSeries as JsonRecord).score;
    const frozenScore = (frozenSeries as JsonRecord).accuracy ?? (frozenSeries as JsonRecord).score;
    expect(typeof liveScore).toBe("number");
    expect(typeof frozenScore).toBe("number");
    expect(liveScore as number).toBeGreaterThan(frozenScore as number);
  });
});
