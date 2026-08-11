# Bug Hunt v5-B Findings — Dimensions 7–11

**Date:** 2026-08-10  
**Mode:** read-only source and live-endpoint audit  
**Scope:** conservation, framework v5 integration, all frontends, critical-path test coverage, and SOC/SDK security/compliance  
**Source changes:** none. This document is the only requested artifact written.

## Executive result

Four P1 findings were confirmed. The required stop threshold was five P1 findings, so the audit continued through Dimensions 7–11. No fifth P1 was promoted from an unproven or demo-only condition.

| Severity | Confirmed | Disposition |
|---|---:|---|
| P1 | 4 | Remediation required before production/security claims |
| P2 | 8 | Fix or explicitly constrain before broad rollout |
| P3 | 5 | Hardening and test-quality work |

## P1 findings

| ID | Dimension | Finding | Evidence | Impact |
|---|---|---|---|---|
| P1-01 | 11d | SOC authentication is fail-open by default. `SAML_ENABLED` defaults to false, and the middleware returns `None` for every request in that mode. Startup explicitly announces that all routes are open. | `gen-ai-roi-demo-v4-v50/backend/app/auth/config.py:44-45`; `gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:37-43`; `gen-ai-roi-demo-v4-v50/backend/app/main.py:188-199` | A deployment that omits SAML configuration exposes every non-exempt SOC route without authentication. This is a production access-control failure, not merely a missing feature. |
| P1-02 | 11b | The EU AI Act dashboard converts two narrow local checks into legal/compliance status labels. Conservation GREEN becomes Article 9 `COMPLIANT`, and audit-chain verification becomes Article 15 `COMPLIANT`; no independent legal, risk-management, robustness, or cybersecurity assessment is required. | `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1497-1512`; `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1537-1555` | The response can present a product-generated “COMPLIANT” conclusion as regulatory evidence when only a conservation status or local hash-chain check passed. |
| P1-03 | 10d / 7b | SDK checkpoint rollback restores centroids and optionally counts, then freezes the scorer, but does not restore `scorer.decision_count` (or other learning-state counters). The saved decision count is returned only as metadata. | `copilot-sdk/copilot_sdk/framework/checkpoint.py:45-48`; `copilot-sdk/copilot_sdk/framework/checkpoint.py:150-163`; `copilot-sdk/copilot_sdk/framework/checkpoint.py:169-174` | After rollback, the scorer’s numerical state and its decision-volume state can describe different histories. Conservation thresholds, calibration gates, and subsequent learning decisions may be computed against post-checkpoint volume. |
| P1-04 | 7f | The live S2P conservation endpoint reported `V=191` and `correct_count=178`, while also reporting `categories_with_data=0`, `alpha=0`, `signal=0`, and a reason saying no verified decisions are available. The implementation derives alpha from category coverage and forces conservation failure when alpha or V is zero. | Live `http://127.0.0.1:8002/api/conservation/status` probe; `s2p-copilot/backend/app/routers/s2p.py:646`; `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:157-176`; `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:251-260` | Existing verified outcomes are being treated as having no usable category coverage. S2P remains RED despite nonzero verified/correct counts, which can block learning and misstate the reason for the block. The source/data contract mismatch must be resolved before trusting the status. |

## Dimension 7 — Conservation invariants

### 7a — Conservation boundary: PASS with a data-contract caveat

The SOC monitor does not allow “all categories correct” to bypass the evidence-volume guard. Empty history produces zero components in `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:100-101`; the SOC conservation adapter sets `V` from verified decisions and `alpha` from category coverage in `:157-176`; and `evaluate()` forces `theta_min` to the conservative sentinel when alpha or V is zero in `:251-260`. RED is selected when conservation fails in `:329-334`.

The edge case is therefore safe against accidental GREEN, but the S2P live mismatch documented as P1-04 shows that the category-coverage input can be wrong or unavailable even when verified outcomes exist.

### 7b — Conservation-to-scoring feedback: mostly enforced

`ProfileScorer.update()` checks `_paused_by_conservation` before mutation and returns `paused_conservation` without changing centroids in `graph-attention-engine-v50/gae/profile_scorer.py:838-851`. `set_conservation_status()` transitions the state machine and sets the pause flag for AMBER/RED in `:712-734`.

Scoring itself remains callable: `score()` is the read/classification path in `graph-attention-engine-v50/gae/profile_scorer.py:408-490`; conservation blocks learning mutation, not the ability to produce a score. This is the expected fail-safe separation. A caller can still receive a score while learning is paused, so the frontend must surface the conservation state alongside the score.

### 7c — Conservation reporting: contract is centralized in SDK, inputs are not uniform

The SDK conservation utility builds the response from store state and category counts in `copilot-sdk/copilot_sdk/backend/conservation_utils.py:202-254`. The shared response model is tested for the CC-4 fields in `copilot-sdk/tests/backend/test_conservation_cc4.py:23-66` and `copilot-sdk/tests/test_response_models.py:267-320`.

Live probes for S2P, Trading, Purchasing, and DataOps returned the required keys (`status`, `alpha`, `q`, `theta_min`, `signal`, `headroom`, `reason`). Their values differed as expected by tenant, but S2P’s category-coverage/verified-volume contradiction is a cross-service data problem, not a missing-key problem.

### 7d — Penalty asymmetry: implementation is parameterized; numeric recovery is not audited

The scorer computes its loss using the configured penalty ratio rather than a hard-coded 2:1 value; the SOC domain configuration owns the penalty setting in `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:825-840`, and the scorer’s conservation/scoring paths consume the configured profile. The requested “20:1, one incorrect decision, recovery V” scenario is not represented by a dedicated regression test. Existing tests exercise formula/status behavior but do not pin recovery volume under each penalty ratio: `gen-ai-roi-demo-v4-v50/backend/tests/test_learning_health.py:203-220`.

**Classification:** P2 test/observability gap, not a confirmed arithmetic defect.

### 7e — theta-min consolidation: PARTIAL FAIL

The canonical implementation is `graph-attention-engine-v50/gae/calibration.py:194-198`, and the exact pin `23.53 / (0.25 * 200)` is `0.4706`; the SDK tests pin this in `copilot-sdk/tests/test_conservation_formula.py:61-67`.

There is a second implementation in `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:825-840`. It duplicates the formula and guard rather than importing the canonical function. The canonical guard handles zero and negative values but does not reject NaN: `alpha=nan` or `V=nan` passes the comparison and returns NaN at `graph-attention-engine-v50/gae/calibration.py:195-198`.

**Classification:** P2 consolidation and non-finite-input gap. Zero/negative inputs safely return infinity; NaN is not covered by the stated invalid-input contract.

### 7f — Conservation payload completeness: PASS on keys, FAIL on semantic consistency for S2P

All four live SDK endpoints returned the required fields. The shared payload construction is visible at `copilot-sdk/copilot_sdk/backend/conservation_utils.py:237-254`, while category counts are obtained at `:361-370`. S2P’s live payload had nullable serialized `theta_min`/`headroom` because the underlying value is infinite and had the contradictory coverage/volume values described in P1-04.

### 7g — Auto-order threshold ratchet: PASS

Errors increase the threshold toward caution in `copilot-sdk/apps/purchasing/backend/app/services/auto_order.py:139-147`; high accuracy decreases it toward the configured floor in `:149-156`. The direction is covered by `copilot-sdk/apps/purchasing/backend/tests/test_auto_order.py:75-102`. No wrong-direction defect was found.

## Dimension 8 — Framework v5 integration

| Probe | Result | Evidence / classification |
|---|---|---|
| 8a category bounds | PASS | `graph-attention-engine-v50/gae/profile_scorer.py:424-430` rejects invalid category indexes and factor shapes before scoring. |
| 8b empty DK category | PASS with neutral fallback | `graph-attention-engine-v50/gae/dk_estimator.py:129-138` skips empty categories and retains neutral initial weights. This is conservative, not a divide-by-zero. |
| 8c shrinkage alpha boundary | PASS | `graph-attention-engine-v50/gae/shrinkage.py:30-74` validates alpha/ramp boundaries and rejects out-of-range values. |
| 8d strategy interactions | PASS / test gaps | Factor masks are applied in `graph-attention-engine-v50/gae/profile_scorer.py:447-453`; Phase-2 DK overrides are applied in `:458-476`; conservation pause and min-confidence gates are ordered in `:838-866`. Cross-product tests for factor mask + min confidence + auto pause are sparse. P2. |
| 8e promotion gate threshold | P2 | The batch gate has ordinary superiority/floor/variance checks at `graph-attention-engine-v50/gae/batch_pipeline.py:268-288`, but conservation is hard-coded true at `:279` and the result labels this `placeholder_always_pass` at `:294`. No production consumer was confirmed in this audit; treat the gate as unsafe for production promotion until wired to real conservation. |
| 8f novelty and `reestimate_dk()` | P2 | `reestimate_dk()` filters to correct buffered decisions and returns for fewer than two samples at `graph-attention-engine-v50/gae/profile_scorer.py:1050-1065`; it does not itself enforce novelty or a novelty-window contract. The trigger/policy boundary needs an integration test. |
| 8g centroid-history duplication | PASS | SDK owns the lineage/checkpoint routes at `copilot-sdk/copilot_sdk/backend/self_computation_router.py:416-430`; the SOC app comments that the route is shared at `gen-ai-roi-demo-v4-v50/backend/app/main.py:179` and no second implementation was found in the focused source search. |
| 8h DK weight transfer leak | P2 design risk, not confirmed leak | Counterfactual replay deliberately holds `dk_weights`/temperature fixed in `copilot-sdk/copilot_sdk/backend/self_computation_router.py:317-359`. This is correct for an ablation, but the contract should explicitly prevent this state from being promoted into the live scorer. |

## Dimension 9 — Frontend consistency

### 9a — Rapid selection race: GAP

No `AbortController` implementation was found in the source frontends. SOC alert loading and selected-alert enrichment are asynchronous in `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/AlertTriageTab.tsx:340-458`, and DataOps selection-dependent calls use `selectedAlertId` in `copilot-sdk/apps/dataops/frontend/src/screens/TriageScreen.tsx:245-299`. There is no source-level cancellation or request-generation guard in these paths.

**Classification:** P2. A slower response for alert A can overwrite state after the user selects alert B; an E2E timing test is also absent.

### 9b — Cross-tab counts after outcome: GAP

SOC outcome submission updates the local feedback path and navigates via a custom event, but no shared invalidation event for queue/count/learning-health data was found around `gen-ai-roi-demo-v4-v50/frontend/src/components/OutcomeFeedback.tsx:76-94` and `:263`. The App event listener is tab navigation at `gen-ai-roi-demo-v4-v50/frontend/src/App.tsx:108-114`, not data revalidation.

**Classification:** P2 stale-count risk. A reload or explicit refetch is required to establish cross-tab consistency.

### 9c — Error boundary: mixed

SOC has a class error boundary at `gen-ai-roi-demo-v4-v50/frontend/src/App.tsx:12-23` and mounts it around the active tab at `:189-191`. The SDK app frontends have API-level `response.ok` checks, for example `copilot-sdk/apps/dataops/frontend/src/api.ts:142-174`, but no shared React error boundary was found in the focused source search.

**Classification:** P2 for SDK frontends; SOC is covered for render errors but still relies on per-call handling for HTTP 500s.

### 9d — Production console errors: not executed; static concern confirmed

A production build was not run because this audit is read-only. Static source inspection found many unconditional `console.error`/`console.warn` calls, including `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/AlertTriageTab.tsx:431-458`, `:487-543`, and `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/CompoundingTab.tsx:702-815`. These may be useful diagnostics but are not gated by an environment logger.

**Classification:** P3 observability/build verification gap, not a confirmed runtime failure.

## Dimension 10 — Critical-path test coverage audit

| Probe | Covered scenarios | Gaps found | Classification |
|---|---|---|---|
| 10a `report_decision_outcome()` | Duplicate identical outcome and conflicting outcome are covered by the idempotency tests; route logic begins at `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1696-1752`. | Missing/unknown decision, graph write failure after feedback lookup, repeated concurrent submissions, and partial learning failure need explicit tests. | P2 |
| 10b `SimulationOrchestrator.run()` | Normal run, per-step ledger creation, category accuracy, and final result are exercised by `gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:248-626` and simulation tests. | Cancellation, two simultaneous runs sharing mutable state, and exception isolation between runs are not demonstrated by the focused tests. | P2 |
| 10c `LearningHealthMonitor.evaluate()` | Empty history, pre-activation, active empty history, calibration, degraded signal, and RED are covered in `gen-ai-roi-demo-v4-v50/backend/tests/test_learning_health.py:47-220`. | NaN/non-finite alpha/V, verified outcomes with missing category coverage, and exact theta sentinel serialization are not all pinned. | P2; overlaps P1-04 and 7e |
| 10d `CheckpointService.rollback()` | Centroid/count restore and freeze are implemented at `copilot-sdk/copilot_sdk/framework/checkpoint.py:118-174`; checkpoint contract tests exist. | Decision counter/state restoration and lineage-target validation are not complete; the counter omission is P1-03. | P1 |
| 10e ProfileScorer Phase 2 | Shape/bounds, update behavior, DK estimation, and phase-gate tests exist under `graph-attention-engine-v50/tests/test_profile_scorer.py`, `test_fw09_phase_b_gate.py`, and `test_update_edge_cases.py`. | Combined phase-2 + factor mask + confidence gate + conservation pause sequence is not a single integration scenario. | P2 |
| 10f `demo.py` preseed freshness | Preseed and no-reseed behavior are tested in `copilot-sdk/tests/test_preseed.py:1-` and `copilot-sdk/tests/test_preseed_demo_data.py:1-`; launcher flags are defined at `copilot-sdk/demo.py:1339-1357`. | No freshness/TTL assertion proves that an already-populated tenant is not silently treated as a fresh demo tenant; persisted state is intentionally reused by app startup, e.g. `copilot-sdk/apps/trading/backend/app/main.py:288-308`. | P2 |
| 10g ProvenanceBadge | New Trading/DataOps/S2P surfaces import badges, e.g. `copilot-sdk/apps/trading/frontend/src/components/VolatilityPanel.tsx:4,38`, `copilot-sdk/apps/dataops/frontend/src/screens/DashboardScreen.tsx:41,195`, and `copilot-sdk/apps/s2p/frontend/src/components/SituationPanel.tsx:92-170`. | No exhaustive inventory test proves every newly surfaced numeric value has a badge; fallback strings such as `illustrative`, `sample`, or `accumulating` are component-local. | P3 |

## Dimension 11 — Security and compliance

### 11a — PII/logging review

Top concerning statements found:

1. `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1710-1711` logs alert ID and outcome on every feedback request.
2. `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:893` logs decision ID and alert ID after graph write.
3. `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1913` logs a decision ID during outcome lookup.
4. `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:390-392` logs IOC values and alert IDs, including the exception path.
5. `copilot-sdk/copilot_sdk/framework/audit.py:145` logs decision ID, alert ID, and action.

These are identifiers and security-event metadata rather than raw credentials, but they are still traceable operational data. Redaction middleware exists in SOC at `gen-ai-roi-demo-v4-v50/backend/app/main.py:86`; no proof was found that process stdout logs pass through that middleware. **Classification: P2 logging/privacy hardening.**

### 11b — Certification language

The strongest issue is P1-02. Additional risky language includes “Three unconditional guarantees for board presentation” in `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1727-1731`, and mock benchmarking values returned by `:1738-1760` while the endpoint docstring says “mock data.” The mock endpoint is explicitly marked as such, which limits the finding, but UI/API consumers must preserve that label.

### 11c — CORS

The audited applications use environment-configured origins rather than literal wildcard origins. For example, SOC uses `CORS_ORIGINS` at `gen-ai-roi-demo-v4-v50/backend/app/main.py:50-60`, and S2P does the same at `s2p-copilot/backend/app/main.py:73-90`. SDK Trading allows credentials and all methods/headers at `copilot-sdk/apps/trading/backend/app/main.py:317-323`; Purchasing and DataOps have the same broad method/header pattern at `copilot-sdk/apps/purchasing/backend/app/main.py:444-448` and `copilot-sdk/apps/dataops/backend/app/main.py:576-580`.

**Classification:** P2 configuration risk. No literal `allow_origins=["*"]` was found in the audited application sources, but permissive environment values and credentialed CORS require deployment validation.

### 11d — SAML bypass

P1-01 is confirmed. The bypass is explicit and global, not route-specific: `require_auth()` returns `None` at `gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:37-43`, and startup prints “all routes open” at `gen-ai-roi-demo-v4-v50/backend/app/main.py:198-199`. The exempt-prefix list only matters when SAML is enabled (`:18-20`, `:53-54`).

## P1 stop-condition audit

Confirmed P1 count: **4**. The fifth-P1 stop condition was not reached. The following were deliberately not promoted to P1 without stronger proof:

- the GAE batch gate’s `placeholder_always_pass` conservation field, because no production consumer was confirmed in this focused trace;
- NaN theta-min behavior, because it is a contract gap that currently tends toward RED comparisons rather than a demonstrated GREEN bypass;
- frontend request races, because the stale-write sequence was statically plausible but not reproduced live in this read-only pass.

## Recommended order of work

1. Make SOC authentication fail-closed outside an explicit local-demo profile; add a route-level unauthenticated test.
2. Replace regulatory `COMPLIANT` labels with evidence-scoped/non-certifying language and require independent controls for any legal conclusion.
3. Restore the complete scorer state on rollback, including decision count and any conservation/calibration counters; add a post-rollback scoring test.
4. Reconcile S2P category coverage with verified-decision storage and add a live contract test for the full conservation payload.
5. Consolidate theta-min into the canonical GAE implementation and reject non-finite inputs.
6. Add request cancellation/generation guards, cross-tab invalidation, and a common SDK frontend error boundary.

## Verification limitations

This was a read-only audit. No source tests, frontend builds, or Playwright suites were run because they can create caches/reports and the task prohibited modifications. Live GET probes were used only for the conservation payload check. All findings above are based on source traces, existing tests read from disk, and the cited live response.
