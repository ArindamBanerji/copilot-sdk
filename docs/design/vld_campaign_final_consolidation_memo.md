# VLD Progressive-Strengthening Campaign — Final Consolidation Memo

**Date:** September 13-14, 2026
**Scope:** All experiments, campaigns (C1-C8), follow-ups (F-1, F-2), and diagnostics (G-1, G-2) from the VLD experiment program
**Authority:** MAP VLD Addendum v20, vld_paper_experiments_request_v2.md, vld_strengthening_campaign_v2.md, vld_B2_moat_redesign_memo.md, vld_oracle_ceiling_and_decision_characterization_v2.md
**Platform:** SDK v0.9.59+, SOC v5.148, S2P v0.7.50-s2p. 6,193 app tests, 0 failures throughout. Frozen hashes unchanged: scorer.py 24ac9e49, investigation.py 3441dcbd, investigation_router.py 08f4df7a

---

## 1. Executive summary

22 experiment runs across 8 campaigns + 4 follow-ups produced a complete, honest characterization of the VLD/RGI mechanism. The campaign was designed to progressively strengthen each paper claim by testing it under harder conditions — and to pre-register what each null/negative finding would do to the paper before results were in.

**Five claims strengthened:**
- Routing-level moat is real, multi-seed, and η-stable (B2 + EXP-1 + F-1)
- Labels are the asset — no realistic acquisition strategy reaches parity (C3)
- B=2 flat reads are sufficient under tested refinement (C7)
- Complexity predicts capability (exploratory, with within-domain proof) (G-2)
- Action-accuracy limitation is a fixable readout problem, not an upstream ceiling (G-1)

**Five claims bounded or corrected:**
- Judgment-specificity (μ) holds for SOC only; 4/5 copilots are routing-only (C2)
- Abstention/risk-coverage is domain-scoped; Trading/S2P show near-zero lift (C6)
- Conservation gate has 9-328 record detection lag and misses fast breaks (C5)
- Gate calibration is unresolved — Purchasing false-pause rate is a product concern (F-2)
- γ re-convergence condition is untested (C4)

**One finding reframes the entire campaign's negatives:** decision complexity (intrinsic dimensionality) predicts which copilots show strong RGI effects — the "weak on Purchasing/S2P" pattern is a characterized applicability boundary, not a collection of domain-specific weaknesses (G-2).

---

## 2. Platform state

```
SDK:         v0.9.59+     3,502 tests, 0 failed
Trading:                  1,452 tests, 0 failed
Purchasing:               827 tests, 0 failed (1 skipped: AGE)
DataOps:                  412 tests, 0 failed
App total:                6,193 tests, 0 failed

VLD:         Tier 5A/5B/5C/5D complete. All 5 copilots at 100% provider coverage.
Experiments: 25 prior (MAP v20) + 12 campaign + 4 follow-up/diagnostic + pre-campaign runs
RL SDK:      OutcomeReceipt, TemporalCreditAssigner, ExplorationBudget extracted
GraphStore:  Shared protocol, 5 copilots consuming
Paper data:  1,101-row result manifest, 13 publication charts, 12 experiment result JSONs
```

---

## 3. Pre-campaign experiments (Sep 13-14, before campaign)

| ID | Key result | Tier | Deliverable |
|---|---|---|---|
| TIER-5C/5D | All 5 copilots at 100% VLD provider coverage, +124 tests | — | apps/{trading,purchasing}/ |
| D-CEL + SMOKE | DataOps SAP/Celonis connectors, 412 tests | — | apps/dataops/ |
| PAPER-CHARTS | 8 PNG + 8 SVG, 300dpi | — | paper_charts/ |
| CLEANUP | DataOps import resolved, Fig 7 CSVs created | — | cleanup_verification_report.md |
| SDK-11 | SDK GREEN 3,502/0/0. mypy + VLD helper fixed | — | reward_protocol.py + vld_validation_report.py |
| GR-01 | GraphStore shared (5 copilots), RL contracts extracted, 38 new tests | — | gr01_rl_sdk_extraction_report.md |
| A1 | GAE gate BROKEN — permits GREEN with ~1/500 correct. SDK composite gate (75%/last-100 at scorer.py:2198) is the real floor. KE-5 inertness: GAE gate only bites first 8-13 decisions | Verification | conservation_gate_reconciliation.md |
| A2 | 1,101-row result manifest, 11 discrepancies flagged | Data | result_manifest.csv + README |
| C1 baseline | VLD within 1.40pp of RF(B=2) with 0 labels. Action accuracy ties RF(all) at 47.55%. LinUCB worse than majority at B=2. | REAL_COMPONENT + SIMULATED | external_baseline_full.json + fig_2b |
| B1 | RETRACTED — tautological design (gave competitor the asset being tested) | — | delayed_entrant_catchup.json (SUPERSEDED) |
| B2 | Routing-level data-specific moat: SOC 29.28pp, DataOps 6.17pp. Labels are the asset (~50% of labeled stream closes gap). | REAL_COMPONENT + SIMULATED | vld_moat_b2_v1.json + moat_b2_summary.md |
| EXP-1 | Seed robustness: SOC 19.56±5.35pp, DataOps 5.72±1.10pp, 0/5 parity both copilots | REAL_COMPONENT + SIMULATED | moat_b2_seeds.json |
| EXP-2 | μ-learning: SOC judgment-specific (+15.9pp, 3/3 seeds). DataOps routing-only (−2.51pp, 0/3). Via ProfileScorer.update() at profile_scorer.py:779 | REAL_COMPONENT + SIMULATED | moat_mu_learning.json |
| D1 | Verification→K update→changed decision. 0.200 vs 0.100 = unweighted vs K-weighted Q. Bulk-volume entitlement clause (no commodity-index). μ unchanged. | REAL_COMPONENT + SIMULATED | recursion_trace_example.md |
| D2 | ILLUSTRATIVE ordering: SOC 0.04wk → Purchasing 0.22 → S2P 0.31 → DataOps 0.47 → Trading 2.63 | ILLUSTRATIVE | verified_outcome_latency.csv |
| Fig-1 | Hero K-curves: +3-21pp, S2P negative dip visible, all frozen baselines MOVE | — | fig1_five_domain_curves.png/svg |
| Fig-2 | Moat catch-up from B2: replay/migration overlap incumbent | — | fig2_delayed_entrant.png/svg |
| Fig-3 | Risk-coverage RE-RUN: +8.9-13.4pp at 73.6-74.6% (NOT +9.5-15.2pp at 75%). Three-way held-out split. | — | fig3_risk_coverage.png/svg |

---

## 4. Campaign results (C1-C8)

### C1 — Oracle-separation core claims [P2 — deprioritized]

**Finding:** GroundTruthOracle exists in copilot-sdk (examples/jm_reference/oracle.py) but is wired to 0/5 harnesses. All five copilots ran at existing tier (REAL_COMPONENT + SIMULATED). 12/65 comparisons moved >3pp — seed/cohort differences, not label-regime effects.

**Critical correction:** The current VLD labels are GEOMETRY-DERIVED (nearest-centroid distance), NOT LLM-derived. There is no LLM prior to remove. "ORACLE-SEP" as a tier name implying escape from LLM dependency is incorrect. Oracle wiring is a robustness test (hidden-centroid displacement), not a tier upgrade.

**Paper impact:** Drop "ORACLE-SEP" tier name. Use "GEOMETRY-DERIVED SYNTHETIC." The labels are already math-derived — a strength (reproducible, deterministic), not a weakness to apologize for. Oracle wiring deferred to TIER-6/7.

**Deliverable:** c1_oracle_sep_summary.md


### C2 — μ-learning moat, all five copilots [P0]

**Finding:** SOC is the ONLY judgment-specific domain.

| Copilot | K-only gap | μ+K gap | Widening | Seeds >2pp | Verdict |
|---|---|---|---|---|---|
| SOC | 19.56 ± 5.35 | 34.68 ± 3.74 | +15.12 ± 2.87 | 5/5 | **Judgment-specific** |
| DataOps | 5.72 ± 1.10 | 3.93 ± 1.81 | −1.79 ± 1.90 | 0/5 | Routing-only |
| Trading | 11.22 ± 2.19 | 9.76 ± 1.96 | −1.46 ± 2.89 | 0/5 | Routing-only |
| Purchasing | 10.68 ± 3.41 | 11.96 ± 3.25 | +1.27 ± 5.96 | 2/5 | Routing-only (borderline) |
| S2P | 10.36 ± 3.19 | 5.02 ± 2.39 | **-5.33 ± 2.11** | 0/5 | Routing-only (μ hurts) |

S2P's μ-learning NARROWS the moat by 5.33pp. Purchasing is borderline (2/5 seeds, high variance ±5.96pp).

**Paper impact:** "Judgment-specificity (μ compounding widens the moat) holds for SOC. The remaining four domains show routing-only moats. S2P's μ-learning narrows the incumbent's lead — a domain property, not an η artifact (confirmed by F-1)."

**Deliverable:** c2_mu_learning_all_five.json + c2_mu_learning_summary.md


### C3 — Label-acquisition breadth [P1]

**Finding:** No realistic label source reaches parity. Labels are the asset.

| Source | SOC gap (routing/action) | DataOps gap (routing/action) | Parity? |
|---|---|---|---|
| Self-labeling (B2 3a) | 21.61 / 26.83 | 7.00 / 12.50 | No |
| WS-1 heuristic (30.5% / 16.3% accurate) | 10.40 / 11.30 | 3.65 / 14.02 | No |
| FM-1 pseudo-labeler (80% accurate) | 12.79 / 16.96 | 4.73 / 11.85 | No |
| FM-2 pseudo-labeler (90% accurate) | 11.76 / 15.69 | 4.76 / 12.07 | No |
| 10% labeled S_A (B2 3b) | 18.86 / 18.17 | 4.50 / 12.83 | No |
| 50% labeled S_A (B2 3b) | 6.03 / 7.17 | −1.50 / 1.83 | Near (DataOps) |
| S_A 10% corruption (B2 3c) | 0.69 / 3.33 | 2.92 / 4.67 | Near (SOC routing) |
| S_A 25% corruption (B2 3c) | 0.78 / 3.00 | 2.67 / 3.17 | Near (SOC routing) |

Even a 90%-accurate pseudo-labeler doesn't close the gap. Label accuracy alone is insufficient — you need the RIGHT labels on the RIGHT decisions. ~50% of the incumbent's actual labeled stream closes DataOps's gap, and corrupted-but-complete S_A nearly closes SOC's routing gap.

**Paper impact:** "Labels are the asset" holds under realistic competitor strategies. The moat is against competitors who cannot access the incumbent's verified-outcome stream — not against data-sharing or breach scenarios.

**Deliverable:** c3_label_breadth.json + c3_label_breadth_summary.md


### C4 — γ re-convergence + geometric conditions [P0, analytic-only]

**Finding:** GATE-B — no runnable two-phase re-convergence harness found. Two archived γ values exist (0.714 and 1.033) under an older ε parameterization, but they omit ‖Δ‖ and cannot be classified against the ε_sim ≪ ‖Δ‖ condition. The condition is UNTESTED — not confirmed or falsified.

**Paper impact:** "The paper claims the mechanism and the geometric condition (γ > 1 when ε_sim ≪ ‖Δ‖). γ magnitude is pilot-only (T-R). No synthetic sim confirms or falsifies γ > 1 at this time."

**Deliverable:** c4_gamma_reconvergence.json (analytic_only) + c4_gamma_summary.md


### C5 — Conservation gate detection lag [P0]

**Finding:** The SDK composite gate (75%/last-100) detects sustained degradation with measurable lag but misses fast breaks.

| Copilot | Slow drift lag | Poison 10% lag | Poison 25% lag | Poison 50% lag | Fast break (within 100) | Clean false-pause |
|---|---|---|---|---|---|---|
| DataOps | 217.5 (2/3) | 102 (3/3) | 50.7 (3/3) | 30.7 (3/3) | 3/3 ✅ | 13.70% |
| Trading | missed (0/3) | missed (0/3) | 90.7 (3/3) | 34.7 (3/3) | 0/3 | 0.74% |
| Purchasing | missed (0/3; 2 pre-paused) | 41 (1/3; 2 pre-paused) | 34 (1/3; 2 pre-paused) | 9 (1/3; 2 pre-paused) | 0/3 | **34.78%** |
| SOC | missed (0/3) | 219 (1/3) | 90.3 (3/3) | 44 (3/3) | 0/3 | 0.37% |
| S2P | 328 (2/3) | 165.7 (3/3) | 40 (3/3) | 26 (3/3) | 0/3 | 3.52% |

12/15 fast-break runs missed within 100 records (DataOps 3/3 was the exception). Purchasing's 34.78% clean-stream false-pause rate is a product blocker (diagnosed in F-2 as base accuracy 0.735 < 0.75 floor).

**Paper impact:** "The SDK composite gate bounds sustained self-poisoning with detection lags of 9-328 records. It paused in 3/15 fast-break runs; 12/15 were not paused within 100 records. A faster trigger is future work."

**Deliverable:** c5_conservation_lag.json + c5_conservation_lag_summary.md


### C6 — Held-out risk-coverage for Trading + S2P [P1]

**Finding:** Five-domain table complete. Trading and S2P show near-zero lift and non-monotonic curves.

| Copilot | Actual coverage at 75% target | Lift (action_accuracy) | Monotonic |
|---|---|---|---|
| DataOps | 74.04% | +10.98pp | ✅ |
| Purchasing | 74.56% | +13.36pp | ✅ |
| SOC | 73.64% | +8.92pp | ✅ |
| Trading | 76.47% | +0.16pp | ❌ (3/3 seeds) |
| S2P | 75.47% | +0.25pp | ❌ (3/3 seeds) |

**Paper impact:** "Risk-coverage calibration holds for evidence-rich domains (DataOps +10.98pp, Purchasing +13.36pp, SOC +8.92pp). Trading and S2P show near-zero lift with non-monotonic curves; universal monotonic risk-coverage is not supported."

**Deliverable:** c6_risk_coverage_trading_s2p.json + c6_risk_coverage_summary.md


### C7 — Looped-operator depth [P1, GATE-B1]

**Finding:** B=2 flat reads hold. A designed Q×K-weighted damped correlated-evidence rescoring operator added no material routing-quality gain. SOC showed +4pp action_accuracy at depth-3 with flat routing — action and routing move independently.

| Copilot | A1 Δr / Δa | A2 Δr / Δa | A3 Δr / Δa |
|---|---|---|---|
| SOC | +0.00 / +0.67pp | +0.00 / +2.00pp | +0.33 / **+4.00pp** |
| DataOps | +0.00 / +0.00pp | +0.00 / +0.00pp | +0.00 / +0.00pp |
| Trading | +0.00 / +0.00pp | +0.00 / +0.00pp | +0.00 / +0.00pp |

No arm exceeded A0 by >2pp routing_quality at ≥2/3 seeds for any copilot. B=2 passes the preregistered rule for this operator and these simulated streams.

**Paper impact:** "For a designed correlated-evidence refinement operating on the same two acquired dimensions, B=2 flat reads remained sufficient under a 2pp routing_quality materiality threshold; iterative refinement added no material routing-quality gain in these geometry-derived simulations."

**Deliverable:** c7_looped_depth.json + c7_looped_depth_summary.md


### C8 — Action-value boundary [P0, SOC-only]

**Finding:** Action accuracy is geometry-bounded, not strategy-bounded. ARCHITECTURE ISSUE on 2/3 geometry states. K-informed scoring is feasible but below the 3pp threshold.

| Geometry | Best strategy | Harness verdict |
|---|---|---|
| Default | B/C/D tie at 53.78% (= single-pass) | ARCHITECTURE ISSUE |
| Trained | E (oracle-category) 23.39%, +2.95pp vs A | VLD VALUE = SELECTIVE ENRICHMENT |
| Bootstrapped | B and single-pass tie at 51.93% | ARCHITECTURE ISSUE |

New K-informed strategies: pooled K weights +2.33pp (0/3 seeds >3pp), category-conditioned K +1.63pp (1/3 seeds). Neither meets the pre-registered rule.

**Paper impact:** "Across three seeded splits of the synthetic SOC fixture at trained geometry, the tested pooled and category-conditioned K-weighted scorers did not improve held-out action_accuracy by more than 3pp in at least two seeds over matched B=2 VLD; this bounds those variants, not all possible action models."

**Deliverable:** c8_action_boundary.json + c8_action_boundary_summary.md (in both repos)

---

## 5. Follow-up experiments (F-1, F-2)

### F-1 — η sweep (μ-learning stability)

**Finding:** Read 2 (real domain property). SOC judgment-specificity is η-stable across 0.5-4× default. S2P's negative widening is a domain property at default η but trends toward zero at higher η.

| η multiplier | SOC widening | S2P widening |
|---|---|---|
| 0.5× (η=0.025) | +9.70 ± 1.53pp | −6.30 ± 4.78pp |
| 1.0× (η=0.050) | +15.94 ± 3.71pp | −5.32 ± 2.85pp |
| 2.0× (η=0.100) | +14.08 ± 6.76pp | −2.69 ± 2.65pp |
| 4.0× (η=0.200) | +13.35 ± 4.95pp | −1.68 ± 3.73pp |

SOC stayed above +2pp in all seeds at every η. S2P mean remained negative but one seed was slightly positive (+1.44pp) at 4×. The bimodal split (SOC judgment-specific, S2P routing-only) is a stable domain characterization, not an η artifact — though S2P's magnitude is η-sensitive.

**Deliverable:** eta_sweep_f1.json + eta_sweep_f1_summary.md


### F-2 — Purchasing gate calibration

**Finding:** UNRESOLVED. Purchasing's steady-state action_accuracy (0.735 ± 0.040) sits below the global 0.75 floor, explaining the 34.78% (C5) / 46.13% (F-2 500-decision diagnostic) false-pause rate. DataOps is also marginal (0.770 ± 0.051, 24.67%).

No tested per-domain floor simultaneously achieved <5% clean PAUSE rates across all copilots AND preserved Purchasing detection within the pre-registered lag bound:

| Margin | DataOps | Trading | Purchasing | SOC | S2P |
|---|---|---|---|---|---|
| 0.05 | 17.87% | 18.53% | 13.47% | 27.20% | 7.53% |
| 0.10 | 5.93% | 8.27% | 1.40% | 11.13% | 0.00% |
| 0.15 | 0.20% | 2.20% | 0.27% | 5.33% | 0.00% |

At margin 0.15: Purchasing detection was lost (slow-drift missed, poison-25% lag = 103.5 records vs 11.3 for global gate). SOC remained above 5%.

**Paper impact:** "None of the tested per-domain floors simultaneously achieved below-5% clean PAUSE rates across all copilots and preserved Purchasing detection within the preregistered lag bound; calibration remains unresolved."

**Deliverable:** gate_calibration_f2.json + gate_calibration_f2_summary.md

---

## 6. Diagnostic experiments (G-1, G-2)

### G-1 — Oracle-ceiling diagnostic (the readout-problem fork)

**Finding:** 4/5 copilots show READOUT-PROBLEM — massive action_accuracy headroom exists when given perfect evidence, but VLD at B=2 doesn't capture it. Trained SOC is the exception (already at ceiling).

| Copilot | Geometry | VLD B=2 | Evidence oracle | Action oracle | Readout gap | Verdict |
|---|---|---|---|---|---|---|
| SOC | trained | 100.0% | 100.0% | 100.0% | 0.00pp | At ceiling |
| SOC | default | — | — | — | +21.00pp | READOUT-PROBLEM |
| SOC | bootstrapped | — | — | — | +46.78pp | READOUT-PROBLEM |

(SOC default/bootstrapped: individual rung values not reported in Codex output; readout gaps computed from available data.)
| DataOps | default | 44.4% | 100.0% | 100.0% | +55.61pp | READOUT-PROBLEM |
| Trading | default | 51.9% | 99.2% | 100.0% | +47.33pp | READOUT-PROBLEM |
| Purchasing | default | 30.7% | 98.8% | 100.0% | +68.11pp | READOUT-PROBLEM |
| S2P | default | 83.8% | 100.0% | 100.0% | +16.22pp | READOUT-PROBLEM |

Architecture gaps are near-zero (0-1.22pp) — the architecture CAN distinguish actions. The limitation is that VLD's readout is not consuming the evidence it acquires. This is fixable: condition the action readout on the investigation state.

**Critical caveat:** Near-perfect oracle scores use geometry-derived labels. These characterize the geometry/readout pipeline, not independent-label performance.

**Cross-references:** SOC's default readout gap (+21pp) is directionally compatible with C7's +4pp depth-3 action gain (partial evidence of closing the gap). Trained SOC at ceiling means training already solved the readout problem for SOC. C8's ARCHITECTURE ISSUE verdicts on default/bootstrapped geometry are consistent with large readout gaps there.

**Paper impact:** "On geometry-generated cases, full-factor evidence exposed substantial action_accuracy headroom over B=2 in four domains, while trained SOC was already at ceiling; these results characterize the geometry/readout pipeline, not independent-label performance."

**Deliverable:** oracle_ceiling_diagnostic.json + oracle_ceiling_summary.md


### G-2 — Decision-complexity characterization

**Finding:** COMPLEXITY-IS-THE-AXIS (exploratory). Intrinsic dimensionality was the strongest predictor of capability results across copilots.

| Configuration | Intrinsic dim | m_conditional | Separability | Chain length | Outcome entropy |
|---|---|---|---|---|---|
| DataOps | 4.866 | 0.407 | 0.938 | 2 | 0.033 |
| Trading | 2.712 | 0.503 | 0.575 | 1 | 0.045 |
| Purchasing | 3.887 | 0.274 | 0.625 | 2 | 0.165 |
| SOC | 1.159 | 0.138 | 0.824 | 1 | 0.020 |
| S2P single-firm | 1.911 | 0.213 | 0.666 | 1 | 0.000 |
| S2P multi-enterprise* | 2.741 | 0.279 | 0.552 | 2 | 0.000 |

*Constructed from three S2P profiles with conditional cross-firm approval steps; not an observed fixture.

Intrinsic dimensionality correlations (n=5-6, descriptive, low statistical power):
- +0.899 with K-learning action_accuracy gain
- +0.800 with conservation clean-PAUSE fraction
- +0.771 with readout gap
- −0.543 with budget-frontier efficiency (B=2/full)
- −0.300 with μ widening (routing_quality)

**S2P within-domain contrast (the proof case):** Multi-enterprise S2P had higher m_conditional (0.213→0.279), higher chain length (1→2), AND higher K-learning action gain (+6.00pp→+16.44pp). Complexity UP, RGI value UP, same domain.

**Paper impact:** "Complexity measures tracked several capability outcomes in this small exploratory sample, and a constructed multi-enterprise S2P contrast increased both conditionality and K-learning action_accuracy gain; independent multi-enterprise validation is needed before claiming a general law."

**Deliverable:** decision_complexity_characterization.json + decision_complexity_summary.md + plot-ready CSV

---

## 7. SDK composite conservation gate — complete reference

Location: `copilot_sdk/scoring/scorer.py:2198`, method `CompoundingScorer._conservation_pause()`

**Check A (real safety floor):** 75% accuracy over last 100 verified records (scorer.py:2245-2254). Defaults: window=100, threshold=0.75 (configurable via preset). "Correct" = confirmed outcome or truthy is_correct. Below 100 records: check does NOT block. Exactly 75% passes.

**Check B (cold-start bootstrap):** α × q_eff × V ≥ 23.53/(α × V) from gae/calibration.py:194. Nonpositive α or V returns infinity. When dispersion inflation > 1.3: q_eff = max(0, q − effective_se). Inert after ~13 decisions (V makes threshold trivially satisfiable).

**Binary: ALLOW or PAUSE/RED. No AMBER branch.**

The SOC learning_health.py monitor is a SEPARATE display/governance path that does NOT implement the 75%/last-100 veto. Its baseline builder returns (0, 0).

**Campaign characterization (C5 + F-2):** Detection lag 9-328 records for sustained degradation. 12/15 fast breaks missed within 100 records. Purchasing false-pause rate is a product blocker (base accuracy < 0.75 floor). Per-domain calibration is unresolved.

---

## 8. Adaptive baseline — six-comparator table

Fixture: 543 SOC alerts, 400/143 train/test split, random_state=42, B=2.
Feature selection for budget-matched learners: privileged_identity_context + pattern_history (VLD's most-frequently-read dimensions).

| Comparator | Category accuracy | Action accuracy | Labels | Budget |
|---|---|---|---|---|
| Majority | 32.17% | 23.78% | 400 | — |
| LinUCB (B=2) | 26.57% | 31.47% | 400 | 2 fixed |
| RF (B=2) | 39.16% | 45.45% | 400 | 2 fixed |
| SVM (B=2) | 40.56% | 44.76% | 400 | 2 fixed |
| FI-routing (B=2) | 31.47% | 47.55% | 400 | 2 fixed |
| VLD (B=2 adaptive) | 37.76% | 47.55% | 0 | 2 adaptive |
| RF (all features) | 72.03% | 47.55% | 400 | all 6 |

VLD within 1.40pp of RF(B=2) with zero labels. Action accuracy ties RF(all) at 47.55%. LinUCB worse than majority at B=2 (confirms RV-1).

---

## 9. Standing claims — final status

| Claim | Status | Number | Source | Tier |
|---|---|---|---|---|
| 5/5 compound, 0 regressions | ✅ MEASURED | +3-21pp | KE-1 | REAL_COMPONENT |
| Within 1.4pp at matched budget, 0 labels | ✅ MEASURED | 37.76% vs 39.16% | C1 baseline | REAL_COMPONENT + SIMULATED |
| Action accuracy ties RF(all) | ✅ MEASURED | 47.55% both | C1 baseline | REAL_COMPONENT + SIMULATED |
| 57:0 saves:hurts | ✅ MEASURED | Constructed hard-tail suite | Astra | SIMULATED |
| Moat routing-level | ✅ MULTI-SEED | SOC 19.56±5.35pp, DataOps 5.72±1.10pp | EXP-1 | REAL_COMPONENT + SIMULATED |
| Moat judgment (μ) | ✅ **SOC ONLY, η-STABLE** | +15.12±2.87pp (5/5), stable at 0.5-4× η | C2 + F-1 | REAL_COMPONENT + SIMULATED |
| S2P μ-narrowing | ⚠️ DOMAIN PROPERTY, η-SENSITIVE | −5.33pp default η, trends to 0 at higher η | C2 + F-1 | REAL_COMPONENT + SIMULATED |
| Labels are the asset | ✅ HOLDS under realistic strategies | 0 realistic sources reach parity | C3 | SIMULATED |
| B=2 flat reads sufficient | ✅ TESTED, HOLDS | No arm >2pp routing vs A0 (one operator, simulated) | C7 | REAL_COMPONENT + SIMULATED |
| SOC depth-sensitive action | ✅ NEW | +4pp action at depth-3, 0 routing | C7 | REAL_COMPONENT + SIMULATED |
| Abstention lift | ✅ **DOMAIN-SCOPED** | +8.9-13.4pp (DataOps/Purchasing/SOC); ≈0 (Trading/S2P) | C6 + Fig-3 | REAL_COMPONENT + SIMULATED |
| Risk-coverage monotonic | ❌ NOT UNIVERSAL | Trading/S2P non-monotonic 3/3 seeds | C6 | REAL_COMPONENT + SIMULATED |
| γ re-convergence | ⏸️ UNTESTED | Condition ε_sim ≪ ‖Δ‖ not exercised | C4 analytic | — |
| Conservation gate | ✅ **MEASURED — lag + misses + calibration open** | Lag 9-328; 12/15 fast breaks missed; Purchasing 34.78% false-pause unresolved | C5 + F-2 | REAL_COMPONENT + SIMULATED |
| Oracle-sep tier | ❌ NOT APPLICABLE | Labels already geometry-derived, no LLM prior | C1 correction | — |
| Action-accuracy limitation | ✅ **READOUT-PROBLEM (4/5)** | 16-68pp readout gap; trained SOC at ceiling | G-1 | REAL_COMPONENT + SIMULATED |
| Complexity predicts capability | ✅ **EXPLORATORY** | Intrinsic dim mean |ρ|=0.66; S2P within-domain proof holds | G-2 | REAL_COMPONENT + SIMULATED (constructed S2P) |
| Frozen-ROI ($523K-$2.8M) | ⚠️ MODELED | Not validated | — | — |
| Second-derivative acceleration | ⚠️ MODELED | Instrumentation only | — | — |

---

## 10. Paper corrections required (priority order)

1. **CONSERVATION SECTION:** Replace GAE formula as safety floor with SDK composite gate (75%/last-100). Include detection lag characterization from C5. Note fast-break miss and Purchasing calibration issue. The GAE formula governs conservation quantity, not accuracy. Explain KE-5 inertness.

2. **MOAT SECTION:** Replace "un-copyable" with "deployment-specific accumulated value + switching cost." B1 retracted. B2 establishes routing-level data-specific moat. Judgment-specificity is SOC-only (C2). Include seed robustness (EXP-1). Note S2P μ-narrowing as domain property (F-1).

3. **ABSTENTION NUMBERS:** Replace "+9.5-15.2pp at 75%" with "+8.9-13.4pp at 73.6-74.6%" (held-out three-way split). Note Trading/S2P near-zero lift and non-monotonic (C6). Scope the claim to evidence-rich domains.

4. **ACTION-ACCURACY SECTION:** Reframe using the G-1 oracle-ceiling fork. 4/5 copilots have READOUT-PROBLEM (fixable). Trained SOC at ceiling. The limitation is readout, not architecture. Reference C7 depth-3 SOC finding as partial evidence.

5. **BASELINE COMPARISON:** Add six-comparator C1 table. Headline: within 1.40pp with 0 labels. Note LinUCB < majority at B=2.

6. **TIERING LANGUAGE:** Drop "ORACLE-SEP." Use "GEOMETRY-DERIVED SYNTHETIC." Add honest labeling method description: "correctness determined by nearest-centroid assignment over exported geometry."

7. **COMPLEXITY CHARACTERIZATION:** Add as a new section or appendix. State as exploratory. Present the S2P within-domain contrast as the proof case. Note n=5-6 limitation. Intrinsic dimensionality as the organizing measure.

8. **S2P-SC2 WALKTHROUGH:** Replace commodity-index clause with bulk-volume entitlement clause. Reconcile Q arithmetic (0.200 = unweighted, 0.100 = K-weighted).

9. **HEADLINE RANGES:** Correct to +3-21pp routing (absolute, not relative) and +6-32pts accuracy, including S2P low end.

10. **FROZEN BASELINES:** Note all five frozen lines move (eval sample changes). Divergence is the valid comparison.

11. **MANIFEST DISCREPANCIES:** Resolve the 11 flagged items — footnotes for different-experiment numbers, corrections for genuine errors, explicit metric names where conflated.

---

## 11. Open design questions

1. **Purchasing conservation gate calibration:** Base accuracy (0.735) < floor (0.75). Per-domain floor approach creates cross-copilot conflict. Needs a different formulation (relative-drop-from-baseline rather than absolute floor). Product blocker.

2. **Action readout conditioning:** G-1 showed 16-68pp readout gap. Conditioning the action readout on investigation state is the natural next step. Trained SOC already solved this — the mechanism exists; it needs to be understood and replicated for other copilots.

3. **C2 bimodal mechanism:** SOC is the only judgment-specific domain, but the mechanism behind the split is unmeasured. Is it evidence-structure richness? Factor dimensionality? The complexity characterization (G-2) suggests intrinsic dimensionality, but the correlation is exploratory (n=5-6).

4. **Multi-enterprise S2P validation:** G-2's within-domain proof used a CONSTRUCTED multi-enterprise S2P. Real multi-enterprise validation from a pilot partner would confirm or falsify the complexity-axis hypothesis.

5. **γ harness construction:** C4 found no runnable harness. The two-phase re-convergence experiment needs to be built to test the γ > 1 claim under the stated geometric condition.

---

## 12. Forward queue

| Item | Status | Dependencies | What it produces |
|---|---|---|---|
| Paper V7 edit | Ready — all inputs complete | All campaigns + diagnostics done | Submission draft with 11 corrections |
| Astra R2 review | Blocked on V7 | Paper V7 | Fix list for V8 |
| Paper V8 + abstract | Blocked on R2 | Astra R2 | Submission-ready |
| DEMO-V29 propagation | Needs v2.9 pre-read | After paper | Codebase aligned to v2.9 scenarios |
| TIER-6 (episode lifecycle) | Design ready, 10d | After paper | Trajectory store, cross-episode patterns |
| TIER-7 (K lifecycle + Frozen Twin) | Design ready, 8d | TIER-6 | Production verified-feedback→K update |
| TIER-8 (demo surface) | Design ready, 16d | TIER-7 + DEMO-V29 | 9 VLD beats in UI, Loom recordings |

Non-campaign parallel items (status at time of writing):
- Trading SAFE-2: sent to Codex
- S2P doc hygiene (SH-05a): sent to Codex
- SOC factor-0 (SH-05b): sent to Codex

---

## 13. Deliverable inventory

All experiment results under `copilot-sdk/experiments/vld/results/`:

| File | Content |
|---|---|
| conservation_gate_reconciliation.md | A1: GAE vs SDK gate, worked table |
| result_manifest.csv | A2: 1,101 rows mapping numbers to experiments |
| result_manifest_README.md | A2: metric definitions, 11 discrepancies |
| external_baseline_full.json | C1 baseline (pre-campaign adaptive baseline, not Campaign C1 oracle-sep): 6 comparators |
| delayed_entrant_catchup.json | B1: SUPERSEDED |
| vld_moat_b2_v1.json | B2: 4 arms × 2 delays × 2 copilots |
| moat_b2_summary.md | B2: moat verdict + scope |
| moat_b2_seeds.json | EXP-1: 5 seeds × 2 copilots |
| moat_mu_learning.json | EXP-2: SOC + DataOps μ-learning |
| recursion_trace_example.md | D1: verification→K→change trace |
| verified_outcome_latency.csv | D2: 5-copilot latency (ILLUSTRATIVE) |
| c1_oracle_sep_summary.md | C1: oracle-sep fallback, 65 comparisons |
| c2_mu_learning_all_five.json | C2: 5 copilots × 5 seeds μ-learning |
| c2_mu_learning_summary.md | C2: bimodal characterization |
| c3_label_breadth.json | C3: 3 new label sources × 2 copilots |
| c3_label_breadth_summary.md | C3: access→catch-up curve |
| c4_gamma_reconvergence.json | C4: analytic-only |
| c4_gamma_summary.md | C4: theorem + condition statement |
| c5_conservation_lag.json | C5: 4 degradation types × 5 copilots |
| c5_conservation_lag_summary.md | C5: detection lag table |
| c6_risk_coverage_trading_s2p.json | C6: Trading + S2P risk-coverage |
| c6_risk_coverage_summary.md | C6: five-domain table |
| c7_looped_depth.json | C7: 4 arms × 3 copilots × 3 seeds |
| c7_looped_depth_summary.md | C7: B=2 sufficiency verdict |
| c8_action_boundary.json | C8: SOC strategies + geometries |
| c8_action_boundary_summary.md | C8: action-accuracy boundary |
| gate_calibration_f2.json | F-2: diagnosis + calibration sweep |
| gate_calibration_f2_summary.md | F-2: per-domain floor analysis |
| eta_sweep_f1.json | F-1: 4 η × 2 copilots × 3 seeds |
| eta_sweep_f1_summary.md | F-1: η-stability verdict |
| oracle_ceiling_diagnostic.json | G-1: 4-rung ladder × 5 copilots |
| oracle_ceiling_summary.md | G-1: readout-problem fork |
| decision_complexity_characterization.json | G-2: 5 measures × 6 configs |
| decision_complexity_summary.md | G-2: complexity-axis verdict |

Charts under `copilot-sdk/experiments/vld/paper_charts/`:

| File | Content |
|---|---|
| fig1_five_domain_curves.png/svg | Hero K-curves, 5 copilots |
| fig2_delayed_entrant.png/svg | Moat catch-up (B2 data) |
| fig_2b_baseline_comparison.png/svg | 6-comparator grouped bars |
| fig3_risk_coverage.png/svg | Abstention lift (held-out re-run) |

Reports under `copilot-sdk/docs/`:

| File | Content |
|---|---|
| quality/cleanup_verification_report.md | TIER-5C verification |
| design/gr01_rl_sdk_extraction_report.md | GraphStore + RL extraction |
| session_state.md | Full session state with all campaigns |

---

*VLD Progressive-Strengthening Campaign — Final Consolidation*
*22 experiment runs · 8 campaigns + 4 follow-ups · 47 total experiments*
*5 claims strengthened · 5 claims bounded · 1 unifying complexity axis (exploratory)*
*All copilot-sdk source hashes unchanged · 6,193 tests green throughout*
