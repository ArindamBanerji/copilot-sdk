# Purchasing Copilot v1.4 Feature Gap Analysis

Date: 2026-08-17  
Scope: `copilot-sdk/apps/purchasing`, `copilot-sdk/copilot_sdk`, purchasing backend tests, and `copilot-sdk/e2e/purchasing`.  
Authority: finalized PD v1.4 and `purchasing_copilot_addendum_FINAL_v1.md`.

## Executive summary

The old MAP audit is not a v1.4 audit. Its Tier 5 items P64–P75 and supplements R7–R17 cover the original purchasing surface and report those items closed, but they do not contain the finalized v1.4 feature manifest. The finalized PD’s Appendix A mentions proposed follow-on IDs #110–#116, but those entries are not present in `master_action_plan_v5.228 (1).md`; they are unincorporated PD planning text, not MAP coverage.

The original F1–F22 surface is mostly implemented. The important exceptions are semantic or gating gaps: F11 Signal Analysis is present but its PD-required F26 Discovery Gate is absent, and F17 has delivery/consolidation plumbing but no clearly named supplier-consolidation implementation.

The new finalized features are not the same as the labels in the task prompt. The PD defines F23–F29 as Proof Ledger, Handoff Pack, Time-to-Competence, Discovery Gate, Frozen Twin, Pre-Order Belief Capture, and Yield-Adjusted Quote Audit. The prompt instead names Decision-Change Proposal, Compounding Ledger, Promotion Workflow, Frozen Twin, Counterfactual, Confidence Panel, and Day-0 Readiness. Both vocabularies were searched; this report uses the finalized PD IDs and records prompt-label matches separately.

## 1. Feature manifest and status

The PD expresses priority as release tier rather than literal P0/P1/P2. For this report: v1.0 = P0, v1.1 = P1, v2.0 = P2, and ARCH = architectural/roadmap. “LIVE” requires backend implementation, mounted API surface, tests, and a product-facing frontend surface. Evidence counts are keyword-hit files and test definitions; shared files can count for more than one feature and are not claims of feature-pure test isolation.

| ID | Feature | Priority / PD section | Origin | Status | Implementation evidence | Tests / frontend evidence | MAP coverage |
|---|---|---|---|---|---|---|---|
| F1 | Spend Dashboard | P0 / §7.2 | Original | LIVE | `services/spend_dashboard.py:13`; `routers/spend_router.py:26`; mounted `main.py:797` | `test_spend_dashboard.py` and provenance tests; `SpendSummaryPanel.tsx`; `spend-dashboard.spec.ts` | P68 closed |
| F2 | Delivery Match | P0 / §7.2 | Original | LIVE | `routers/match.py:55`; mounted `main.py:775` | `test_match_queue.py` (21 matching test definitions); `MatchResultPanel.tsx`; order E2E coverage | P69 closed |
| F3 | Smart Order Queue | P0 / §7.2 | Original | LIVE | `routers/queue.py`; mounted through the application | `test_match_queue.py` / factor tests; `OrderQueuePanel.tsx`; order E2E | P70 closed |
| F4 | Evidence Panel | P0 / §7.2 | Original | LIVE | `routers/evidence.py:21`, endpoints at lines 24, 53, 70, 96 | `test_evidence.py` (9 feature-relevant tests); audit/evidence frontend surfaces; day-zero/order E2E | P71/P72 evidence portions |
| F5 | One-Click Verify | P0 / §7.2 | Original | LIVE, loop proof incomplete | `routers/verify_router.py:59`; POST handler at line 74; mounted `main.py:813` | `test_verify.py` (20+ definitions); verify E2E | P71 closed, but §7.3 closure not independently demonstrated |
| F6 | Conservation Dashboard | P0 / §7.2 | Original | LIVE | Shared conservation router plus purchasing evidence/status routes; mounted shared routers in `main.py:746–773` | conservation/evidence/auto-order tests; `AutoOrderPanel.tsx`, dashboard surfaces; 6 purchasing E2E files hit | P72 closed |
| F7 | Auto-Approve Engine | P0 / §7.2 | Original | LIVE | `services/auto_order.py`; `routers/auto_order_router.py:29`; mounted `main.py:776` | `test_auto_order.py` (21 definitions); `AutoOrderPanel.tsx`; `auto-order.spec.ts` | P72 closed |
| F8 | Par Level Intelligence | P0 / §7.2 | Original | LIVE | `routers/par_router.py:19`; predictive-par route in `main.py:638`; optimizer/predictive services | `test_par_optimizer.py`, `test_predictive_par.py`; ParLevel panels; par E2E coverage | P73 closed |
| F9 | IKS Tracker | P0 / §7.2 | Original | LIVE | `routers/iks.py:19`; scorecard/IKS routes mounted `main.py:774,793` | `test_iks_trust.py`, scorecard/evidence tests; `IKSTrackerPanel.tsx`; scorecard/performance E2E | P74 closed |
| F10 | Supplier Scorecard | P0 / §7.2 | Original | LIVE | `services/supplier_scorecard.py`; `routers/scorecard_router.py:27`; mounted `main.py:793` | `test_scorecard.py`; `SupplierScorecardPanel.tsx`; `scorecard.spec.ts` | P74 closed |
| F11 | Signal Analysis | P0 / §7.2; gated by F26 | Original | PARTIAL | `routers/signal_router.py:12`; supplier signal and trust services | `test_predictive_par.py` and trust-related tests; `TrustRadarPanel.tsx` and supplier intelligence surfaces | P75 closed as trust analysis, but v1.4 gate dependency is absent |
| F12 | Weather Intelligence | P1 / §7.4 | Original | LIVE | weather factor/provider and context routes | weather tests and `weather.spec.ts`; weather impact UI | R7 closed |
| F13 | Event Intelligence | P1 / §7.4 | Original | LIVE | event router and event planner services | `test_event_planner.py`; event/analysis E2E; event UI surfaces | R10 closed |
| F14 | Day-of-Week Model | P1 / §7.4 | Original | LIVE | `services/day_of_week.py`; context/factor routes | factor/context/evidence tests; `DayOfWeekChart.tsx` | R8/R9-related coverage; no separately named MAP row |
| F15 | Commodity Decomposition | P1 / §7.4 | Original | LIVE | commodity provider/router and spend integration; mounted `main.py:798` | commodity/provider/spend tests; `CommodityPricePanel.tsx`; `commodity.spec.ts` | R16 closed |
| F16 | Cross-System Discovery | P1 / §7.4 | Original | LIVE | `services/cross_discovery.py`; `routers/discovery_router.py:28`; mounted `main.py:787` | `test_cross_discovery.py` (12 definitions); `DiscoveryDigestCard.tsx`; `discovery.spec.ts` | R14 closed |
| F17 | Supplier Consolidation | P1 / §7.4 | Original | PARTIAL | delivery coordinator/router at `routers/delivery_router.py:13`; chain/multi-unit plumbing | delivery/coordinator tests and `DeliveryScheduleCard.tsx`; delivery E2E | R11/R12 cover adjacent delivery/chain behavior, not a dedicated supplier-consolidation MAP item |
| F18 | AgentEvolver | P1 / §7.4 | Original | LIVE | `evolver_config.py`; shared evolution router mounted `main.py:746`; variant persistence | `test_evolution_purchasing.py`; lifecycle/evolution UI; dashboard/flows E2E | MAP #112 is an older PUR-AE-VARIANTS item and is closed |
| F19 | Disruption Recovery | P2 / §7.5 | Original | LIVE | `services/disruption_recovery.py:9`; routes in `main.py:656–662` | `test_disruption_recovery.py`; `DisruptionRecoveryPanel.tsx`; `disruption-recovery.spec.ts` | No distinct P64–P75/R7–R17 row found |
| F20 | Multi-Location Transfer | P2 / §7.5 | Original | LIVE | chain/multi-unit routers mounted `main.py:784,800` | chain/multi-unit tests; `ChainTransferCard.tsx`; chain-transfer E2E | R11/R17 closed |
| F21 | Payment Timing Intelligence | P2 / §7.5 | Original | LIVE | `services/payment_timing.py:8`; routes `main.py:664–670` | `test_payment_timing.py`; `PaymentTimingPanel.tsx`; payment-timing E2E | No distinct P64–P75/R7–R17 row found |
| F22 | Audit & Export Pack | P2 / §7.5 | Original | LIVE | `services/audit_export.py:12`; routes `main.py:672–682` | `test_audit_export.py` (8 tests); `AuditExportPanel.tsx`; audit-export E2E | Adjacent audit/provenance coverage; no distinct v1.4 row |
| F23 | Proof Ledger | P0 / §8.2 | **NEW** | PARTIAL | Generic evidence/audit/conservation-proof endpoints exist (`routers/evidence.py:96`, `AuditExportService`), but no `ProofLedger`, two-curve model, attribution hierarchy, or honest-$0 computation | Generic evidence/audit tests and `AuditExportPanel`; no Proof Ledger panel/E2E | **MAP-MISSING in v5.228**; PD Appendix proposes #110 |
| F24 | Handoff Pack | P0 / §8.2 | **NEW** | GAP | No Handoff Pack service, builder, endpoint, or schema found | No dedicated tests, panel, or E2E | **MAP-MISSING in v5.228**; PD Appendix proposes #111 |
| F25 | Time-to-Competence Meter | P1 / §8.3 | **NEW** | GAP | General evolution/promotion code is not a re-convergence-time metric | No dedicated tests, panel, endpoint, or E2E | **MAP-MISSING in v5.228**; PD Appendix proposes #112 |
| F26 | Discovery Gate (+ “Not Yet”) | P0 / §8.4 | **NEW** | GAP | No DiscoveryGate, evidence-floor gate, OOS confirmation, or selection-adjusted statistic; incidental “not yet” strings are not implementation | No dedicated tests, endpoint, or panel | **MAP-MISSING in v5.228**; PD Appendix proposes #113 |
| F27 | Frozen Twin | P2 / §8.5 | **NEW** | PARTIAL | Generic counterfactual plumbing exists (`context_router.py`, shared `counterfactual_router.py`), but no checkpoint-based frozen baseline/replay object | `test_purchasing_backend.py` and analysis/sweep E2E cover generic counterfactuals; no FrozenTwin-specific test/UI | **MAP-MISSING in v5.228**; PD Appendix proposes #114 |
| F28 | Pre-Order Belief Capture | ARCH / §8.6 | **NEW** | GAP | No pre-order belief capture schema, prompt flow, or causal storage found | No dedicated tests, endpoint, panel, or E2E | **MAP-MISSING in v5.228**; PD Appendix proposes #115 |
| F29 | Yield-Adjusted Quote Audit | P1 / §8.7 | **NEW** | GAP | No yield-adjusted plate-cost, depletion, trim-waste, or quote-audit implementation found | No dedicated tests, endpoint, panel, or E2E | **MAP-MISSING in v5.228**; PD Appendix proposes #116 |

### Status totals

| Status | Count | IDs |
|---|---:|---|
| LIVE | 20 | F1–F10, F12–F16, F18–F22 |
| PARTIAL | 4 | F11, F17, F23, F27 |
| SCAFFOLDED | 0 | No class was counted as a feature merely because an unrelated class exists |
| GAP | 5 | F24–F26, F28–F29 |

The final row-level count is **LIVE 20 + PARTIAL 4 + GAP 5 = 29**. F23 and F27 are partial because adjacent evidence/counterfactual plumbing exists, but the v1.4 contracts are not implemented.

### Representative exact test counts

These are counts of actual `def test_` functions in the named files, not estimates from filenames:

| Surface | Backend tests | Purchasing E2E tests |
|---|---:|---:|
| Spend / F1 | `test_spend_dashboard.py`: 19 | `spend-dashboard.spec.ts`: 14 |
| Match / F2 | `test_match_queue.py`: 21 | `match-engine.spec.ts`: 7 |
| Queue / F3 | `test_match_queue.py`: 21 shared | `order-queue.spec.ts`: 9 |
| Evidence / F4 | `test_evidence.py`: 8 | `day-zero.spec.ts`: 3; `order.spec.ts`: 9 shared |
| Verify / F5 | `test_verify.py`: 16 | `verify.spec.ts`: 9 |
| Auto-approve / F7 | `test_auto_order.py`: 21 | `auto-order.spec.ts`: 10 |
| Par / F8 | `test_par_optimizer.py`: 21; `test_predictive_par.py`: 20 | `par-level.spec.ts`: 8; `predictive-par.spec.ts`: 6 |
| IKS / F9 | `test_iks_trust.py`: 10; `test_scorecard.py`: 15 | `scorecard.spec.ts`: 8; `trust-radar.spec.ts`: 8 |
| Discovery / F16 | `test_cross_discovery.py`: 12 | `discovery.spec.ts`: 6 |
| Disruption / F19 | `test_disruption_recovery.py`: 8 | `disruption-recovery.spec.ts`: 3 |
| Payment / F21 | `test_payment_timing.py`: 8 | `payment-timing.spec.ts`: 3 |
| Audit / F22 | `test_audit_export.py`: 8 | `audit-export.spec.ts`: 3 |
| Cohort/readiness alias | `test_cohort_status.py`: 12 | `cohort-status.spec.ts`: 9 |

Shared backend files such as `test_purchasing_backend.py` intentionally are not attributed wholesale to a single feature. No dedicated test file was found for F23–F29.

## 2. New-feature gap list: F23–F29

| Feature | What exists | Missing | Recommended build | Effort |
|---|---|---|---|---:|
| F23 Proof Ledger | Flat evidence, audit export, conservation proof | Proof Curve, Competence Curve, attribution hierarchy, honest-$0 behavior, persistent ledger contract | Add an explicit domain-agnostic proof ledger with claim-level provenance/substantiation and UI showing both curves | 1.5 weeks (PD Appendix #110) |
| F24 Handoff Pack | Audit export can be downloaded | Single-page operational transfer pack derived from accumulated judgment | Define versioned handoff schema, generator, endpoint, panel, and provenance tests | 1 week (#111) |
| F25 Time-to-Competence | Evolution variants and lifecycle telemetry | Re-convergence measurement per supplier/manager/menu/shock and time-series display | Add event anchors, convergence detector, stored metric, and panel | 1 week (#112) |
| F26 Discovery Gate | Generic discovery/counterfactual surfaces; F11 signals | Evidence floor, OOS confirmation, partial pooling, selection-adjusted statistic, explicit “Not Yet” outcome | Implement shared gate before F11 claims and test false-positive/insufficient-evidence paths | 1.5 weeks (#113) |
| F27 Frozen Twin | Generic counterfactual card/router | Immutable checkpoint snapshot and replay against a frozen baseline | Add checkpoint identity, replay service, comparison API, and read-only UI | 2–3 weeks (#114) |
| F28 Pre-Order Belief Capture | No matching implementation | Pre-deviation prompt, structured belief, causal linkage to later outcome | Architecture/spec first; implement only after schema and privacy review | ARCH (#115) |
| F29 Yield-Adjusted Quote Audit | Existing commodity/order data, but no yield semantics | POS depletion, trim/waste, net plate cost, gross-vs-net quote audit | Add source contract and audit calculation; do not infer yield from generic price data | 1 week (#116) |

## 3. Verify-in-code results

### §7.3 compounding-loop precondition

The purchasing verify path is real and dependency-injected: `create_verify_router` is defined at `app/routers/verify_router.py:59`, its POST handler starts at line 74, and it calls `_learn_with_context` at the verification path. `_learn_with_context` calls the injected state’s `learn()` or scorer’s `learn()` at lines 170–195. The response projection exposes `iks_before`, `iks_after`, and `centroid_delta` at lines 227–245.

This proves the **verified decision → learn invocation → learning telemetry** half of §7.3. It does not prove the full precondition, which requires scoring a later comparable decision and demonstrating a measurable improvement. Existing tests verify that learn is called and that counts/payload fields change; no dedicated purchasing test was found that performs score-before, verify, score-after on a controlled repeated case and asserts the later score improves. Classification: **PARTIAL / NEAR**, not LIVE under the PD’s “one-grep” rule.

### Banned vocabulary check

The requested scan is not clean. `app/routers/verify_router.py:48` defines `reward_raw`, and `app/routers/verify_router.py:238` exposes it in the response projection. These are production-app hits outside tests/comments. The purchasing app therefore still leaks retired reinforcement-learning vocabulary through an API model, even though the core product language is otherwise purchasing-oriented. Recommended action: rename the wire field through a compatibility plan, or explicitly document it as an internal legacy field before removal; do not silently change an external response contract.

### §12.0 legal-exposure framework

No dedicated legal-exposure policy/service/router was found for antitrust-safe benchmarking, supplier-disparagement controls, de-identification, franchise transfer boundaries, or auto-approval separation of duties and revoke logging.

There is only adjacent evidence/status metadata: `app/graph_status.py:433–461` reports receipt mapping as `excluded_first_cutover` / `design_required` and `evidence_receipt_mapping_complete: False`. That is an honest disclosure of an incomplete evidence mapping, not implementation of §12.0. Classification: **GAP at framework level**, with a useful honesty signal that should be retained.

## 4. MAP reconciliation

The audited MAP’s Tier 5 rows P64–P75 are closed for the older surface: P68 spend, P69 match, P70 queue, P71 verify, P72 conservation/auto-order, P73 par, P74 IKS/scorecard, and P75 trust analysis. R7–R17 likewise cover weather, waste/menu, event, chain transfer, delivery, predictive par, cross discovery, alerts, economics, and multi-unit behavior. Those rows substantiate the strong F1–F22 implementation footprint; they do not establish v1.4 feature coverage.

The MAP file contains no matches for the finalized F23–F29 names or for `#110`–`#116` as the new v1.4 items. It does contain unrelated historical IDs such as #110/#112 in older sections, so numeric ID reuse must not be treated as coverage. The PD Appendix A’s #110–#116 proposals should be promoted into the next MAP revision with unique IDs or an explicit reconciliation note.

## 5. Recommended MAP additions

| Proposed item | Scope | Priority | Dependency | Effort |
|---|---|---|---|---:|
| PUR-PROOF-LEDGER | F23 two-curve ledger, attribution, honest-$0 UI/API/tests | P0 | F5, F22, evidence/provenance contracts | 1.5w |
| PUR-HANDOFF-PACK | F24 generated handoff pack and export tests | P0 | F18, F22, provenance | 1w |
| PUR-DISCOVERY-GATE | F26 evidence floor, OOS, partial pooling, “Not Yet” | P0 | F11, shared evidence API | 1.5w |
| PUR-COMPOUNDING-LOOP | §7.3 score→verify→learn→later-score experiment and metric | P0 | F5, real scorer/store, seeded repeat case | 1–2w |
| PUR-LEGAL-EXPOSURE | §12.0 policy model, field-level controls, audit/revoke tests | P0 | F5, F22, product/legal review | 1.5–2w |
| PUR-TIME-TO-COMPETENCE | F25 convergence metric and panel | P1 | PUR-COMPOUNDING-LOOP, event anchors | 1w |
| PUR-YIELD-AUDIT | F29 yield/depletion/trim-waste quote audit | P1 | POS and supplier data contracts | 1w |
| PUR-FROZEN-TWIN | F27 immutable checkpoint replay | P2 | durable checkpoint contract, scorer snapshotting | 2–3w |
| PUR-BELIEF-CAPTURE | F28 architecture and later implementation | ARCH | privacy/schema decision | discovery first |

## 6. Priority queue

### Demo-blocking / P0

1. PUR-COMPOUNDING-LOOP: close the §7.3 proof gap with a real later-score experiment.
2. PUR-DISCOVERY-GATE: build the missing prerequisite for F11’s v1.4 claims.
3. PUR-PROOF-LEDGER: avoid presenting flat audit output as the two-curve Proof Ledger.
4. PUR-HANDOFF-PACK: implement the missing transfer artifact.
5. PUR-LEGAL-EXPOSURE: define guardrails before exposing stronger autonomy, comparison, or supplier claims.
6. Resolve or quarantine the `reward_raw` production response field.

### Pilot-blocking / P1

7. PUR-TIME-TO-COMPETENCE, because it depends on measurable learning rather than static evolution status.
8. PUR-YIELD-AUDIT, because gross quote comparisons are not net plate-cost evidence.
9. Decide whether F17’s adjacent delivery consolidation is sufficient or needs an explicit supplier-consolidation service.

### v1.1 / P2 follow-on

10. PUR-FROZEN-TWIN after durable checkpoint identity and replay semantics are available.
11. PUR-BELIEF-CAPTURE after architecture, privacy, and causal-storage decisions.

## 7. Key risks and conclusions

- **Highest-risk P0 gaps:** F24 Handoff Pack and F26 Discovery Gate are complete gaps; F23 is only a generic evidence/audit approximation. F11 should not be called fully v1.4-complete while F26 is absent.
- **Semantic false positive:** `AuditExportPanel`, `conservation-proof`, `CounterfactualCard`, and `CohortStatusPanel` are useful adjacent surfaces, but their names or generic behavior do not satisfy the finalized F23, F27, or F29 contracts.
- **Prompt/PD drift:** the task’s alternate F23–F29 labels are not the finalized manifest. In the alternate vocabulary, “Counterfactual” is PARTIAL, “Day-0 Readiness” is PARTIAL via `/api/purchasing/cohort-status` and `CohortStatusPanel`, while “Decision-Change Proposal”, “Compounding Ledger”, “Promotion Workflow”, and “Confidence Panel” have no feature-specific implementation. This does not change the authoritative PD classification.
- **Repository path drift:** the prompt names `$CLAUDE_SDK/packages/copilot-sdk/copilot_sdk/`; this checkout’s shared SDK path is `copilot-sdk/copilot_sdk/`. The scan used the actual checkout path.
- **MAP conclusion:** the old “zero gaps” result is valid only for the old audited scope. It cannot be used as evidence for v1.4 F23–F29.

## Source references

- PD manifest and build classes: `copilot-sdk/docs/design/product/purchasing_copilot_pd_v1_4.md:686–750`.
- §7.3 compounding precondition: same PD, `:752–791`.
- §12.0 legal exposure: same PD, `:1149–1176`.
- PD’s proposed #110–#116 appendix items: same PD, `:1296–1326`.
- Audited MAP Tier 5: `copilot-sdk/docs/design/master_action_plan_v5.228 (1).md:199–214`.
- Audited MAP R7–R17: same MAP, `:255–265`.
- Verify/learn path: `copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py:59–105,170–195,227–245`.
- Banned production field: same router, `:47–48,237–241`.
- Incomplete evidence mapping disclosure: `copilot-sdk/apps/purchasing/backend/app/graph_status.py:433–461`.
