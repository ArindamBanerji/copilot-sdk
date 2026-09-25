# Sweep 7 — Cross-repo contract verification

Date: September 18, 2026 (America/Los_Angeles).
Scope: copilot-sdk, s2p-copilot, gen-ai-roi-demo-v4-v50.
Method: bug_hunt_v5.md A–E; source inspection, AST import/call inventory, isolated real-object diagnostics, and live contract probes.
Disposition: review only. No fixes, service restarts, preseed, scoring/analyze mutations, or test-suite runs.

## Summary

**Nine ranked findings: 1 P1, 8 P2, 0 P3.** The most consequential drift is semantic: imports resolve, but adapters consume the wrong fields or expose incompatible meanings.

1. **P1 — S2P twin serialization drops the real action name**, silently corrupting live/frozen accuracy and missed-decision evidence.
2. **P2 — S2P's budget integration reads a nonexistent public decision_count**, so a warmed SDK scorer is treated as cold-start.
3. **P2 — Budget allocation receives situation-classifier confidence rather than action confidence**; correcting the counter alone leaves the default classifier allocating four reads even to easy inputs.
4. **P2 — SOC's “SDK-compatible” aliases do not satisfy SDK response schemas**, particularly conservation state and required engine metadata.
5. **P2 — The S2P twin panel consumes a drift contract that never supplies its required accuracy fields**, so healthy twin initialization cannot make the comparison render.

Additional findings: a twin GET writes governance events, SOC labels an elapsed-decision count as missed decisions, S2P advertises a frozen twin when none exists, and SDK framework helpers retain reverse dependencies on a consumer's app package.

### Coverage and confidence

- **202 SDK symbol-import occurrences statically resolved:** 122 S2P, 80 SOC.
- These represent **115 distinct module/symbol pairs**, **47 SDK import modules**, and **60 consumer files**.
- **201 direct imported-name call sites** inventoried: 106 explicitly signature-compatible; 2 compatible subject to dynamic arguments; 93 indirect/inherited/dataclass/constant calls not conclusively signature-checked by the static checker.
- No missing imported symbol or explicit direct-call argument mismatch was found.
- **Six response-contract families compared:** fingerprint, trajectory, conservation, investigation, frozen twin, investigation budget.
- **16 live HTTP probes:** 12 GETs and 4 investigation POSTs. Native SOC investigation returned 500; two SOC reads and Trading conservation returned 503. These block successful-response verification at those paths, not source review.
- This is **not** a claim that all imported abstractions are semantically correct, all methods are exercised, or every installed SDK copy equals the inspected checkout. Bound-method behavior, dynamic imports, and deployment module resolution require additional integration tests.
- The source-referenced GAE result declaration was also inspected to trace the SDK twin's returned object; GAE was not a fourth repository audit.

No LLM output was used as a correctness oracle. The action-name diagnostic used a real GAE ProfileScorer result, not a mocked scorer.

## SDK→S2P Import Verification

The complete occurrence ledger is in Appendix B. All 122 explicit SDK symbol imports in backend/app resolve in the local SDK checkout, including barrel re-exports.

| Integration | Producer contract vs consumer | Verdict |
|---|---|---|
| CompoundingScorer | S2P main constructs the shared scorer; its public verified-decision accessor is get_verified_count(), not decision_count | Import/signature resolves; budget accessor is wrong, F2 |
| AdaptiveBudgetPolicy | allocate(confidence, category, verified_count); cold-start return before history append | Called by S2P's SituationClassifier subclass, but both count and confidence semantics drift, F2/F3 |
| create_budget_router | Receives the same policy instance stored on app.state | Correct mounting; telemetry is not proof of effective adaptation |
| create_investigation_router | Provider, evidence factory, K store, classifier, factors, default budget match factory parameters | Canonical request is decision_id/category/factor_vector, not event_id/category alone |
| KUtilityStore | Requires a DB connection with the expected interface and a factor dimension | S2P supplies a connection shim for its local store; no direct constructor mismatch found |
| create_conservation_router / ScorerBackedProvider | Shared flat public status vs normalized internal promotion state | S2P uses shared routes; live response has verified_count and all three gate details |
| FrozenTwin / FrozenTwinStore | Raw scorer passed to twin scoring; score_parallel returns raw scoring results | Unwrapping is deliberate; result serialization is incompatible, F1 |
| Evolution/promotion/graph/state/auth/situation imports | Symbols and direct explicit call signatures checked; dataclass/inherited calls recorded separately | No unresolved exports; not a blanket behavioral certification |

Evidence: [s2p-copilot/backend/app/main.py:53](../../../s2p-copilot/backend/app/main.py:53), [s2p-copilot/backend/app/main.py:247](../../../s2p-copilot/backend/app/main.py:247), [s2p-copilot/backend/app/main.py:381](../../../s2p-copilot/backend/app/main.py:381), [copilot-sdk/copilot_sdk/scoring/scorer.py:732](../../../copilot-sdk/copilot_sdk/scoring/scorer.py:732), [copilot-sdk/copilot_sdk/backend/investigation_router.py:42](../../../copilot-sdk/copilot_sdk/backend/investigation_router.py:42).

### New-export scope corrections

| Item named in sweep context | Actual location/consumption |
|---|---|
| budget_policy | Shared SDK module; S2P imports AdaptiveBudgetPolicy |
| budget_router | Shared SDK module; S2P imports and mounts its factory |
| investigation_router | Shared SDK module; both S2P and SOC import and mount it |
| conservation | S2P mounts shared router; SOC wraps local learning health and normalizes separately for promotion |
| concepts_router | Exists as a direct SDK module; no explicit S2P/SOC import in the scanned app trees |
| cross_signal_router | Exists as a direct SDK module; no explicit S2P/SOC import in the scanned app trees |
| switching_cost_router | Shared SDK module; no explicit S2P/SOC import in the scanned app trees |
| trust_perturbation_router | **App-local**, at apps/dataops/backend/app/routers/trust_perturbation_router.py, not copilot_sdk/backend/trust_perturbation_router.py |

Not being re-exported by backend/__init__.py does not make a direct-module import invalid. Likewise, a shared module's existence does not establish that every domain must mount it. No consumer import of the nonexistent shared trust-perturbation path was found; that incorrect path is a scope correction, not a demonstrated startup failure.

## SDK→SOC Import Verification

All 80 explicit SDK symbol imports resolve. The important distinction is between SOC's legacy adapter, its domain-native routes, and the canonical SDK routes.

| Integration | Trace | Verdict |
|---|---|---|
| Shared scorer | SOC retains a legacy profile adapter around a shared compound scorer | Deliberate adaptation; not the same public object as S2P's scorer |
| Investigation | SOC mounts create_investigation_router in addition to its native /api/soc/investigate | Canonical SDK route works; native wrapper is a separate contract |
| K store | SOC supplies the connection adapter expected by the shared KUtilityStore | Constructor wiring compatible |
| Conservation promotion state | SOC uses CachedAsyncProvider and normalize_conservation_state; S2P uses ScorerBackedProvider | Different providers are legitimate; internal normalization exists |
| Public compatibility status | /api/conservation/status directly returns SOC learning_health() | Internal promotion normalization does not normalize this HTTP alias, F5 |
| Twin | SOC uses FrozenTwin with a day-zero scorer view | Different baseline policy is intentional; missed-decision alias is wrong, F6 |
| Auth, graph, promotion, RL, situation, evolution | All explicit SDK symbol imports resolve | No missing export found; dynamic/indirect behavior not exhaustively executed |

Evidence: [gen-ai-roi-demo-v4-v50/backend/app/main.py:246](../../../gen-ai-roi-demo-v4-v50/backend/app/main.py:246), [gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:26](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:26), [gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:84](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:84). The SOC endpoint map was read as documentation, but implementation and live responses take precedence.

### Reverse dependency found in SDK framework helpers

SDK audit and intervention helpers still import app.framework or app.db from the hosting application. These are **three reverse imports**, not additional SDK→consumer symbol imports in the 202 count. No direct S2P/SOC consumption of these SDK helper modules was found in the app import inventory; the applications retain local implementations. Therefore this is a latent SDK portability problem, not evidence that their current startup calls these broken SDK fallbacks. See F9.

## Frozen Twin Contract Comparison

These are **not one interchangeable HTTP API**. The SDK supplies core snapshot/scoring/drift abstractions; each application adds its own HTTP wrapper.

| Surface | Contract | Empty/not-initialized behavior | Compatibility judgment |
|---|---|---|---|
| SDK FrozenTwin.score_parallel | ParallelResult with live_result, frozen_result, delta | Depends on frozen snapshot existence | Results retain underlying scorer's action_name; consumers must adapt correctly |
| SDK DriftReport | centroid_drift, weight_drift, conservation_drift, iks_delta, decision_count_since_freeze | No accuracy fields | A state-drift object, not an accuracy series |
| S2P /api/s2p/twin/drift | DriftReport serialized plus evidence metadata | Manager controls availability | Correct drift transport; incorrect consumer assumptions in F8 |
| S2P /api/s2p/learning/frozen-twin | frozen_available, current/frozen accuracy and coverage, visual_diff, current_vs_frozen, missed-decision list | Fallback sets frozen_available=true even without a frozen manager | F1/F4/F7 |
| SOC /api/learning/frozen-twin | Domain comparison plus current_vs_frozen, replay_candidates, missed-decision alias | Live 503: day-zero baseline unavailable | F6: alias becomes an integer when initialized |
| Purchasing /api/purchasing/frozen-twin | Domain-specific available/status/evidence_tier wrapper | Live 200, available=false, status=NOT_INITIALIZED | Honest unavailable state; not an accuracy comparison |
| SDK shared frontend FrozenTwinComparisonPanel | Explicit liveData/frozenData inputs | Depends on caller adaptation | Does not automatically normalize the domain HTTP wrappers |

**Live observations:** S2P returned frozen_available=true, empty visual_diff and missed-decision arrays, and null current/frozen accuracy. This does not demonstrate a measured twin advantage. Purchasing explicitly reported no initialized twin. SOC rejected the request with 503. These were observed current states, not permanent architectural claims.

**Field-level drift:** S2P's decisions_frozen_would_have_missed is a list; SOC derives the identically named field from an integer number of decisions since freeze. Neither an elapsed count nor the mere existence of a twin proves missed decisions.

Evidence: [copilot-sdk/copilot_sdk/twin/service.py:82](../../../copilot-sdk/copilot_sdk/twin/service.py:82), [copilot-sdk/copilot_sdk/twin/models.py:147](../../../copilot-sdk/copilot_sdk/twin/models.py:147), [s2p-copilot/backend/app/routers/s2p_demo_beats.py:153](../../../s2p-copilot/backend/app/routers/s2p_demo_beats.py:153), [gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:108](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:108).

## Investigation Contract Comparison

| Surface | Request | Successful response | Observed result |
|---|---|---|---|
| Trading canonical SDK /api/investigation/investigate | decision_id, category, factor_vector; optional budget/use_K | Shared 14-field InvestigationResponse | 200 with valid 10-factor input |
| SOC canonical SDK /api/investigation/investigate | Same schema; SOC category and 6-factor vector | Same shared 14-field response | 200 |
| SOC native /api/soc/investigate | alert_id | status, mode, alert_id, single_pass, vld, investigation_trace, conservation_emit_gate | 500 for the planted alert; successful shape verified from source only |
| S2P canonical SDK route | Shared request model; S2P factors/category/provider | Shared response model | Mount/signature inspected; no additional S2P investigation POST executed |

Canonical response fields: decision_id, category, budget_used, situation, situation_confidence, surface_action, surface_margin, final_action, final_margin, action_changed, steps, contrast, snapshot, halt_reason.

In both successful canonical probes, actions were integer indices, margins were floats, steps a list, contrast and snapshot dictionaries. Explicit budget=1 bypassed classification, so situation and situation_confidence were null. Step entries carried the same read/evidence/action/margin fields; snapshots supplied action_names and factor_names for interpretation.

The user's example Trading request containing only event_id/category returned **422** for missing decision_id and factor_vector. This is correct validation, not evidence that the endpoint is absent. A second request with the actual schema succeeded.

SOC's native route returns action names and a domain-specific trace under different keys. That difference alone is **not drift in the shared route**: SOC also exposes the canonical SDK endpoint, and its live response matched Trading's field/type contract. Clients must choose one API and use its request/response schema.

Both investigated paths are described in source as read-only/shadow investigation. No analyze, outcome, checkpoint, perturbation, or preseed endpoints were invoked. The native 500's root cause was not established from the response; no specific source line is blamed without a complete failure trace.

Evidence: [copilot-sdk/copilot_sdk/backend/investigation_router.py:16](../../../copilot-sdk/copilot_sdk/backend/investigation_router.py:16), [copilot-sdk/copilot_sdk/backend/investigation_router.py:24](../../../copilot-sdk/copilot_sdk/backend/investigation_router.py:24), [copilot-sdk/copilot_sdk/backend/investigation_router.py:59](../../../copilot-sdk/copilot_sdk/backend/investigation_router.py:59), [gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:454](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:454).

## Budget Policy Integration Analysis

### Actual call path

1. S2P main creates AdaptiveBudgetPolicy(safety_lambda=0.0).
2. The same instance is mounted behind GET /api/self/investigation-budget.
3. S2P subclasses the SDK SituationClassifier and injects that policy plus _s2p_verified_count.
4. The canonical SDK investigation handler calls classify only when the request does not specify budget.
5. The S2P subclass calls allocate and replaces assessment.recommended_budget.
6. VLDInvestigator consumes that selected budget.

Therefore the policy is **not merely telemetry**, but neither is it part of every ordinary /api/s2p/score call. Its production integration is the automatic-budget investigation path. Explicit budget bypasses it. No allocate call was found in the ordinary S2P score handler.

### Two independent semantic faults

- **Count:** _s2p_verified_count reads app.state.scorer.decision_count with default 0. The shared compound scorer exposes get_verified_count(), not that public attribute. Cold-start therefore persists under normal shared-scorer wiring.
- **Confidence:** the subclass supplies the situation-classification confidence. With no classifier model path supplied, the SDK fallback always assigns 0.5, independently of surface action probability. Once the count is repaired, this selects max_reads=4, even for an easy S1 input.

The local real-class diagnostic used a surface distribution headed by 0.99. The fallback classifier returned S1/confidence=0.5. allocate(..., verified_count=196) returned 4; allocate(..., verified_count=0) returned 2. Thus fixing only the count will expose the second fault.

Live S2P status showed 196 verified decisions, while its budget stats returned controller=adaptive, decisions=0, safety_lambda=0. A zero history alone would also be possible before any allocation requests; the source accessor mismatch, not telemetry alone, establishes F2.

safety_lambda is stored and reported by the SDK policy; allocate does not use it in its decision formula. Setting it to zero is accepted, but does not establish an independently active safety optimization objective.

## Response Shape Comparison (live probes)

Probe batch timestamp: **2026-09-19 00:09:36 UTC / September 18, 17:09 PDT** for the GET batch. Investigation probes followed during the same audit. State can change after these observations.

| # | Copilot / method / path | HTTP | Observed contract/evidence |
|---|---|---:|---|
| 1 | SOC GET /api/learning/frozen-twin | 503 | detail: SOC day-zero baseline unavailable; Frozen Twin not initialized |
| 2 | S2P GET /api/s2p/learning/frozen-twin | 200 | frozen_available=true; null accuracy values; empty visual_diff/missed lists |
| 3 | Purchasing GET /api/purchasing/frozen-twin | 200 | available=false; status=NOT_INITIALIZED; evidence_tier |
| 4 | SOC GET /api/fingerprint | 200 | factors[6], win rate, precision, decisions, SOC geometry; no engine |
| 5 | Trading GET /api/fingerprint | 200 | factors[10], win rate, precision, decisions, engine |
| 6 | SOC GET /api/conservation/status | 200 | RED; nested components and conservation; g_abs/g_rel/g_rate; no root verified_count |
| 7 | Trading GET /api/conservation/status | 503 | detail reports graph connection closed unexpectedly |
| 8 | S2P GET /api/conservation/status | 200 | GREEN; verified_count=196; flat shared state plus three gate details |
| 9 | SOC GET /api/trajectory | 503 | detail: SOC trajectory unavailable |
| 10 | Trading GET /api/trajectory | 200 | points[37], current_iks, current_win_rate, decisions_total, days_active, engine |
| 11 | S2P GET /api/self/investigation-budget | 200 | controller=adaptive, decisions=0, safety_lambda=0 |
| 12 | Trading GET /api/self/investigation-budget | 404 | Not Found; no S2P-like budget mount established for Trading |
| 13 | Trading POST /api/investigation/investigate; event_id/category only | 422 | Missing decision_id and factor_vector |
| 14 | Trading POST /api/investigation/investigate; valid 10-factor vector, budget=1 | 200 | Shared 14-field response |
| 15 | SOC POST /api/soc/investigate; PL-SOC-1-NO-PRECEDENT-001 | 500 | Internal Server Error; underlying exception not verified |
| 16 | SOC POST /api/investigation/investigate; valid 6-factor vector, budget=1 | 200 | Shared 14-field response; matches canonical Trading schema |

GET does not guarantee absence of application side effects: source tracing after the S2P twin probe revealed F4. No deliberate lifecycle or decision mutations were issued, and that response contained no comparison rows. No populated twin replay was invoked to reproduce ledger growth.

### Schema verdicts, not just key equality

- Different factor counts and domain-specific extra fields are expected.
- Missing **required** engine metadata is not an innocent extra-field difference.
- Nested SOC conservation fields require an explicit translation to the SDK flat contract.
- Shared canonical investigation matched on field names and observed types; different native wrappers should not be conflated.
- SOC trajectory's success contract could only be checked in source because its live request failed.
- Null/empty twin comparisons must not be interpreted as measured wins.
- Live 500/503 responses are operational limitations, not proof of a particular import defect.

## Test Count Reconciliation

Read-only AST counts include test functions/methods, including async definitions, under test_*.py. They are **not collected pytest cases** and do not imply a passing run. Parameter expansion, collection rules, skip state, and snapshot age differ.

| Scope | Files | Current test definitions | Parametrized functions | Session-state result inspected |
|---|---:|---:|---:|---|
| SDK root | 287 | 3183 | 65 | 3548 passed + 1 unrelated Purchasing evolution failure; isolated rerun subsequently passed |
| Trading | 88 | 1344 | 21 | 1455 passed |
| Purchasing | 55 | 773 | 15 | 827 passed, 1 skipped |
| DataOps | 28 | 387 | 8 | 418 passed |
| S2P | 151 | 1842 | 5 | 1857 passed, 0 failed |
| SOC | 251 | 2450 | 14 | 2475 passed, 16 skipped |

Total: **9,979 current test definitions across 860 files**. No parse errors occurred in this count. Different definition and historical passed-case totals are not evidence of deleted tests.

SDK's later budget entry records nine added tests, but does not constitute a fresh full-suite count; this report does not add historical totals together and call the sum verified.

Session references: [copilot-sdk/docs/session_state.md:1040](../../../copilot-sdk/docs/session_state.md:1040), [copilot-sdk/docs/session_state.md:1046](../../../copilot-sdk/docs/session_state.md:1046), [copilot-sdk/docs/session_state.md:1052](../../../copilot-sdk/docs/session_state.md:1052), [s2p-copilot/backend/docs/session_state.md:344](../../../s2p-copilot/backend/docs/session_state.md:344), [gen-ai-roi-demo-v4-v50/docs/session_state.md:323](../../../gen-ai-roi-demo-v4-v50/docs/session_state.md:323).

### Existing cross-repo tests and their limits

The context claim that “no cross-repo test catches it” is too broad if read as “no cross-repo tests exist.”

- gen-ai-roi-demo-v4-v50/backend/tests/test_cross_repo_contracts.py contains **9 tests**. It covers older GAE/CI-platform/SOC contracts (including scoring-result features and audit/graph-related checks), not these new budget, twin-serialization, public-alias, or frontend contract boundaries.
- copilot-sdk/tests/test_budget_policy.py contains **9 tests** covering the policy in isolation, including cold-start and easy/hard thresholds. It does not exercise S2P's verified-count adapter or the fallback classifier's confidence semantics.
- s2p-copilot/backend/tests/test_s2p_autonomy.py contains **21 tests**. Its score/twin surface checks do not validate that actual raw GAE result names survive the serializer or that the twin panel receives accuracy fields.
- Static import resolution and a passing shape-only endpoint test cannot establish semantic contract parity.

Recommended integration cases: real raw scorer → S2P serialized action; warmed shared scorer → automatic budget; high surface confidence → easy read budget; public SOC alias → SDK response-model validation; populated twin GET repeated without ledger growth; drift/comparison API → real frontend field requirements; initialized SOC twin missed-decision collection type.

No pytest suite or collection pass was executed during this read-only audit, to avoid app startup hooks, graph writes, caches, and fixture side effects.

## Ranked Findings (P1 → P3)

Each finding follows A LOCATE, B READ, C TRACE, D VERDICT, E CLASSIFY. References identify the current inspected checkout, not a historical release.

### F1 — P1: S2P serializes raw twin actions as the empty string

**A — LOCATE.** [s2p-copilot/backend/app/services/s2p_autonomy.py:164](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:164); consumer [s2p-copilot/backend/app/routers/s2p_demo_beats.py:218](../../../s2p-copilot/backend/app/routers/s2p_demo_beats.py:218).

**B — READ.** Read the complete _score_payload and parallel_score functions, FrozenTwin.score_parallel, raw ScoringResult declaration, and the whole S2P frozen_twin route.

**C — TRACE.** The SDK twin returns raw ProfileScorer ScoringResult objects. Their action name is action_name, while _score_payload reads action with fallback "". Both live and frozen results therefore lose the actual name. The demo route compares those empty strings to verified actual_action labels.

**D — VERDICT.** On any populated comparison with a nonempty actual-action label, correct decisions are counted incorrect; frozen misses are inflated and both accuracies can collapse to zero. This is silent evidence corruption, not merely a renamed JSON field. A real ProfileScorer diagnostic produced action_name="a", no action attribute, and S2P's unchanged serializer produced action="": confidence and action_index survived. The live empty comparison did not itself exercise the nonempty accuracy branch.

**E — CLASSIFY.** P1, confirmed producer/consumer mismatch plus real-object reproduction. Repair priority: first; bind serialization to the real result type and test label preservation.

### F2 — P2: S2P budget provider reads the wrong scorer counter

**A — LOCATE.** [s2p-copilot/backend/app/main.py:250](../../../s2p-copilot/backend/app/main.py:250) versus [copilot-sdk/copilot_sdk/scoring/scorer.py:732](../../../copilot-sdk/copilot_sdk/scoring/scorer.py:732).

**B — READ.** Read the S2P scorer creation and budget wiring, _s2p_verified_count, classifier override, SDK get_verified_count, and policy allocate/get_stats functions.

**C — TRACE.** app.state.scorer is the shared CompoundingScorer. It has get_verified_count(), but no public decision_count in the inspected implementation. getattr(...,0) hides this incompatibility. allocate sees zero and returns two reads before recording history.

**D — VERDICT.** Warmed S2P investigations without an explicit budget stay on cold-start allocation. The budget endpoint can continue showing zero allocation history despite verified decisions. Live verified_count=196 is consistent with a warmed scorer; policy history alone is not conclusive evidence.

**E — CLASSIFY.** P2, deterministic normal-wiring semantic failure. Use the scorer's public verified-count contract; do not silently convert an absent interface into a real zero.

### F3 — P2: Budget policy uses situation confidence as action confidence

**A — LOCATE.** [s2p-copilot/backend/app/main.py:74](../../../s2p-copilot/backend/app/main.py:74); fallback producer [copilot-sdk/copilot_sdk/scoring/situation_classifier.py:105](../../../copilot-sdk/copilot_sdk/scoring/situation_classifier.py:105).

**B — READ.** Read complete classify implementations and allocate, including the SDK's trained-model and heuristic fallback branches.

**C — TRACE.** S2P passes assessment.confidence to the easy/hard policy. It constructs SituationClassifier without a model path, so the inherited fallback assigns 0.5 for every situation. This is confidence in a situation classification, not the probability of the proposed action. F2 currently masks its warmed-path effect.

**D — VERDICT.** Fixing the verified-count accessor alone causes all default-classifier automatic allocations to select four reads, including a real diagnostic with max surface probability 0.99 and situation S1. Claimed easy/hard budget differentiation remains absent.

**E — CLASSIFY.** P2, confirmed latent second defect. Define which confidence the policy consumes and test the coupled classifier/policy boundary rather than only allocate in isolation.

### F4 — P2: Reading S2P twin comparison appends governance events

**A — LOCATE.** [s2p-copilot/backend/app/routers/s2p_demo_beats.py:213](../../../s2p-copilot/backend/app/routers/s2p_demo_beats.py:213) → [s2p-copilot/backend/app/services/s2p_autonomy.py:151](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:151) → [s2p-copilot/backend/app/services/compounding_ledger.py:126](../../../s2p-copilot/backend/app/services/compounding_ledger.py:126) and [s2p-copilot/backend/app/services/compounding_ledger.py:78](../../../s2p-copilot/backend/app/services/compounding_ledger.py:78).

**B — READ.** Read the complete route, parallel_score, _record_event, record_governance_event, and _write functions.

**C — TRACE.** GET replays every eligible verified row through manager.parallel_score. The manager always records frozen_twin_comparison when a ledger recorder is available. The ledger writes an evolution event with a fresh UUID.

**D — VERDICT.** One GET over N valid rows can add N persisted governance events; refreshing repeats the writes rather than reading a stable comparison. Browser refreshes and contract probes become audit writes and increase work with history size. This was established by source data flow, not by deliberately growing the live ledger.

**E — CLASSIFY.** P2, unintended read-side mutation and operational amplification. Separate pure comparison from explicit event-recording operations.

### F5 — P2: SOC's SDK-compatible aliases lack SDK-required fields/normalization

**A — LOCATE.** [gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:36](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:36), [gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:68](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:68), [gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:84](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:84); SDK models [copilot-sdk/copilot_sdk/backend/models.py:107](../../../copilot-sdk/copilot_sdk/backend/models.py:107), [copilot-sdk/copilot_sdk/backend/models.py:122](../../../copilot-sdk/copilot_sdk/backend/models.py:122), [copilot-sdk/copilot_sdk/backend/models.py:155](../../../copilot-sdk/copilot_sdk/backend/models.py:155).

**B — READ.** Read the full compatibility router, SDK fingerprint/trajectory route functions and response models, SOC learning_health, and the internal SOC conservation-provider normalization.

**C — TRACE.** SDK routes add engine metadata before response-model serialization. SOC returns raw scorer fingerprint/trajectory data without that step. Its conservation alias returns native learning health with components.verified_decisions and nested conservation rather than root verified_count/correct_count/alpha/q/V/domain/engine. Its internal promotion-state normalizer is not used by this alias.

**D — VERDICT.** Clients validating or consuming the shared SDK schema cannot interchange these SOC aliases with native SDK endpoints. Live fingerprint confirmed missing engine; live conservation confirmed the structural mismatch. SOC trajectory returned 503, so its successful-path omission is source-confirmed only. Different factor counts themselves are legitimate.

**E — CLASSIFY.** P2, public compatibility contract drift. Normalize deliberately and validate all aliases against the promised SDK models without removing domain-specific extensions.

### F6 — P2: SOC's missed-decision alias is an elapsed count, not missed decisions

**A — LOCATE.** [gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:115](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:115); producer [gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:131](../../../gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:131).

**B — READ.** Read SOC's complete frozen_twin route and comparison function, SDK DriftReport, and S2P's _frozen_twin_contract.

**C — TRACE.** SOC maps decisions_since_freeze (an integer derived from DriftReport.decision_count_since_freeze) into decisions_frozen_would_have_missed. S2P uses the latter key for a list of actual comparison records.

**D — VERDICT.** Once initialized, SOC can return 12 under a field that another domain returns as a list; it also misrepresents “12 decisions elapsed” as evidence of frozen misses. This is not a valid calculation of counterfactual errors. Live SOC unavailability masked the initialized path during the probe.

**E — CLASSIFY.** P2, type and meaning drift. Keep elapsed count separate and compute missed decisions from verified replay evidence.

### F7 — P2: S2P advertises a frozen twin when its manager/snapshot is absent

**A — LOCATE.** [s2p-copilot/backend/app/routers/s2p_demo_beats.py:183](../../../s2p-copilot/backend/app/routers/s2p_demo_beats.py:183) and [s2p-copilot/backend/app/routers/s2p_demo_beats.py:187](../../../s2p-copilot/backend/app/routers/s2p_demo_beats.py:187).

**B — READ.** Read both complete initialized and fallback branches and manager.twin_status.

**C — TRACE.** The fallback is entered when the manager is not a S2PAutonomyManager or its twin is not frozen, yet it emits frozen_available=true. It reports config-baseline drift and null accuracy, and labels the reason “Graph unavailable” even though that is not the branch condition.

**D — VERDICT.** Availability-based clients and demo assertions cannot distinguish a persisted frozen twin from a configuration-baseline fallback. The live true/null response is not by itself proof that this branch ran; the contradictory fallback is established from source.

**E — CLASSIFY.** P2, false availability/provenance signal. Report real frozen availability separately from availability of a canonical baseline.

### F8 — P2: S2P twin UI expects accuracy from the SDK drift-only response

**A — LOCATE.** [copilot-sdk/apps/s2p/frontend/src/components/FrozenTwinComparisonPanel.tsx:21](../../../copilot-sdk/apps/s2p/frontend/src/components/FrozenTwinComparisonPanel.tsx:21) and [copilot-sdk/apps/s2p/frontend/src/components/FrozenTwinComparisonPanel.tsx:27](../../../copilot-sdk/apps/s2p/frontend/src/components/FrozenTwinComparisonPanel.tsx:27); endpoint client [copilot-sdk/apps/s2p/frontend/src/api.ts:173](../../../copilot-sdk/apps/s2p/frontend/src/api.ts:173); producer [copilot-sdk/copilot_sdk/twin/models.py:147](../../../copilot-sdk/copilot_sdk/twin/models.py:147).

**B — READ.** Read the complete component, API methods, TwinDriftReport TypeScript type, S2P twin drift route/manager method, and SDK DriftReport dataclass.

**C — TRACE.** The component fetches /api/s2p/twin/drift and searches for frozen_accuracy/baseline_accuracy/frozen_score plus live_accuracy/current_accuracy/live_score. The server serializes only centroid_drift, weight_drift, conservation_drift, iks_delta, and decision_count_since_freeze (plus evidence metadata). The separate learning/frozen-twin comparison route is not fetched by this component.

**D — VERDICT.** Even with a healthy persisted twin and measured comparison outcomes, this request path cannot populate either accuracy curve. The UI stays at “Pending outcomes”/awaiting accuracy. Optional TypeScript properties and an open index signature hide the producer/consumer mismatch from typechecking.

**E — CLASSIFY.** P2, deterministic rendering-contract gap. Consume an actual accuracy-comparison contract or render state drift under its real meaning; do not relabel drift as accuracy.

### F9 — P2: SDK framework fallbacks retain reverse app dependencies and crash standalone

**A — LOCATE.** [copilot-sdk/copilot_sdk/framework/audit.py:199](../../../copilot-sdk/copilot_sdk/framework/audit.py:199), [copilot-sdk/copilot_sdk/framework/audit.py:204](../../../copilot-sdk/copilot_sdk/framework/audit.py:204), [copilot-sdk/copilot_sdk/framework/audit.py:296](../../../copilot-sdk/copilot_sdk/framework/audit.py:296), [copilot-sdk/copilot_sdk/framework/intervention_controls.py:142](../../../copilot-sdk/copilot_sdk/framework/intervention_controls.py:142).

**B — READ.** Read complete reconstruct_from_memory, rebuild_from_age, and InterventionControls.rollback functions.

**C — TRACE.** reconstruct_from_memory imports app.framework.feedback_store; on ImportError it assigns None, then unconditionally calls FEEDBACK_GIVEN.items(). rebuild_from_age likewise assigns graph_client=None after a missing app.db import and then awaits graph_client.run_query. Non-preview rollback imports app.framework.checkpoint unconditionally.

**D — VERDICT.** These SDK abstractions are not portable to a host without SOC-shaped app modules: advertised standalone fallbacks raise AttributeError, and rollback raises ModuleNotFoundError. Current SOC/S2P app trees use local implementations instead; no live production failure is attributed to these dormant SDK paths, and no new introduction date is claimed.

**E — CLASSIFY.** P2, confirmed latent shared-library portability defect, lower urgency than active F1–F8. Inject required services or provide a real unavailable result; do not silently install None and dereference it.

## Recommended Verification / Fix Priority

1. Preserve true action identity at the SDK→S2P twin boundary (F1); add real-scorer end-to-end accuracy assertions.
2. Fix both budget inputs together (F2/F3); prove a warmed easy/hard stream yields differentiated automatic budgets.
3. Make public SOC alias schemas explicit and validated (F5), while retaining domain-native endpoints.
4. Align twin availability, missed-decision semantics, UI contract, and read-only behavior (F4/F6/F7/F8).
5. Remove reverse app dependencies or define explicit unsupported-host behavior (F9).
6. Re-probe native SOC investigation and SOC/Trading failing reads after service health is restored; the audit does not diagnose their 500/503 causes from status codes alone.
7. Add cross-repo integration coverage for these boundaries, then reconcile actual pytest collection/run totals rather than source-function counts.

## Appendix A — Complete Imported SDK Module Inventory

Symbols below are the actual consumer imports, deduplicated per module and consumer. “—” means no import from that consumer. All resolve statically; this table does not imply every symbol was runtime-exercised.

| SDK module | S2P imported symbols | SOC imported symbols |
|---|---|---|
| copilot_sdk.ae | — | FitnessEvaluator, PromotionGate, Variant, VariantGenerator |
| copilot_sdk.auth | AuthMiddleware, create_auth_router | AuthMiddleware |
| copilot_sdk.auth.config | — | AuthConfig, load_auth_config |
| copilot_sdk.auth.dependencies | — | ADMIN_PREFIXES, EXEMPT_PREFIXES, MUTATION_PATHS, get_auth_config, require_auth |
| copilot_sdk.auth.jwt_utils | — | create_jwt, derive_role, verify_jwt |
| copilot_sdk.backend | create_conservation_router, create_evolution_router, create_measurement_state_router | — |
| copilot_sdk.backend.auth_router | — | create_auth_router |
| copilot_sdk.backend.budget_router | create_budget_router | — |
| copilot_sdk.backend.conservation_utils | compute_conservation_metrics, compute_conservation_status_payload | — |
| copilot_sdk.backend.counterfactual_router | create_counterfactual_router | — |
| copilot_sdk.backend.diagnostics_models | build_diagnostics | build_diagnostics |
| copilot_sdk.backend.evolution_router | — | create_evolution_router |
| copilot_sdk.backend.investigation_router | create_investigation_router | create_investigation_router |
| copilot_sdk.backend.self_computation_router | mount_self_computation_router | mount_self_computation_router |
| copilot_sdk.backend.transfer_router | create_transfer_router | — |
| copilot_sdk.config | GraphConfig, GraphConfigError, require_shared_graph | GraphConfig, GraphConfigError, require_shared_graph |
| copilot_sdk.domains.base | — | DomainAction, DomainFactor, DomainSituationType |
| copilot_sdk.enterprise.process_ingest | ProcessExportIngester | — |
| copilot_sdk.evolution | AutonomousPromotionGate, ConservationStateProvider, ContextAwareSelector, PromotionDecision, PromptEvolverConfig, PromptVariantEvolver, ScorerBackedProvider, SelectionContext, VariantSpec | — |
| copilot_sdk.evolution.conservation_contract | — | CachedAsyncProvider, ConservationState, normalize_conservation_state |
| copilot_sdk.evolution.graph_store | GraphVariantStore | — |
| copilot_sdk.evolution.prompt_evolver | — | PromptEvolverConfig, PromptVariantEvolver |
| copilot_sdk.evolution.variant_store | — | CategoryVariantStats, InMemoryVariantStore, VariantSpec, VariantStats, VariantStore |
| copilot_sdk.graph.contract | EdgeType, GraphContract, NodeType | — |
| copilot_sdk.graph.dual_write_store | — | DualWriteStore |
| copilot_sdk.graph.enrichment | EnrichmentSourceSet, EntityEnrichmentReceipt, EntityEnrichmentRecord, ProvenancedValue | — |
| copilot_sdk.graph.factory | create_graph_store | create_graph_store |
| copilot_sdk.graph.memory_store | InMemoryGraphStore | — |
| copilot_sdk.graph.protocol | GraphStore, GraphTraversalStore, ProtocolV2GraphStore | — |
| copilot_sdk.outcome.models | VerifiedOutcome | — |
| copilot_sdk.promotion | PromotionEngine, PromotionRecord, PromotionResult, PromotionStore, S2PPromotionPolicy | PromotionEngine, PromotionRecord, PromotionStage, PromotionStore, SOCPromotionPolicy |
| copilot_sdk.rl | RewardComputer | CreditAssigner, DomainRewardFunction, ExplorationPolicy, RewardComputer, RewardResult |
| copilot_sdk.scoring | CompoundingScorer | — |
| copilot_sdk.scoring.budget_policy | AdaptiveBudgetPolicy | — |
| copilot_sdk.scoring.dk_persistence | DKWelfordTracker, persist_dk_after_reestimate | DKWelfordTracker, persist_dk_after_reestimate |
| copilot_sdk.scoring.investigation | EvidenceProvider, KUtilityStore | KUtilityStore |
| copilot_sdk.scoring.mutation_lock | get_mutation_lock, serialize_mutation | — |
| copilot_sdk.scoring.scorer | — | CompoundingScorer |
| copilot_sdk.scoring.situation_classifier | SituationAssessment, SituationClassifier | SituationClassifier |
| copilot_sdk.scoring.startup_restore | restore_l5_runtime_state | — |
| copilot_sdk.situation | ContextChain, NLRenderer, SituationAnalyzer, SituationContext, TraversalEdge, TraversalNode, TypedIntent | SituationContext, TraversalEdge, TraversalNode, TypedIntent |
| copilot_sdk.situation.templates | SafeTemplateRenderer | — |
| copilot_sdk.state | TabStateCache, create_invalidation_header_middleware, create_tab_state_router, register_tab_state_cache | — |
| copilot_sdk.state.cached_static | cached_static | — |
| copilot_sdk.state.invalidation | apply_cache_invalidation_event, get_tab_state_cache | — |
| copilot_sdk.substantiation.cohort_day_zero | BaseCohortDayZeroState, STATES, compute_state, evaluate_v7_gate | BaseCohortDayZeroState, STATES, compute_state, evaluate_v7_gate |
| copilot_sdk.twin | FrozenTwin, FrozenTwinStore | FrozenTwin, FrozenTwinStore |

## Appendix B — All 202 Cross-Repo Import Occurrences

Each row records one symbol import occurrence, including repeated imports in different consumers. Targets follow SDK re-exports to their definitions. This is an auditable static-binding ledger, not a substitute for runtime protocol tests.

| # | Consumer location | Imported SDK symbol | Resolved definition |
|---|---|---|---|
| 1 | [gen-ai-roi-demo-v4-v50/backend/app/auth/config.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/auth/config.py:2) | copilot_sdk.auth.config.AuthConfig | [copilot-sdk/copilot_sdk/auth/config.py:8](../../../copilot-sdk/copilot_sdk/auth/config.py:8) |
| 2 | [gen-ai-roi-demo-v4-v50/backend/app/auth/config.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/auth/config.py:2) | copilot_sdk.auth.config.load_auth_config | [copilot-sdk/copilot_sdk/auth/config.py:33](../../../copilot-sdk/copilot_sdk/auth/config.py:33) |
| 3 | [gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:2) | copilot_sdk.auth.dependencies.ADMIN_PREFIXES | [copilot-sdk/copilot_sdk/auth/dependencies.py:11](../../../copilot-sdk/copilot_sdk/auth/dependencies.py:11) |
| 4 | [gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:2) | copilot_sdk.auth.dependencies.EXEMPT_PREFIXES | [copilot-sdk/copilot_sdk/auth/dependencies.py:10](../../../copilot-sdk/copilot_sdk/auth/dependencies.py:10) |
| 5 | [gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:2) | copilot_sdk.auth.dependencies.get_auth_config | [copilot-sdk/copilot_sdk/auth/dependencies.py:14](../../../copilot-sdk/copilot_sdk/auth/dependencies.py:14) |
| 6 | [gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:2) | copilot_sdk.auth.dependencies.MUTATION_PATHS | [copilot-sdk/copilot_sdk/auth/dependencies.py:12](../../../copilot-sdk/copilot_sdk/auth/dependencies.py:12) |
| 7 | [gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:2) | copilot_sdk.auth.dependencies.require_auth | [copilot-sdk/copilot_sdk/auth/dependencies.py:21](../../../copilot-sdk/copilot_sdk/auth/dependencies.py:21) |
| 8 | [gen-ai-roi-demo-v4-v50/backend/app/auth/jwt_utils.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/auth/jwt_utils.py:2) | copilot_sdk.auth.jwt_utils.create_jwt | [copilot-sdk/copilot_sdk/auth/jwt_utils.py:7](../../../copilot-sdk/copilot_sdk/auth/jwt_utils.py:7) |
| 9 | [gen-ai-roi-demo-v4-v50/backend/app/auth/jwt_utils.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/auth/jwt_utils.py:2) | copilot_sdk.auth.jwt_utils.derive_role | [copilot-sdk/copilot_sdk/auth/jwt_utils.py:18](../../../copilot-sdk/copilot_sdk/auth/jwt_utils.py:18) |
| 10 | [gen-ai-roi-demo-v4-v50/backend/app/auth/jwt_utils.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/auth/jwt_utils.py:2) | copilot_sdk.auth.jwt_utils.verify_jwt | [copilot-sdk/copilot_sdk/auth/jwt_utils.py:11](../../../copilot-sdk/copilot_sdk/auth/jwt_utils.py:11) |
| 11 | [gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:9](../../../gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:9) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 12 | [gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:9](../../../gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:9) | copilot_sdk.config.GraphConfigError | [copilot-sdk/copilot_sdk/config/graph_config.py:22](../../../copilot-sdk/copilot_sdk/config/graph_config.py:22) |
| 13 | [gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:9](../../../gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:9) | copilot_sdk.config.require_shared_graph | [copilot-sdk/copilot_sdk/config/graph_config.py:26](../../../copilot-sdk/copilot_sdk/config/graph_config.py:26) |
| 14 | [gen-ai-roi-demo-v4-v50/backend/app/domains/base.py:23](../../../gen-ai-roi-demo-v4-v50/backend/app/domains/base.py:23) | copilot_sdk.domains.base.DomainAction | [copilot-sdk/copilot_sdk/domains/base.py:22](../../../copilot-sdk/copilot_sdk/domains/base.py:22) |
| 15 | [gen-ai-roi-demo-v4-v50/backend/app/domains/base.py:23](../../../gen-ai-roi-demo-v4-v50/backend/app/domains/base.py:23) | copilot_sdk.domains.base.DomainFactor | [copilot-sdk/copilot_sdk/domains/base.py:36](../../../copilot-sdk/copilot_sdk/domains/base.py:36) |
| 16 | [gen-ai-roi-demo-v4-v50/backend/app/domains/base.py:23](../../../gen-ai-roi-demo-v4-v50/backend/app/domains/base.py:23) | copilot_sdk.domains.base.DomainSituationType | [copilot-sdk/copilot_sdk/domains/base.py:48](../../../copilot-sdk/copilot_sdk/domains/base.py:48) |
| 17 | [gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:30](../../../gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:30) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 18 | [gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:12](../../../gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:12) | copilot_sdk.scoring.scorer.CompoundingScorer | [copilot-sdk/copilot_sdk/scoring/scorer.py:120](../../../copilot-sdk/copilot_sdk/scoring/scorer.py:120) |
| 19 | [gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:35](../../../gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:35) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 20 | [gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:35](../../../gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:35) | copilot_sdk.config.require_shared_graph | [copilot-sdk/copilot_sdk/config/graph_config.py:26](../../../copilot-sdk/copilot_sdk/config/graph_config.py:26) |
| 21 | [gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:295](../../../gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:295) | copilot_sdk.graph.factory.create_graph_store | [copilot-sdk/copilot_sdk/graph/factory.py:129](../../../copilot-sdk/copilot_sdk/graph/factory.py:129) |
| 22 | [gen-ai-roi-demo-v4-v50/backend/app/main.py:14](../../../gen-ai-roi-demo-v4-v50/backend/app/main.py:14) | copilot_sdk.auth.AuthMiddleware | [copilot-sdk/copilot_sdk/auth/middleware.py:8](../../../copilot-sdk/copilot_sdk/auth/middleware.py:8) |
| 23 | [gen-ai-roi-demo-v4-v50/backend/app/main.py:15](../../../gen-ai-roi-demo-v4-v50/backend/app/main.py:15) | copilot_sdk.backend.auth_router.create_auth_router | [copilot-sdk/copilot_sdk/backend/auth_router.py:11](../../../copilot-sdk/copilot_sdk/backend/auth_router.py:11) |
| 24 | [gen-ai-roi-demo-v4-v50/backend/app/main.py:111](../../../gen-ai-roi-demo-v4-v50/backend/app/main.py:111) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 25 | [gen-ai-roi-demo-v4-v50/backend/app/main.py:151](../../../gen-ai-roi-demo-v4-v50/backend/app/main.py:151) | copilot_sdk.backend.self_computation_router.mount_self_computation_router | [copilot-sdk/copilot_sdk/backend/self_computation_router.py:596](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py:596) |
| 26 | [gen-ai-roi-demo-v4-v50/backend/app/main.py:152](../../../gen-ai-roi-demo-v4-v50/backend/app/main.py:152) | copilot_sdk.backend.evolution_router.create_evolution_router | [copilot-sdk/copilot_sdk/backend/evolution_router.py:38](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py:38) |
| 27 | [gen-ai-roi-demo-v4-v50/backend/app/main.py:153](../../../gen-ai-roi-demo-v4-v50/backend/app/main.py:153) | copilot_sdk.backend.investigation_router.create_investigation_router | [copilot-sdk/copilot_sdk/backend/investigation_router.py:41](../../../copilot-sdk/copilot_sdk/backend/investigation_router.py:41) |
| 28 | [gen-ai-roi-demo-v4-v50/backend/app/main.py:154](../../../gen-ai-roi-demo-v4-v50/backend/app/main.py:154) | copilot_sdk.scoring.investigation.KUtilityStore | [copilot-sdk/copilot_sdk/scoring/investigation.py:404](../../../copilot-sdk/copilot_sdk/scoring/investigation.py:404) |
| 29 | [gen-ai-roi-demo-v4-v50/backend/app/main.py:155](../../../gen-ai-roi-demo-v4-v50/backend/app/main.py:155) | copilot_sdk.scoring.situation_classifier.SituationClassifier | [copilot-sdk/copilot_sdk/scoring/situation_classifier.py:91](../../../copilot-sdk/copilot_sdk/scoring/situation_classifier.py:91) |
| 30 | [gen-ai-roi-demo-v4-v50/backend/app/routers/auth.py:2](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/auth.py:2) | copilot_sdk.backend.auth_router.create_auth_router | [copilot-sdk/copilot_sdk/backend/auth_router.py:11](../../../copilot-sdk/copilot_sdk/backend/auth_router.py:11) |
| 31 | [gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:20](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:20) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 32 | [gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:35](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:35) | copilot_sdk.backend.diagnostics_models.build_diagnostics | [copilot-sdk/copilot_sdk/backend/diagnostics_models.py:297](../../../copilot-sdk/copilot_sdk/backend/diagnostics_models.py:297) |
| 33 | [gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:35](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:35) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 34 | [gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:13](../../../gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:13) | copilot_sdk.promotion.PromotionEngine | [copilot-sdk/copilot_sdk/promotion/core.py:212](../../../copilot-sdk/copilot_sdk/promotion/core.py:212) |
| 35 | [gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:13](../../../gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:13) | copilot_sdk.promotion.PromotionRecord | [copilot-sdk/copilot_sdk/promotion/core.py:52](../../../copilot-sdk/copilot_sdk/promotion/core.py:52) |
| 36 | [gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:13](../../../gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:13) | copilot_sdk.promotion.PromotionStage | [copilot-sdk/copilot_sdk/promotion/core.py:15](../../../copilot-sdk/copilot_sdk/promotion/core.py:15) |
| 37 | [gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:13](../../../gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:13) | copilot_sdk.promotion.PromotionStore | [copilot-sdk/copilot_sdk/promotion/core.py:110](../../../copilot-sdk/copilot_sdk/promotion/core.py:110) |
| 38 | [gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:13](../../../gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py:13) | copilot_sdk.promotion.SOCPromotionPolicy | [copilot-sdk/copilot_sdk/promotion/policies.py:62](../../../copilot-sdk/copilot_sdk/promotion/policies.py:62) |
| 39 | [gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:9](../../../gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:9) | copilot_sdk.substantiation.cohort_day_zero.BaseCohortDayZeroState | [copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:68](../../../copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:68) |
| 40 | [gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:9](../../../gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:9) | copilot_sdk.substantiation.cohort_day_zero.compute_state | [copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:19](../../../copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:19) |
| 41 | [gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:9](../../../gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:9) | copilot_sdk.substantiation.cohort_day_zero.evaluate_v7_gate as _sdk_evaluate_v7_gate | [copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:32](../../../copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:32) |
| 42 | [gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:9](../../../gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:9) | copilot_sdk.substantiation.cohort_day_zero.STATES | [copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:16](../../../copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:16) |
| 43 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:15](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:15) | copilot_sdk.ae.FitnessEvaluator | [copilot-sdk/copilot_sdk/ae/fitness.py:12](../../../copilot-sdk/copilot_sdk/ae/fitness.py:12) |
| 44 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:15](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:15) | copilot_sdk.ae.PromotionGate | [copilot-sdk/copilot_sdk/ae/gate.py:12](../../../copilot-sdk/copilot_sdk/ae/gate.py:12) |
| 45 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:15](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:15) | copilot_sdk.ae.Variant | [copilot-sdk/copilot_sdk/ae/types.py:10](../../../copilot-sdk/copilot_sdk/ae/types.py:10) |
| 46 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:15](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:15) | copilot_sdk.ae.VariantGenerator | [copilot-sdk/copilot_sdk/ae/variant.py:11](../../../copilot-sdk/copilot_sdk/ae/variant.py:11) |
| 47 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:16](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:16) | copilot_sdk.evolution.conservation_contract.CachedAsyncProvider | [copilot-sdk/copilot_sdk/evolution/conservation_contract.py:120](../../../copilot-sdk/copilot_sdk/evolution/conservation_contract.py:120) |
| 48 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:16](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:16) | copilot_sdk.evolution.conservation_contract.ConservationState | [copilot-sdk/copilot_sdk/evolution/conservation_contract.py:21](../../../copilot-sdk/copilot_sdk/evolution/conservation_contract.py:21) |
| 49 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:16](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:16) | copilot_sdk.evolution.conservation_contract.normalize_conservation_state | [copilot-sdk/copilot_sdk/evolution/conservation_contract.py:52](../../../copilot-sdk/copilot_sdk/evolution/conservation_contract.py:52) |
| 50 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:21](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:21) | copilot_sdk.evolution.prompt_evolver.PromptEvolverConfig | [copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:28](../../../copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:28) |
| 51 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:21](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:21) | copilot_sdk.evolution.prompt_evolver.PromptVariantEvolver | [copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:58](../../../copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:58) |
| 52 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:22](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:22) | copilot_sdk.evolution.variant_store.CategoryVariantStats | [copilot-sdk/copilot_sdk/evolution/variant_store.py:51](../../../copilot-sdk/copilot_sdk/evolution/variant_store.py:51) |
| 53 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:22](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:22) | copilot_sdk.evolution.variant_store.InMemoryVariantStore | [copilot-sdk/copilot_sdk/evolution/variant_store.py:81](../../../copilot-sdk/copilot_sdk/evolution/variant_store.py:81) |
| 54 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:22](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:22) | copilot_sdk.evolution.variant_store.VariantSpec | [copilot-sdk/copilot_sdk/evolution/variant_store.py:19](../../../copilot-sdk/copilot_sdk/evolution/variant_store.py:19) |
| 55 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:22](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:22) | copilot_sdk.evolution.variant_store.VariantStats | [copilot-sdk/copilot_sdk/evolution/variant_store.py:40](../../../copilot-sdk/copilot_sdk/evolution/variant_store.py:40) |
| 56 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:22](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:22) | copilot_sdk.evolution.variant_store.VariantStore | [copilot-sdk/copilot_sdk/evolution/variant_store.py:63](../../../copilot-sdk/copilot_sdk/evolution/variant_store.py:63) |
| 57 | [gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:434](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:434) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 58 | [gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:28](../../../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:28) | copilot_sdk.scoring.dk_persistence.DKWelfordTracker | [copilot-sdk/copilot_sdk/scoring/dk_persistence.py:120](../../../copilot-sdk/copilot_sdk/scoring/dk_persistence.py:120) |
| 59 | [gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:28](../../../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:28) | copilot_sdk.scoring.dk_persistence.persist_dk_after_reestimate | [copilot-sdk/copilot_sdk/scoring/dk_persistence.py:231](../../../copilot-sdk/copilot_sdk/scoring/dk_persistence.py:231) |
| 60 | [gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:231](../../../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:231) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 61 | [gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:231](../../../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:231) | copilot_sdk.config.GraphConfigError | [copilot-sdk/copilot_sdk/config/graph_config.py:22](../../../copilot-sdk/copilot_sdk/config/graph_config.py:22) |
| 62 | [gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:271](../../../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:271) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 63 | [gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:271](../../../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:271) | copilot_sdk.config.GraphConfigError | [copilot-sdk/copilot_sdk/config/graph_config.py:22](../../../copilot-sdk/copilot_sdk/config/graph_config.py:22) |
| 64 | [gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:272](../../../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:272) | copilot_sdk.graph.factory.create_graph_store | [copilot-sdk/copilot_sdk/graph/factory.py:129](../../../copilot-sdk/copilot_sdk/graph/factory.py:129) |
| 65 | [gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:273](../../../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:273) | copilot_sdk.graph.dual_write_store.DualWriteStore | [copilot-sdk/copilot_sdk/graph/dual_write_store.py:36](../../../copilot-sdk/copilot_sdk/graph/dual_write_store.py:36) |
| 66 | [gen-ai-roi-demo-v4-v50/backend/app/services/learning.py:5](../../../gen-ai-roi-demo-v4-v50/backend/app/services/learning.py:5) | copilot_sdk.rl.RewardComputer | [copilot-sdk/copilot_sdk/rl/reward.py:27](../../../copilot-sdk/copilot_sdk/rl/reward.py:27) |
| 67 | [gen-ai-roi-demo-v4-v50/backend/app/services/learning.py:5](../../../gen-ai-roi-demo-v4-v50/backend/app/services/learning.py:5) | copilot_sdk.rl.RewardResult | [copilot-sdk/copilot_sdk/rl/types.py:10](../../../copilot-sdk/copilot_sdk/rl/types.py:10) |
| 68 | [gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:10](../../../gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:10) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 69 | [gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:61](../../../gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:61) | copilot_sdk.graph.factory.create_graph_store | [copilot-sdk/copilot_sdk/graph/factory.py:129](../../../copilot-sdk/copilot_sdk/graph/factory.py:129) |
| 70 | [gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:19](../../../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:19) | copilot_sdk.rl.CreditAssigner as SDKCreditAssigner | [copilot-sdk/copilot_sdk/rl/credit.py:10](../../../copilot-sdk/copilot_sdk/rl/credit.py:10) |
| 71 | [gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:19](../../../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:19) | copilot_sdk.rl.DomainRewardFunction | [copilot-sdk/copilot_sdk/rl/reward.py:12](../../../copilot-sdk/copilot_sdk/rl/reward.py:12) |
| 72 | [gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:19](../../../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:19) | copilot_sdk.rl.ExplorationPolicy as SDKExplorationPolicy | [copilot-sdk/copilot_sdk/rl/exploration.py:121](../../../copilot-sdk/copilot_sdk/rl/exploration.py:121) |
| 73 | [gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:19](../../../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:19) | copilot_sdk.rl.RewardComputer as SDKRewardComputer | [copilot-sdk/copilot_sdk/rl/reward.py:27](../../../copilot-sdk/copilot_sdk/rl/reward.py:27) |
| 74 | [gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:625](../../../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:625) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 75 | [gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:19](../../../gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:19) | copilot_sdk.twin.FrozenTwin | [copilot-sdk/copilot_sdk/twin/service.py:17](../../../copilot-sdk/copilot_sdk/twin/service.py:17) |
| 76 | [gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:19](../../../gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:19) | copilot_sdk.twin.FrozenTwinStore | [copilot-sdk/copilot_sdk/twin/store.py:14](../../../copilot-sdk/copilot_sdk/twin/store.py:14) |
| 77 | [gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:11](../../../gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:11) | copilot_sdk.situation.SituationContext | [copilot-sdk/copilot_sdk/situation/models.py:213](../../../copilot-sdk/copilot_sdk/situation/models.py:213) |
| 78 | [gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:11](../../../gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:11) | copilot_sdk.situation.TraversalEdge | [copilot-sdk/copilot_sdk/situation/models.py:193](../../../copilot-sdk/copilot_sdk/situation/models.py:193) |
| 79 | [gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:11](../../../gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:11) | copilot_sdk.situation.TraversalNode | [copilot-sdk/copilot_sdk/situation/models.py:171](../../../copilot-sdk/copilot_sdk/situation/models.py:171) |
| 80 | [gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:11](../../../gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:11) | copilot_sdk.situation.TypedIntent | [copilot-sdk/copilot_sdk/situation/models.py:100](../../../copilot-sdk/copilot_sdk/situation/models.py:100) |
| 81 | [s2p-copilot/backend/app/domains/s2p/evolution/service.py:9](../../../s2p-copilot/backend/app/domains/s2p/evolution/service.py:9) | copilot_sdk.evolution.AutonomousPromotionGate | [copilot-sdk/copilot_sdk/evolution/autonomous_promotion.py:23](../../../copilot-sdk/copilot_sdk/evolution/autonomous_promotion.py:23) |
| 82 | [s2p-copilot/backend/app/domains/s2p/evolution/service.py:9](../../../s2p-copilot/backend/app/domains/s2p/evolution/service.py:9) | copilot_sdk.evolution.ContextAwareSelector | [copilot-sdk/copilot_sdk/evolution/context_selector.py:19](../../../copilot-sdk/copilot_sdk/evolution/context_selector.py:19) |
| 83 | [s2p-copilot/backend/app/domains/s2p/evolution/service.py:9](../../../s2p-copilot/backend/app/domains/s2p/evolution/service.py:9) | copilot_sdk.evolution.PromotionDecision | [copilot-sdk/copilot_sdk/evolution/autonomous_promotion.py:10](../../../copilot-sdk/copilot_sdk/evolution/autonomous_promotion.py:10) |
| 84 | [s2p-copilot/backend/app/domains/s2p/evolution/service.py:9](../../../s2p-copilot/backend/app/domains/s2p/evolution/service.py:9) | copilot_sdk.evolution.SelectionContext | [copilot-sdk/copilot_sdk/evolution/context_selector.py:11](../../../copilot-sdk/copilot_sdk/evolution/context_selector.py:11) |
| 85 | [s2p-copilot/backend/app/domains/s2p/evolver_config.py:5](../../../s2p-copilot/backend/app/domains/s2p/evolver_config.py:5) | copilot_sdk.evolution.PromptEvolverConfig | [copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:28](../../../copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:28) |
| 86 | [s2p-copilot/backend/app/domains/s2p/evolver_config.py:5](../../../s2p-copilot/backend/app/domains/s2p/evolver_config.py:5) | copilot_sdk.evolution.VariantSpec | [copilot-sdk/copilot_sdk/evolution/variant_store.py:19](../../../copilot-sdk/copilot_sdk/evolution/variant_store.py:19) |
| 87 | [s2p-copilot/backend/app/domains/s2p/reward.py:7](../../../s2p-copilot/backend/app/domains/s2p/reward.py:7) | copilot_sdk.rl.RewardComputer | [copilot-sdk/copilot_sdk/rl/reward.py:27](../../../copilot-sdk/copilot_sdk/rl/reward.py:27) |
| 88 | [s2p-copilot/backend/app/evidence_provider.py:10](../../../s2p-copilot/backend/app/evidence_provider.py:10) | copilot_sdk.scoring.investigation.EvidenceProvider | [copilot-sdk/copilot_sdk/scoring/investigation.py:75](../../../copilot-sdk/copilot_sdk/scoring/investigation.py:75) |
| 89 | [s2p-copilot/backend/app/framework/audit.py:19](../../../s2p-copilot/backend/app/framework/audit.py:19) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 90 | [s2p-copilot/backend/app/graph_contract.py:7](../../../s2p-copilot/backend/app/graph_contract.py:7) | copilot_sdk.graph.contract.EdgeType | [copilot-sdk/copilot_sdk/graph/contract.py:16](../../../copilot-sdk/copilot_sdk/graph/contract.py:16) |
| 91 | [s2p-copilot/backend/app/graph_contract.py:7](../../../s2p-copilot/backend/app/graph_contract.py:7) | copilot_sdk.graph.contract.GraphContract | [copilot-sdk/copilot_sdk/graph/contract.py:25](../../../copilot-sdk/copilot_sdk/graph/contract.py:25) |
| 92 | [s2p-copilot/backend/app/graph_contract.py:7](../../../s2p-copilot/backend/app/graph_contract.py:7) | copilot_sdk.graph.contract.NodeType | [copilot-sdk/copilot_sdk/graph/contract.py:9](../../../copilot-sdk/copilot_sdk/graph/contract.py:9) |
| 93 | [s2p-copilot/backend/app/graph/s2p_graph_reader.py:8](../../../s2p-copilot/backend/app/graph/s2p_graph_reader.py:8) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 94 | [s2p-copilot/backend/app/main.py:13](../../../s2p-copilot/backend/app/main.py:13) | copilot_sdk.backend.create_conservation_router | [copilot-sdk/copilot_sdk/backend/conservation_router.py:35](../../../copilot-sdk/copilot_sdk/backend/conservation_router.py:35) |
| 95 | [s2p-copilot/backend/app/main.py:13](../../../s2p-copilot/backend/app/main.py:13) | copilot_sdk.backend.create_evolution_router | [copilot-sdk/copilot_sdk/backend/evolution_router.py:38](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py:38) |
| 96 | [s2p-copilot/backend/app/main.py:13](../../../s2p-copilot/backend/app/main.py:13) | copilot_sdk.backend.create_measurement_state_router | [copilot-sdk/copilot_sdk/backend/scoring_router.py:435](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py:435) |
| 97 | [s2p-copilot/backend/app/main.py:18](../../../s2p-copilot/backend/app/main.py:18) | copilot_sdk.backend.budget_router.create_budget_router | [copilot-sdk/copilot_sdk/backend/budget_router.py:10](../../../copilot-sdk/copilot_sdk/backend/budget_router.py:10) |
| 98 | [s2p-copilot/backend/app/main.py:19](../../../s2p-copilot/backend/app/main.py:19) | copilot_sdk.auth.AuthMiddleware | [copilot-sdk/copilot_sdk/auth/middleware.py:8](../../../copilot-sdk/copilot_sdk/auth/middleware.py:8) |
| 99 | [s2p-copilot/backend/app/main.py:19](../../../s2p-copilot/backend/app/main.py:19) | copilot_sdk.auth.create_auth_router | [copilot-sdk/copilot_sdk/backend/auth_router.py:11](../../../copilot-sdk/copilot_sdk/backend/auth_router.py:11) |
| 100 | [s2p-copilot/backend/app/main.py:20](../../../s2p-copilot/backend/app/main.py:20) | copilot_sdk.evolution.ScorerBackedProvider | [copilot-sdk/copilot_sdk/evolution/conservation_contract.py:83](../../../copilot-sdk/copilot_sdk/evolution/conservation_contract.py:83) |
| 101 | [s2p-copilot/backend/app/main.py:21](../../../s2p-copilot/backend/app/main.py:21) | copilot_sdk.backend.self_computation_router.mount_self_computation_router | [copilot-sdk/copilot_sdk/backend/self_computation_router.py:596](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py:596) |
| 102 | [s2p-copilot/backend/app/main.py:22](../../../s2p-copilot/backend/app/main.py:22) | copilot_sdk.backend.counterfactual_router.create_counterfactual_router | [copilot-sdk/copilot_sdk/backend/counterfactual_router.py:35](../../../copilot-sdk/copilot_sdk/backend/counterfactual_router.py:35) |
| 103 | [s2p-copilot/backend/app/main.py:23](../../../s2p-copilot/backend/app/main.py:23) | copilot_sdk.backend.transfer_router.create_transfer_router | [copilot-sdk/copilot_sdk/backend/transfer_router.py:39](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py:39) |
| 104 | [s2p-copilot/backend/app/main.py:24](../../../s2p-copilot/backend/app/main.py:24) | copilot_sdk.backend.investigation_router.create_investigation_router | [copilot-sdk/copilot_sdk/backend/investigation_router.py:41](../../../copilot-sdk/copilot_sdk/backend/investigation_router.py:41) |
| 105 | [s2p-copilot/backend/app/main.py:25](../../../s2p-copilot/backend/app/main.py:25) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 106 | [s2p-copilot/backend/app/main.py:25](../../../s2p-copilot/backend/app/main.py:25) | copilot_sdk.config.require_shared_graph | [copilot-sdk/copilot_sdk/config/graph_config.py:26](../../../copilot-sdk/copilot_sdk/config/graph_config.py:26) |
| 107 | [s2p-copilot/backend/app/main.py:26](../../../s2p-copilot/backend/app/main.py:26) | copilot_sdk.graph.factory.create_graph_store | [copilot-sdk/copilot_sdk/graph/factory.py:129](../../../copilot-sdk/copilot_sdk/graph/factory.py:129) |
| 108 | [s2p-copilot/backend/app/main.py:27](../../../s2p-copilot/backend/app/main.py:27) | copilot_sdk.scoring.CompoundingScorer | [copilot-sdk/copilot_sdk/scoring/scorer.py:120](../../../copilot-sdk/copilot_sdk/scoring/scorer.py:120) |
| 109 | [s2p-copilot/backend/app/main.py:28](../../../s2p-copilot/backend/app/main.py:28) | copilot_sdk.scoring.investigation.KUtilityStore | [copilot-sdk/copilot_sdk/scoring/investigation.py:404](../../../copilot-sdk/copilot_sdk/scoring/investigation.py:404) |
| 110 | [s2p-copilot/backend/app/main.py:29](../../../s2p-copilot/backend/app/main.py:29) | copilot_sdk.scoring.situation_classifier.SituationClassifier as _BaseSituationClassifier | [copilot-sdk/copilot_sdk/scoring/situation_classifier.py:91](../../../copilot-sdk/copilot_sdk/scoring/situation_classifier.py:91) |
| 111 | [s2p-copilot/backend/app/main.py:30](../../../s2p-copilot/backend/app/main.py:30) | copilot_sdk.scoring.situation_classifier.SituationAssessment | [copilot-sdk/copilot_sdk/scoring/situation_classifier.py:84](../../../copilot-sdk/copilot_sdk/scoring/situation_classifier.py:84) |
| 112 | [s2p-copilot/backend/app/main.py:31](../../../s2p-copilot/backend/app/main.py:31) | copilot_sdk.scoring.budget_policy.AdaptiveBudgetPolicy | [copilot-sdk/copilot_sdk/scoring/budget_policy.py:13](../../../copilot-sdk/copilot_sdk/scoring/budget_policy.py:13) |
| 113 | [s2p-copilot/backend/app/main.py:32](../../../s2p-copilot/backend/app/main.py:32) | copilot_sdk.scoring.startup_restore.restore_l5_runtime_state | [copilot-sdk/copilot_sdk/scoring/startup_restore.py:14](../../../copilot-sdk/copilot_sdk/scoring/startup_restore.py:14) |
| 114 | [s2p-copilot/backend/app/main.py:33](../../../s2p-copilot/backend/app/main.py:33) | copilot_sdk.state.create_invalidation_header_middleware | [copilot-sdk/copilot_sdk/state/invalidation.py:85](../../../copilot-sdk/copilot_sdk/state/invalidation.py:85) |
| 115 | [s2p-copilot/backend/app/main.py:33](../../../s2p-copilot/backend/app/main.py:33) | copilot_sdk.state.create_tab_state_router | [copilot-sdk/copilot_sdk/state/tab_state_router.py:11](../../../copilot-sdk/copilot_sdk/state/tab_state_router.py:11) |
| 116 | [s2p-copilot/backend/app/routers/cohort_status_router.py:10](../../../s2p-copilot/backend/app/routers/cohort_status_router.py:10) | copilot_sdk.state.cached_static.cached_static | [copilot-sdk/copilot_sdk/state/cached_static.py:35](../../../copilot-sdk/copilot_sdk/state/cached_static.py:35) |
| 117 | [s2p-copilot/backend/app/routers/framework_router.py:21](../../../s2p-copilot/backend/app/routers/framework_router.py:21) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 118 | [s2p-copilot/backend/app/routers/s2p_auto_approve.py:10](../../../s2p-copilot/backend/app/routers/s2p_auto_approve.py:10) | copilot_sdk.scoring.mutation_lock.serialize_mutation | [copilot-sdk/copilot_sdk/scoring/mutation_lock.py:48](../../../copilot-sdk/copilot_sdk/scoring/mutation_lock.py:48) |
| 119 | [s2p-copilot/backend/app/routers/s2p_auto_approve.py:11](../../../s2p-copilot/backend/app/routers/s2p_auto_approve.py:11) | copilot_sdk.state.cached_static.cached_static | [copilot-sdk/copilot_sdk/state/cached_static.py:35](../../../copilot-sdk/copilot_sdk/state/cached_static.py:35) |
| 120 | [s2p-copilot/backend/app/routers/s2p_control_tower.py:9](../../../s2p-copilot/backend/app/routers/s2p_control_tower.py:9) | copilot_sdk.state.cached_static.cached_static | [copilot-sdk/copilot_sdk/state/cached_static.py:35](../../../copilot-sdk/copilot_sdk/state/cached_static.py:35) |
| 121 | [s2p-copilot/backend/app/routers/s2p_discovery.py:9](../../../s2p-copilot/backend/app/routers/s2p_discovery.py:9) | copilot_sdk.state.cached_static.cached_static | [copilot-sdk/copilot_sdk/state/cached_static.py:35](../../../copilot-sdk/copilot_sdk/state/cached_static.py:35) |
| 122 | [s2p-copilot/backend/app/routers/s2p_evidence.py:13](../../../s2p-copilot/backend/app/routers/s2p_evidence.py:13) | copilot_sdk.state.cached_static.cached_static | [copilot-sdk/copilot_sdk/state/cached_static.py:35](../../../copilot-sdk/copilot_sdk/state/cached_static.py:35) |
| 123 | [s2p-copilot/backend/app/routers/s2p_evidence.py:24](../../../s2p-copilot/backend/app/routers/s2p_evidence.py:24) | copilot_sdk.situation.SituationAnalyzer | [copilot-sdk/copilot_sdk/situation/analyzer.py:20](../../../copilot-sdk/copilot_sdk/situation/analyzer.py:20) |
| 124 | [s2p-copilot/backend/app/routers/s2p_evidence.py:24](../../../s2p-copilot/backend/app/routers/s2p_evidence.py:24) | copilot_sdk.situation.SituationContext | [copilot-sdk/copilot_sdk/situation/models.py:213](../../../copilot-sdk/copilot_sdk/situation/models.py:213) |
| 125 | [s2p-copilot/backend/app/routers/s2p_evolution.py:7](../../../s2p-copilot/backend/app/routers/s2p_evolution.py:7) | copilot_sdk.scoring.mutation_lock.serialize_mutation | [copilot-sdk/copilot_sdk/scoring/mutation_lock.py:48](../../../copilot-sdk/copilot_sdk/scoring/mutation_lock.py:48) |
| 126 | [s2p-copilot/backend/app/routers/s2p_explorer.py:17](../../../s2p-copilot/backend/app/routers/s2p_explorer.py:17) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 127 | [s2p-copilot/backend/app/routers/s2p_novelty.py:7](../../../s2p-copilot/backend/app/routers/s2p_novelty.py:7) | copilot_sdk.state.cached_static.cached_static | [copilot-sdk/copilot_sdk/state/cached_static.py:35](../../../copilot-sdk/copilot_sdk/state/cached_static.py:35) |
| 128 | [s2p-copilot/backend/app/routers/s2p_preview.py:15](../../../s2p-copilot/backend/app/routers/s2p_preview.py:15) | copilot_sdk.state.cached_static.cached_static | [copilot-sdk/copilot_sdk/state/cached_static.py:35](../../../copilot-sdk/copilot_sdk/state/cached_static.py:35) |
| 129 | [s2p-copilot/backend/app/routers/s2p_preview.py:16](../../../s2p-copilot/backend/app/routers/s2p_preview.py:16) | copilot_sdk.graph.protocol.ProtocolV2GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:264](../../../copilot-sdk/copilot_sdk/graph/protocol.py:264) |
| 130 | [s2p-copilot/backend/app/routers/s2p_preview.py:281](../../../s2p-copilot/backend/app/routers/s2p_preview.py:281) | copilot_sdk.graph.memory_store.InMemoryGraphStore | [copilot-sdk/copilot_sdk/graph/memory_store.py:327](../../../copilot-sdk/copilot_sdk/graph/memory_store.py:327) |
| 131 | [s2p-copilot/backend/app/routers/s2p_process_fusion.py:9](../../../s2p-copilot/backend/app/routers/s2p_process_fusion.py:9) | copilot_sdk.enterprise.process_ingest.ProcessExportIngester | [copilot-sdk/copilot_sdk/enterprise/process_ingest.py:22](../../../copilot-sdk/copilot_sdk/enterprise/process_ingest.py:22) |
| 132 | [s2p-copilot/backend/app/routers/s2p_situation.py:11](../../../s2p-copilot/backend/app/routers/s2p_situation.py:11) | copilot_sdk.situation.NLRenderer | [copilot-sdk/copilot_sdk/situation/renderer.py:38](../../../copilot-sdk/copilot_sdk/situation/renderer.py:38) |
| 133 | [s2p-copilot/backend/app/routers/s2p_situation.py:11](../../../s2p-copilot/backend/app/routers/s2p_situation.py:11) | copilot_sdk.situation.SituationAnalyzer | [copilot-sdk/copilot_sdk/situation/analyzer.py:20](../../../copilot-sdk/copilot_sdk/situation/analyzer.py:20) |
| 134 | [s2p-copilot/backend/app/routers/s2p.py:27](../../../s2p-copilot/backend/app/routers/s2p.py:27) | copilot_sdk.backend.conservation_utils.compute_conservation_metrics | [copilot-sdk/copilot_sdk/backend/conservation_utils.py:194](../../../copilot-sdk/copilot_sdk/backend/conservation_utils.py:194) |
| 135 | [s2p-copilot/backend/app/routers/s2p.py:27](../../../s2p-copilot/backend/app/routers/s2p.py:27) | copilot_sdk.backend.conservation_utils.compute_conservation_status_payload | [copilot-sdk/copilot_sdk/backend/conservation_utils.py:61](../../../copilot-sdk/copilot_sdk/backend/conservation_utils.py:61) |
| 136 | [s2p-copilot/backend/app/routers/s2p.py:31](../../../s2p-copilot/backend/app/routers/s2p.py:31) | copilot_sdk.backend.diagnostics_models.build_diagnostics | [copilot-sdk/copilot_sdk/backend/diagnostics_models.py:297](../../../copilot-sdk/copilot_sdk/backend/diagnostics_models.py:297) |
| 137 | [s2p-copilot/backend/app/routers/s2p.py:32](../../../s2p-copilot/backend/app/routers/s2p.py:32) | copilot_sdk.graph.protocol.ProtocolV2GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:264](../../../copilot-sdk/copilot_sdk/graph/protocol.py:264) |
| 138 | [s2p-copilot/backend/app/routers/s2p.py:33](../../../s2p-copilot/backend/app/routers/s2p.py:33) | copilot_sdk.scoring.mutation_lock.get_mutation_lock | [copilot-sdk/copilot_sdk/scoring/mutation_lock.py:17](../../../copilot-sdk/copilot_sdk/scoring/mutation_lock.py:17) |
| 139 | [s2p-copilot/backend/app/routers/s2p.py:33](../../../s2p-copilot/backend/app/routers/s2p.py:33) | copilot_sdk.scoring.mutation_lock.serialize_mutation | [copilot-sdk/copilot_sdk/scoring/mutation_lock.py:48](../../../copilot-sdk/copilot_sdk/scoring/mutation_lock.py:48) |
| 140 | [s2p-copilot/backend/app/routers/s2p.py:34](../../../s2p-copilot/backend/app/routers/s2p.py:34) | copilot_sdk.scoring.dk_persistence.DKWelfordTracker | [copilot-sdk/copilot_sdk/scoring/dk_persistence.py:120](../../../copilot-sdk/copilot_sdk/scoring/dk_persistence.py:120) |
| 141 | [s2p-copilot/backend/app/routers/s2p.py:34](../../../s2p-copilot/backend/app/routers/s2p.py:34) | copilot_sdk.scoring.dk_persistence.persist_dk_after_reestimate | [copilot-sdk/copilot_sdk/scoring/dk_persistence.py:231](../../../copilot-sdk/copilot_sdk/scoring/dk_persistence.py:231) |
| 142 | [s2p-copilot/backend/app/routers/s2p.py:35](../../../s2p-copilot/backend/app/routers/s2p.py:35) | copilot_sdk.state.invalidation.apply_cache_invalidation_event | [copilot-sdk/copilot_sdk/state/invalidation.py:70](../../../copilot-sdk/copilot_sdk/state/invalidation.py:70) |
| 143 | [s2p-copilot/backend/app/routers/s2p.py:35](../../../s2p-copilot/backend/app/routers/s2p.py:35) | copilot_sdk.state.invalidation.get_tab_state_cache | [copilot-sdk/copilot_sdk/state/invalidation.py:48](../../../copilot-sdk/copilot_sdk/state/invalidation.py:48) |
| 144 | [s2p-copilot/backend/app/routers/s2p.py:36](../../../s2p-copilot/backend/app/routers/s2p.py:36) | copilot_sdk.state.cached_static.cached_static | [copilot-sdk/copilot_sdk/state/cached_static.py:35](../../../copilot-sdk/copilot_sdk/state/cached_static.py:35) |
| 145 | [s2p-copilot/backend/app/s2p_graph_status.py:16](../../../s2p-copilot/backend/app/s2p_graph_status.py:16) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 146 | [s2p-copilot/backend/app/s2p_graph_status.py:16](../../../s2p-copilot/backend/app/s2p_graph_status.py:16) | copilot_sdk.config.GraphConfigError | [copilot-sdk/copilot_sdk/config/graph_config.py:22](../../../copilot-sdk/copilot_sdk/config/graph_config.py:22) |
| 147 | [s2p-copilot/backend/app/s2p_graph_status.py:16](../../../s2p-copilot/backend/app/s2p_graph_status.py:16) | copilot_sdk.config.require_shared_graph | [copilot-sdk/copilot_sdk/config/graph_config.py:26](../../../copilot-sdk/copilot_sdk/config/graph_config.py:26) |
| 148 | [s2p-copilot/backend/app/s2p_graph_status.py:352](../../../s2p-copilot/backend/app/s2p_graph_status.py:352) | copilot_sdk.graph.factory.create_graph_store | [copilot-sdk/copilot_sdk/graph/factory.py:129](../../../copilot-sdk/copilot_sdk/graph/factory.py:129) |
| 149 | [s2p-copilot/backend/app/s2p_shadow.py:18](../../../s2p-copilot/backend/app/s2p_shadow.py:18) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 150 | [s2p-copilot/backend/app/s2p_shadow.py:18](../../../s2p-copilot/backend/app/s2p_shadow.py:18) | copilot_sdk.config.GraphConfigError | [copilot-sdk/copilot_sdk/config/graph_config.py:22](../../../copilot-sdk/copilot_sdk/config/graph_config.py:22) |
| 151 | [s2p-copilot/backend/app/s2p_shadow.py:165](../../../s2p-copilot/backend/app/s2p_shadow.py:165) | copilot_sdk.graph.factory.create_graph_store | [copilot-sdk/copilot_sdk/graph/factory.py:129](../../../copilot-sdk/copilot_sdk/graph/factory.py:129) |
| 152 | [s2p-copilot/backend/app/seed_graph.py:11](../../../s2p-copilot/backend/app/seed_graph.py:11) | copilot_sdk.config.GraphConfig | [copilot-sdk/copilot_sdk/config/graph_config.py:69](../../../copilot-sdk/copilot_sdk/config/graph_config.py:69) |
| 153 | [s2p-copilot/backend/app/services/centroid_explorer.py:11](../../../s2p-copilot/backend/app/services/centroid_explorer.py:11) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 154 | [s2p-copilot/backend/app/services/cohort_status.py:9](../../../s2p-copilot/backend/app/services/cohort_status.py:9) | copilot_sdk.substantiation.cohort_day_zero.BaseCohortDayZeroState | [copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:68](../../../copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:68) |
| 155 | [s2p-copilot/backend/app/services/cohort_status.py:9](../../../s2p-copilot/backend/app/services/cohort_status.py:9) | copilot_sdk.substantiation.cohort_day_zero.compute_state | [copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:19](../../../copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:19) |
| 156 | [s2p-copilot/backend/app/services/cohort_status.py:9](../../../s2p-copilot/backend/app/services/cohort_status.py:9) | copilot_sdk.substantiation.cohort_day_zero.evaluate_v7_gate as _sdk_evaluate_v7_gate | [copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:32](../../../copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:32) |
| 157 | [s2p-copilot/backend/app/services/cohort_status.py:9](../../../s2p-copilot/backend/app/services/cohort_status.py:9) | copilot_sdk.substantiation.cohort_day_zero.STATES | [copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:16](../../../copilot-sdk/copilot_sdk/substantiation/cohort_day_zero.py:16) |
| 158 | [s2p-copilot/backend/app/services/compounding_ledger.py:13](../../../s2p-copilot/backend/app/services/compounding_ledger.py:13) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 159 | [s2p-copilot/backend/app/services/proposal_service.py:12](../../../s2p-copilot/backend/app/services/proposal_service.py:12) | copilot_sdk.outcome.models.VerifiedOutcome | [copilot-sdk/copilot_sdk/outcome/models.py:39](../../../copilot-sdk/copilot_sdk/outcome/models.py:39) |
| 160 | [s2p-copilot/backend/app/services/proposal_service.py:15](../../../s2p-copilot/backend/app/services/proposal_service.py:15) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 161 | [s2p-copilot/backend/app/services/s2p_autonomy.py:9](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:9) | copilot_sdk.evolution.ScorerBackedProvider | [copilot-sdk/copilot_sdk/evolution/conservation_contract.py:83](../../../copilot-sdk/copilot_sdk/evolution/conservation_contract.py:83) |
| 162 | [s2p-copilot/backend/app/services/s2p_autonomy.py:10](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:10) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 163 | [s2p-copilot/backend/app/services/s2p_autonomy.py:11](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:11) | copilot_sdk.promotion.PromotionEngine | [copilot-sdk/copilot_sdk/promotion/core.py:212](../../../copilot-sdk/copilot_sdk/promotion/core.py:212) |
| 164 | [s2p-copilot/backend/app/services/s2p_autonomy.py:11](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:11) | copilot_sdk.promotion.PromotionRecord | [copilot-sdk/copilot_sdk/promotion/core.py:52](../../../copilot-sdk/copilot_sdk/promotion/core.py:52) |
| 165 | [s2p-copilot/backend/app/services/s2p_autonomy.py:11](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:11) | copilot_sdk.promotion.PromotionResult | [copilot-sdk/copilot_sdk/promotion/core.py:102](../../../copilot-sdk/copilot_sdk/promotion/core.py:102) |
| 166 | [s2p-copilot/backend/app/services/s2p_autonomy.py:11](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:11) | copilot_sdk.promotion.PromotionStore | [copilot-sdk/copilot_sdk/promotion/core.py:110](../../../copilot-sdk/copilot_sdk/promotion/core.py:110) |
| 167 | [s2p-copilot/backend/app/services/s2p_autonomy.py:11](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:11) | copilot_sdk.promotion.S2PPromotionPolicy | [copilot-sdk/copilot_sdk/promotion/policies.py:41](../../../copilot-sdk/copilot_sdk/promotion/policies.py:41) |
| 168 | [s2p-copilot/backend/app/services/s2p_autonomy.py:18](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:18) | copilot_sdk.twin.FrozenTwin | [copilot-sdk/copilot_sdk/twin/service.py:17](../../../copilot-sdk/copilot_sdk/twin/service.py:17) |
| 169 | [s2p-copilot/backend/app/services/s2p_autonomy.py:18](../../../s2p-copilot/backend/app/services/s2p_autonomy.py:18) | copilot_sdk.twin.FrozenTwinStore | [copilot-sdk/copilot_sdk/twin/store.py:14](../../../copilot-sdk/copilot_sdk/twin/store.py:14) |
| 170 | [s2p-copilot/backend/app/services/s2p_context_builder.py:9](../../../s2p-copilot/backend/app/services/s2p_context_builder.py:9) | copilot_sdk.situation.TraversalEdge | [copilot-sdk/copilot_sdk/situation/models.py:193](../../../copilot-sdk/copilot_sdk/situation/models.py:193) |
| 171 | [s2p-copilot/backend/app/services/s2p_context_builder.py:9](../../../s2p-copilot/backend/app/services/s2p_context_builder.py:9) | copilot_sdk.situation.TraversalNode | [copilot-sdk/copilot_sdk/situation/models.py:171](../../../copilot-sdk/copilot_sdk/situation/models.py:171) |
| 172 | [s2p-copilot/backend/app/services/s2p_context_builder.py:10](../../../s2p-copilot/backend/app/services/s2p_context_builder.py:10) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 173 | [s2p-copilot/backend/app/services/s2p_enrichment.py:10](../../../s2p-copilot/backend/app/services/s2p_enrichment.py:10) | copilot_sdk.graph.enrichment.EnrichmentSourceSet | [copilot-sdk/copilot_sdk/graph/enrichment.py:154](../../../copilot-sdk/copilot_sdk/graph/enrichment.py:154) |
| 174 | [s2p-copilot/backend/app/services/s2p_enrichment.py:10](../../../s2p-copilot/backend/app/services/s2p_enrichment.py:10) | copilot_sdk.graph.enrichment.EntityEnrichmentReceipt | [copilot-sdk/copilot_sdk/graph/enrichment.py:171](../../../copilot-sdk/copilot_sdk/graph/enrichment.py:171) |
| 175 | [s2p-copilot/backend/app/services/s2p_enrichment.py:10](../../../s2p-copilot/backend/app/services/s2p_enrichment.py:10) | copilot_sdk.graph.enrichment.EntityEnrichmentRecord | [copilot-sdk/copilot_sdk/graph/enrichment.py:187](../../../copilot-sdk/copilot_sdk/graph/enrichment.py:187) |
| 176 | [s2p-copilot/backend/app/services/s2p_enrichment.py:10](../../../s2p-copilot/backend/app/services/s2p_enrichment.py:10) | copilot_sdk.graph.enrichment.ProvenancedValue | [copilot-sdk/copilot_sdk/graph/enrichment.py:41](../../../copilot-sdk/copilot_sdk/graph/enrichment.py:41) |
| 177 | [s2p-copilot/backend/app/services/s2p_enrichment.py:16](../../../s2p-copilot/backend/app/services/s2p_enrichment.py:16) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 178 | [s2p-copilot/backend/app/services/s2p_evidence_templates.py:8](../../../s2p-copilot/backend/app/services/s2p_evidence_templates.py:8) | copilot_sdk.situation.templates.SafeTemplateRenderer | [copilot-sdk/copilot_sdk/situation/templates.py:53](../../../copilot-sdk/copilot_sdk/situation/templates.py:53) |
| 179 | [s2p-copilot/backend/app/services/s2p_evolver.py:9](../../../s2p-copilot/backend/app/services/s2p_evolver.py:9) | copilot_sdk.evolution.ConservationStateProvider | [copilot-sdk/copilot_sdk/evolution/conservation_contract.py:34](../../../copilot-sdk/copilot_sdk/evolution/conservation_contract.py:34) |
| 180 | [s2p-copilot/backend/app/services/s2p_evolver.py:9](../../../s2p-copilot/backend/app/services/s2p_evolver.py:9) | copilot_sdk.evolution.PromptVariantEvolver | [copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:58](../../../copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:58) |
| 181 | [s2p-copilot/backend/app/services/s2p_evolver.py:9](../../../s2p-copilot/backend/app/services/s2p_evolver.py:9) | copilot_sdk.evolution.VariantSpec | [copilot-sdk/copilot_sdk/evolution/variant_store.py:19](../../../copilot-sdk/copilot_sdk/evolution/variant_store.py:19) |
| 182 | [s2p-copilot/backend/app/services/s2p_evolver.py:14](../../../s2p-copilot/backend/app/services/s2p_evolver.py:14) | copilot_sdk.evolution.graph_store.GraphVariantStore | [copilot-sdk/copilot_sdk/evolution/graph_store.py:125](../../../copilot-sdk/copilot_sdk/evolution/graph_store.py:125) |
| 183 | [s2p-copilot/backend/app/services/s2p_evolver.py:15](../../../s2p-copilot/backend/app/services/s2p_evolver.py:15) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 184 | [s2p-copilot/backend/app/services/s2p_situation_pattern.py:8](../../../s2p-copilot/backend/app/services/s2p_situation_pattern.py:8) | copilot_sdk.situation.SituationContext | [copilot-sdk/copilot_sdk/situation/models.py:213](../../../copilot-sdk/copilot_sdk/situation/models.py:213) |
| 185 | [s2p-copilot/backend/app/services/s2p_situation_pattern.py:8](../../../s2p-copilot/backend/app/services/s2p_situation_pattern.py:8) | copilot_sdk.situation.TraversalEdge | [copilot-sdk/copilot_sdk/situation/models.py:193](../../../copilot-sdk/copilot_sdk/situation/models.py:193) |
| 186 | [s2p-copilot/backend/app/services/s2p_situation_pattern.py:8](../../../s2p-copilot/backend/app/services/s2p_situation_pattern.py:8) | copilot_sdk.situation.TraversalNode | [copilot-sdk/copilot_sdk/situation/models.py:171](../../../copilot-sdk/copilot_sdk/situation/models.py:171) |
| 187 | [s2p-copilot/backend/app/services/s2p_situation_pattern.py:8](../../../s2p-copilot/backend/app/services/s2p_situation_pattern.py:8) | copilot_sdk.situation.TypedIntent | [copilot-sdk/copilot_sdk/situation/models.py:100](../../../copilot-sdk/copilot_sdk/situation/models.py:100) |
| 188 | [s2p-copilot/backend/app/services/situation_graph_enrichment.py:8](../../../s2p-copilot/backend/app/services/situation_graph_enrichment.py:8) | copilot_sdk.graph.enrichment.EnrichmentSourceSet | [copilot-sdk/copilot_sdk/graph/enrichment.py:154](../../../copilot-sdk/copilot_sdk/graph/enrichment.py:154) |
| 189 | [s2p-copilot/backend/app/services/situation_graph_enrichment.py:8](../../../s2p-copilot/backend/app/services/situation_graph_enrichment.py:8) | copilot_sdk.graph.enrichment.ProvenancedValue | [copilot-sdk/copilot_sdk/graph/enrichment.py:41](../../../copilot-sdk/copilot_sdk/graph/enrichment.py:41) |
| 190 | [s2p-copilot/backend/app/services/situation_graph_enrichment.py:9](../../../s2p-copilot/backend/app/services/situation_graph_enrichment.py:9) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 191 | [s2p-copilot/backend/app/services/situation_traversals.py:8](../../../s2p-copilot/backend/app/services/situation_traversals.py:8) | copilot_sdk.situation.ContextChain | [copilot-sdk/copilot_sdk/situation/models.py:245](../../../copilot-sdk/copilot_sdk/situation/models.py:245) |
| 192 | [s2p-copilot/backend/app/services/situation_traversals.py:8](../../../s2p-copilot/backend/app/services/situation_traversals.py:8) | copilot_sdk.situation.SituationContext | [copilot-sdk/copilot_sdk/situation/models.py:213](../../../copilot-sdk/copilot_sdk/situation/models.py:213) |
| 193 | [s2p-copilot/backend/app/services/situation_traversals.py:8](../../../s2p-copilot/backend/app/services/situation_traversals.py:8) | copilot_sdk.situation.TraversalEdge | [copilot-sdk/copilot_sdk/situation/models.py:193](../../../copilot-sdk/copilot_sdk/situation/models.py:193) |
| 194 | [s2p-copilot/backend/app/services/situation_traversals.py:8](../../../s2p-copilot/backend/app/services/situation_traversals.py:8) | copilot_sdk.situation.TraversalNode | [copilot-sdk/copilot_sdk/situation/models.py:171](../../../copilot-sdk/copilot_sdk/situation/models.py:171) |
| 195 | [s2p-copilot/backend/app/services/situation_traversals.py:8](../../../s2p-copilot/backend/app/services/situation_traversals.py:8) | copilot_sdk.situation.TypedIntent | [copilot-sdk/copilot_sdk/situation/models.py:100](../../../copilot-sdk/copilot_sdk/situation/models.py:100) |
| 196 | [s2p-copilot/backend/app/services/situation_traversals.py:15](../../../s2p-copilot/backend/app/services/situation_traversals.py:15) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 197 | [s2p-copilot/backend/app/services/situation_traversals.py:15](../../../s2p-copilot/backend/app/services/situation_traversals.py:15) | copilot_sdk.graph.protocol.GraphTraversalStore | [copilot-sdk/copilot_sdk/graph/protocol.py:238](../../../copilot-sdk/copilot_sdk/graph/protocol.py:238) |
| 198 | [s2p-copilot/backend/app/services/supplier_intelligence.py:11](../../../s2p-copilot/backend/app/services/supplier_intelligence.py:11) | copilot_sdk.graph.enrichment.ProvenancedValue | [copilot-sdk/copilot_sdk/graph/enrichment.py:41](../../../copilot-sdk/copilot_sdk/graph/enrichment.py:41) |
| 199 | [s2p-copilot/backend/app/services/supplier_intelligence.py:12](../../../s2p-copilot/backend/app/services/supplier_intelligence.py:12) | copilot_sdk.graph.protocol.GraphStore | [copilot-sdk/copilot_sdk/graph/protocol.py:16](../../../copilot-sdk/copilot_sdk/graph/protocol.py:16) |
| 200 | [s2p-copilot/backend/app/state/s2p_registry.py:11](../../../s2p-copilot/backend/app/state/s2p_registry.py:11) | copilot_sdk.state.register_tab_state_cache | [copilot-sdk/copilot_sdk/state/invalidation.py:43](../../../copilot-sdk/copilot_sdk/state/invalidation.py:43) |
| 201 | [s2p-copilot/backend/app/state/s2p_registry.py:11](../../../s2p-copilot/backend/app/state/s2p_registry.py:11) | copilot_sdk.state.TabStateCache | [copilot-sdk/copilot_sdk/state/tab_state_cache.py:75](../../../copilot-sdk/copilot_sdk/state/tab_state_cache.py:75) |
| 202 | [s2p-copilot/backend/app/state/s2p_registry.py:12](../../../s2p-copilot/backend/app/state/s2p_registry.py:12) | copilot_sdk.backend.conservation_utils.compute_conservation_status_payload | [copilot-sdk/copilot_sdk/backend/conservation_utils.py:61](../../../copilot-sdk/copilot_sdk/backend/conservation_utils.py:61) |

## Audit Completion

- Repositories analyzed: **3**.
- Cross-repo SDK symbol imports statically verified: **202 occurrences / 115 unique symbols**.
- Response-contract families compared: **6**.
- Ranked findings: **P1: 1 | P2: 8 | P3: 0**.
- Live probes: **16**, with unavailable/error responses explicitly distinguished from successful contract verification.
- Source files modified: **0**. Existing files modified: **0**. This report is **1 newly created file**.
- Frozen SHA-256 prefixes inspected: investigation.py **3441dcbd**, investigation_router.py **08f4df7a**, scorer.py **24ac9e49**.

