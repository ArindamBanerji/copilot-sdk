# Sweep 5 — Conservation and Three-Layer Safety Gate

Date: 2026-09-18. Read-only audit; final evidence review at 23:35 UTC.

## Summary

**The claim that the same three-layer safety gate is enforced across all five copilots is not supported by the current code.** All three layer calculations exist, but reporting, learning enforcement, evolution promotion, and verified-outcome inputs do not share one gate implementation.

- **P1 F01:** Trading, Purchasing, DataOps, and S2P do not call the three-layer SDK adapter in their underlying learning gate. It is invoked by the HTTP status route, not by `CompoundingScorer.learn()` or its promotion-state provider.
- **P1 F02:** SOC's relative/rate layers consume `LearningState.history`, while the live outcome route updates the separate scorer and increments the LearningState counter without appending that history. Persisting/restoring this history does not make it current.
- **P1 F03:** SOC currently returns HTTP 500, not a RED payload. Server logs confirm an AGE/PostgreSQL connection failure escapes the learning-health route. The other three SDK backends return controlled 503s for the same reported database-connection symptom.
- **P2 F04/F05:** SDK relative reporting falls back to comparing accuracy against 70% of itself. S2P additionally supplies counts without outcomes: its live GREEN response has 196 verified decisions but a zero-length G-RATE window.
- **Historical SOC RED:** zero qualifying verified coverage makes `alpha=0`, `V=0`, `theta_min=1e9`, and the absolute check fail. There is a confirmed mismatch between the verified populations used by SOC health and its snapshot/SDK store. The historical rows cannot be re-examined through the failing health query, so the audit does **not** claim that restart loss, missing timestamps, or missing categories alone has been proven to explain that earlier zero.

**Findings: 3 P1, 7 P2, 1 P3.** The bug-hunt stop threshold of five P1 findings was not reached. **20 focused tests passed** (12 SDK + 8 SOC). These are not five-copilot enforcement integration tests.

No source, test, configuration, fixture, experiment result, or session-state file was edited. This report is the only intentionally created artifact. No server was restarted, no preseed was run, and no mutating demo POST was issued.

### Scope and evidence conventions

Paths below use these workspace-relative aliases:

- `SDK` = `copilot-sdk`
- `SOC` = `gen-ai-roi-demo-v4-v50`
- `S2P` = `s2p-copilot`
- `CI` = `ci-platform`
- `GAE` = `graph-attention-engine-v50`

Read SDK `CLAUDE.md`, session-state precheck, and `docs/design/bug_hunt_v5.md`. Findings follow LOCATE → READ → TRACE → VERDICT → CLASSIFY. LIVE means observed HTTP/log evidence; ISOLATED means a production pure function or disposable in-process FastAPI app; SOURCE TRACE means a source-derived execution path, not a live injected threat. No production poisoning/drop experiment was performed.

The requested `SDK/copilot_sdk/scoring/conservation.py` and `compounding.py` are not the implementation paths in this checkout. Relevant code is `scoring/composite_gate.py`, `scoring/scorer.py`, `backend/conservation_utils.py`, and `GAE/gae/calibration.py`. Framework files also named `composite_gate.py` concern other gate composition and are not evidence that the scoring adapter is enforced.

## Live Conservation State (all 5 copilots)

GET `/api/conservation/status`, repeated where errors occurred:

| Copilot | Port | HTTP / status | Verified / correct | Alpha / q / theta_min | G-RATE evidence |
|---|---:|---|---|---|---|
| SOC | 8001 | 500, `Internal Server Error` | Unavailable from conservation | Unavailable | Unavailable; cannot infer inactive or active from an error |
| S2P | 8002 | 200, GREEN; passed=true | 196 / 173 | 0.8 / 0.8826530612244898 / 0.1501 | active=false; short_accuracy=null; short_window_count=0 |
| Trading | 8010 | 503 | Unavailable | Unavailable | Unavailable |
| Purchasing | 8020 | 503 | Unavailable | Unavailable | Unavailable |
| DataOps | 8030 | 503 | Unavailable | Unavailable | Unavailable |

All three 503 bodies report `Graph store unavailable: consuming input failed: server closed the connection unexpectedly`. This proves availability failure at the conservation dependency, not missing route mounts, nor a zero verified population. The audit did not determine why PostgreSQL closed the connections. Docker CLI was unavailable; no infrastructure changes were attempted.

S2P's remaining observed values:

```text
signal=138.4; headroom=138.2499; V=196
categories_with_data=4; categories_total=5; penalty_ratio=5
baseline=baseline_q=q=0.8826530612244898
g_abs.active=false
g_rel.active=false; threshold=0.6178571428571429
g_rate.long_baseline=0.8826530612244898
g_rate.threshold=0.7502551020408164; w_short=20; m_rate=0.85
conservation_mode=normal; conservation_applicable=true
```

Other non-mutating SOC probes:

- `/api/soc/learning-health`: the same HTTP 500.
- `/api/soc/learning-state`: HTTP 200; frozen=true, decision_count=4862, verified_decisions=4862, last_verified_at=null, total_decisions=0, categories_active=0, iks_v2=94.1, interpretation=`Snapshot-backed institutional knowledge score`.
- `/api/health`: HTTP 200, healthy; graph health source=`posterior_store`. This is not evidence that the failing conservation query succeeds.

The 4862 value is a snapshot/display result, not a fresh successful execution of the conservation population query. The SDK status decorator can also return materialized cache entries (`SDK/copilot_sdk/state/cached_static.py:103–118`); a 200 alone does not prove a new graph read.

## SOC RED Diagnosis (root cause analysis)

### Historical RED and current 500 are different observations

The prior design review records HTTP 200 with RED, theta_min=1e9, verified_count=0 (`SDK/docs/design/demo_features_design_v2.md:123`). The current source explains the immediate arithmetic:

1. `LearningHealthMonitor.evaluate()` obtains LearningState history and then replaces its diagnostic accuracy/count with graph-derived SOC verified statistics (`SOC/backend/app/services/learning_health.py:314–323`).
2. With no qualifying graph rows, `_query_soc_verified_conservation_stats()` returns zero categories, verified, and correct counts (`:599–621`). `_apply_soc_conservation_components()` consequently sets alpha=0, q=0, V=0 (`:229–255`).
3. `evaluate()` selects the explicit **conservative sentinel** 1,000,000,000 when alpha<=0 or V<=0 (`:324–325`). This is not a calibrated deployment floor.
4. Signal=0 fails the absolute conservation check. For a LearningState counter >=300 and learning enabled, the steady branch returns RED (`:422–427`), even if that counter was populated by bootstrap or historical learning state.
5. The snapshot's verified count is not used to repair the conservation inputs. Treating 4862 as V without verifying the population would conceal the discrepancy.

There is a concrete population mismatch (F06): snapshot/store counts accept active SOC decisions with status confirmed/overridden, while SOC health additionally requires `Decision.verified_at_epoch`, canonical category, and a different status/outcome predicate. Shared SDK outcome writes can persist `Outcome.verified_at` without `Decision.verified_at_epoch`. These records can count in one surface and not the other.

**Conclusion:** historical RED is consistent with a zero-coverage fail-closed input path, not evidence of G-RATE detecting a sudden drop. Population/schema mismatch and bootstrap-vs-verified counts are confirmed risks; attributing every historical zero to a specific missing field remains unproven during the database outage. There is no evidence here of wholesale conservation reset on restart.

### Current failure is confirmed by logs

`SDK/logs/soc.log` contains the observed route stack:

```text
framework_router.py:750 -> LearningHealthMonitor.evaluate()
learning_health.py:320 -> _apply_soc_conservation_components()
learning_health.py:215 -> _query_soc_verified_conservation_stats()
learning_health.py:597 -> RuntimeError("AGE query failed for SOC conservation stats")
cause: psycopg.OperationalError: consuming input failed:
       server closed the connection unexpectedly
```

No fresh RED/AMBER/GREEN classification is available from those failed requests. The live learning-state handler catches graph-read errors and retains snapshot fields (`SOC/backend/app/routers/soc.py:1040–1079`), explaining why it still displays 4862 while conservation fails.

## Gate Parameter Matrix (per copilot)

| Copilot | Absolute floor actually computed | Relative reporting | Rate reporting | Learning enforcement / provider |
|---|---|---|---|---|
| Trading | 23.53/(alpha*V), with regime adjustment | .7 × supplied baseline, otherwise current lifetime q | W=20, m=.85; latest up to400 outcome values | CompoundingScorer legacy ABS + last100 accuracy<.75 + dispersion; Trading regime wrapper; ScorerBackedProvider over proxy |
| Purchasing | 23.53/(alpha*V) | Same fallback | Same defaults | Same underlying legacy scorer gate; ScorerBackedProvider over FreshScorerProxy |
| DataOps | 23.53/(alpha*V) | Same fallback | Same defaults | Same underlying legacy scorer gate; ScorerBackedProvider over FreshScorerProxy |
| S2P | 23.53/(alpha*V) | Same fallback; live baseline=q | W=20, m=.85 advertised, but no outcomes supplied | Counts-only route gate plus CompoundingScorer; ScorerBackedProvider for evolution/autonomy |
| SOC | 23.53/(alpha*V), or 1e9 if no coverage/count | .7 × **first** up to400 history outcomes vs latest400 | W=20, m=.85 against **first** up to400 history outcomes | LearningHealthMonitor → effective status → raw scorer conservation state/guarded_update; SOCConservationProvider with CachedAsyncProvider |

Evidence: `GAE/gae/calibration.py:194–198,440–477`; SDK gate `:18–26,39–48`; SOC monitor `:44–49,98–118,324–329`; scorer `:2198–2300`; S2P `backend/app/routers/s2p.py:1005–1082`.

Important qualifications:

- Current runtime floor formula is **not** the fixed SOC=.764, S2P=.769, Trading=.766, Purchasing=.655, DataOps=.669 floor used by the A1 experiment. The asserted experimental V_clear≈3 is not a verified current production cold-start threshold.
- SDK learning explicitly allows V=0 and V=1–9 as COLD_START/BOOTSTRAP (`scorer.py:2229–2243`). SOC uses a 300-decision LearningState calibration branch. These policies differ materially.
- Trading/Purchasing/DataOps presets expose w_short20/m_rate.85 (`presets/trading.py:90–95`, `purchasing.py:84–89`, `dataops.py:78–83`). FreshScorerProxy does not expose `_preset`; the shared route generally uses its own defaults. Equal observed defaults do not establish that approved preset changes would reach the route.
- Penalty ratios in the current presets are SOC20, S2P5, Trading3, Purchasing3, DataOps10. The GAE floor helper does not use penalty_ratio, despite its presence in status payloads.
- `q` in shared status is **correct/verified lifetime accuracy**, not a decision count and not explicitly a 400-decision rolling mean. The gate's short-window baseline is separately computed from rows. S2P's count-only provider cannot supply that sequence.

## Preseed → Conservation Chain Analysis

| Copilot | Preseed/outcome path | Durable evidence | Restart behavior and gap |
|---|---|---|---|
| Trading | SDK preseed POST score → POST learn; current target200, overrides50 | Decision + Outcome through GraphStore; centroid/conservation artifacts | Graph-backed counts survive restart; lazy proxy creates scorer from persisted state. No shared G-RATE enforcement; a paused learn does not accept the new outcome (F09) |
| Purchasing | Same SDK preseed/learn path | Same | Same |
| DataOps | Same SDK preseed/learn path | Same | Same |
| S2P | SDK script includes S2P scoring/verification path; native score/learn handlers | S2P GraphStore; cached count provider | Caches are process-local and reconstructed; G-RATE history is absent from the status-provider contract, not merely lost at restart |
| SOC | Demo preseed creates Alert/User/Asset fixtures, AE events, invokes simulate-failure/freeze/checkpoint/rollback | Fixtures and learning checkpoints in graph | These demo steps do not constitute a stream of verified Decision outcomes. Live outcome route writes graph evidence but does not update the monitor history (F02) |

SDK preseed details: `SDK/scripts/preseed_all_copilots.py:24–27,552–606` builds factors, scores, then submits confirmed/overridden actual actions to `/api/learn`. Its success counter increments after an HTTP-success learn response without checking for the scorer's paused status (`:598–605`). Do not equate the script's successes with verified-count growth when conservation is blocking. The script documents server-side `COPILOT_PRESEED_MODE=true`; scorer `:2199–2201` intentionally bypasses conservation in that mode. No running process's preseed-mode setting was inferred or changed in this audit.

SOC durability: `services/gae_state.py:158–217` serializes/restores W, decision_count, and history in an AGE posterior. Initialization loads that posterior and creates the scorer using the same configured AGE store (`:257–373`); bootstrap can set decision_count directly (`:341`) without filling verified history. `LearningHealthMonitor._persist_l5_conservation_state()` (`:640–707`) writes aggregate status/alpha/q/V, not a replacement verified stream. Consequently, persistence exists, but freshness and agreement between sources do not follow automatically.

SOC demo fixture runner: `scripts/preseed_demo_scenarios.py:198–219,284–350`. Its “verified” strings describe fixture checks, not analyst-verified outcomes. No seed/restart was executed during this sweep.

## Test Coverage Matrix (3-layer gate tests)

| Test surface | Test functions | Coverage read | Missing safety evidence |
|---|---:|---|---|
| SDK `tests/test_composite_gate.py` | 12 | Clean, abrupt failure, <20 outcomes, .85/.90 comparison, recovery, each layer, combined flags, HTTP keys | No real app/proxy→learn integration; G-REL receives a hand-supplied independent baseline; route fixture injects outcomes unlike S2P's provider |
| SOC `backend/tests/test_soc_grate.py` | 8 | Clean, abrupt failure, insufficient window, multiplier, layers, recovery, returned keys | Supplies synthetic history; evaluate test substitutes coverage components; no real outcome→history→pause assertion |
| S2P `backend/tests/test_s2p_conservation_coverage.py` | 8 | Coverage fields/clamping, count-based status agreement, COLD_START/BOOTSTRAP accepted by pause helper | No populated G-RATE window; “public” comparison calls the payload helper, not full decorated route |
| SDK `tests/scoring/test_conservation.py` | Reviewed relevant pause case | Verifies paused learn leaves verified count unchanged | Does not prove autonomous recovery or three-layer enforcement |
| SOC `backend/tests/test_soc_conservation_provider.py` | 7 | GREEN/AMBER/RED/CALIBRATING/UNKNOWN normalization and staleness | Does not produce a gate state from newly verified outcomes |
| A1-R2 harness/results | Experiment, not production tests | Seeded simulated threats and multiplier sensitivity | Different baseline/window readiness/floor policies; cannot certify deployed FPR |

Executed, with bytecode/cache writes disabled:

```text
SDK: python -B -m pytest tests/test_composite_gate.py -q -p no:cacheprovider --timeout=60
12 passed, 24 warnings in 1.03s

SOC: python -B -m pytest backend/tests/test_soc_grate.py -q -p no:cacheprovider --timeout=60
8 passed, 16 warnings in 5.21s
```

Warnings were pytest/freezegun distutils deprecations. No full backend suite, browser demo suite, or live threat injection was run. Tests whose counts are listed above but not included in these commands were inspected, not reported as passing.

Requested behavior coverage:

- Cold start: helper tests can fire ABS, but production SDK deliberately bypasses it before10 verified; SOC tests do not establish equivalent policy.
- Sustained drift: SDK direct helper test covers an explicitly passed baseline, not runtime baseline acquisition. S2P cannot run sequence checks from its provider.
- Sudden drop: focused tests inject 20 consecutive failures after healthy outcomes, **not** the advertised 15pp shift distribution.
- False-positive rate 0.87%: a simulated sensitivity result, not a production regression test or cross-copilot measurement.
- Three layers combined: direct helper flag coverage exists; end-to-end prevention and recovery are not established.

## Cross-Copilot Consistency

### Mounts are present

| App | Source mount | Status implementation |
|---|---|---|
| Trading | `SDK/apps/trading/backend/app/main.py:557–564` | Shared route, TradingRegimeScorerProxy |
| Purchasing | `SDK/apps/purchasing/backend/app/main.py:824–831` | Shared route, FreshScorerProxy |
| DataOps | `SDK/apps/dataops/backend/app/main.py:844–850` | Shared route, FreshScorerProxy |
| S2P | `S2P/backend/app/main.py:359–364` | Shared route, counts-returning lambda |
| SOC | `SOC/backend/app/main.py:170,195` | Framework health route + compatibility alias `routers/compat_router.py:83–89` |

Thus the current failures are not an absent `/api/conservation/status` mount. SOC's response is also not the SDK schema: core counts/q/alpha are under `components`, with `conservation`, `auto_pause_active`, and provider fields. Consumers must not assume top-level `verified_count` exists on the current SOC alias.

### Providers and enforcement are distinct

SDK `ScorerBackedProvider.get_state()` (`evolution/conservation_contract.py:90–112`) calls a scorer/proxy getter and normalizes its result. FreshScorerProxy's getter (`backend/scorer_proxy.py:134–138`) calls `_evolution_conservation_state()`, which uses the absolute floor, not the status route's CompositeGate. S2P installs ScorerBackedProvider separately from its count-only HTTP provider (`backend/app/main.py:258,359–364`).

SOC `SOCConservationProvider` (`services/evolver.py:216–292`) wraps an async-derived snapshot in CachedAsyncProvider, invalidates on fresh health, and returns UNKNOWN on stale/error refresh. This is a useful fail-closed mechanism; it does not repair missing history inputs. SOC's AMBER can reach `set_conservation_status()` and `guarded_update()`, so **do not** infer that the router's RED-only branch alone means AMBER is ignored: `GAE/gae/profile_scorer.py:703–734` pauses on AMBER/RED when configured, and SOC `services/gae_state.py:1023–1029` checks `is_paused`.

## Ranked Findings (P1 → P3)

### F01 — P1: Three-layer SDK reporting is disconnected from learning and promotion enforcement

**A — LOCATE.** `CompositeGate.evaluate(...)`, `SDK/copilot_sdk/scoring/composite_gate.py:29`; `CompoundingScorer._conservation_pause(self)`, `scoring/scorer.py:2198`; `_evolution_conservation_state(self)`, `:2606`.

**B — READ.** Full evaluate29–73, full pause2198–2300, full promotion state2606–2649, full learn967–1228, full public getter736–819, and proxy getter134–138. Search of production SDK call sites finds CompositeGate used in `backend/conservation_router.py`, not scorer learning/promotion.

**C — TRACE.** Consider 400 verified decisions spanning all categories, 380 correct then20 incorrect, no preseed bypass or regime throttle. At scorer2244 q=.95;2245–2254 the last100 accuracy is .80, which does not cross .75. At2270–2282 the dispersion adjustment cannot reduce this large signal to the approximately .0588 floor; no ABS pause follows. At2300 the function returns None. Learn1008–1009 therefore proceeds. The adapter, fed the same ordered outcomes, calculates short_accuracy=0, long_baseline=.95, threshold=.8075 and rate_active=true (ISOLATED result). Promotion state2639–2649 similarly reports GREEN from the absolute product alone.

The production `_recent_quality` and `_conservation_dispersion` helpers were also executed in isolation on those400 correctness records: recent=(100,.8), inflation=3.9906565, effective_se=.04354163, effective_signal=362.5833471 versus theta=.058825. No scorer/store was constructed or mutated for this check.

**D — VERDICT.** A stream that trips G-RATE can still be permitted by the actual SDK learning gate and advertised safe to promotion. Decisive line: `return None` (scorer2300). Existing last100/dispersion protection is real but is not the requested .85× last20 detector.

**E — CLASSIFY.** P1 safety-enforcement bypass relative to the claimed three-layer contract. Applies to the common scorer used by Trading/Purchasing/DataOps/S2P; not a claim that all existing conservation protection is absent. SOURCE TRACE plus isolated adapter result; no live bad outcomes injected.

### F02 — P1: SOC verified outcomes do not advance the history consumed by G-REL/G-RATE

**A — LOCATE.** `LearningHealthMonitor._gate_layers(history, conservation_passed, signal, theta_min)`, `SOC/backend/app/services/learning_health.py:80`; `report_decision_outcome(...)`, `routers/triage.py:1884`; `SOCCompoundingScorerAdapter.update(...)`, `domains/soc/scorer_adapter.py:68`.

**B — READ.** Full layers80–142 and evaluate288–469; full outcome route1884–2954 in chunks1884–2173,2174–2470,2471–2585,2586–2618,2619–2954; full adapter1–128; state serialization/restoration158–217 and guarded_update984–1039.

**C — TRACE.** Start with history=[] and a LearningState counter already>=300. A valid scorable outcome uses the raw profile update through adapter86–93, persists Decision/Outcome and centroid evidence, then triage2608–2611 increments only `_ref_ls.decision_count` and saves it. Neither that route nor adapter appends a WeightUpdate to LearningState.history. The routing-action branch2198–2203 also increments only the counter. On subsequent evaluate315–317 the old history is unchanged; layers93–96 yields outcomes=[]; at114/118 both relative/rate checks remain false. With a nonempty historical history, the same path leaves the detector looking at old outcomes instead of the new loss sequence.

**D — VERDICT.** Live correctness can deteriorate without updating the detector's input window. Exact counter-only update: `_ref_ls.decision_count += 1` (triage2610). Serializing the unchanged history at gae_state181 preserves the gap across restart.

**E — CLASSIFY.** P1 missing safety-input wiring. The source path is confirmed; current live history length could not be read through the failing health endpoint. It is not inferred from the displayed 4862 count.

### F03 — P1: SOC conservation dependency failure escapes as an unstructured HTTP 500

**A — LOCATE.** `_query_soc_verified_conservation_stats(graph_service=None)`, `SOC/backend/app/services/learning_health.py:570`; `learning_health()`, `routers/framework_router.py:724`; compatibility alias `routers/compat_router.py:84`.

**B — READ.** Full query570–621, component conversion206–256, evaluate288–469, route724–760, and alias84–89. Compared SDK route45–76's explicit 503 conversion.

**C — TRACE.** LIVE AGE query raises psycopg.OperationalError. At health595–597 catch converts it to RuntimeError, not a status object. At evaluate320 it escapes; framework750 has no local conversion; compat89 simply awaits that route. Both public paths return500. SOC log confirms the same call chain and exception.

**D — VERDICT.** Operators lose the gate status during its dependency outage instead of receiving a structured unavailable state. Exact failing line: `raise RuntimeError("AGE query failed for SOC conservation stats") from exc`.

**E — CLASSIFY.** P1 by the audit's uncaught-production-exception rule. No claim that learning proceeds: the outcome route catches monitor errors and blocks learning at triage2281–2283.

### F04 — P2: SDK G-REL defaults to a mathematically non-firing self-baseline

**A — LOCATE.** `_baseline_q(state, current_q)`, `SDK/copilot_sdk/backend/conservation_utils.py:147`; status builder61; `CompositeGate.evaluate`, scoring/composite_gate.py29.

**B — READ.** Full baseline147–165, builder61–144, gate29–73, proxy implementation, and all three relevant mount blocks.

**C — TRACE.** Counts yield q=correct/verified at utilities95. The standard proxies and S2P count mapping supply no independent baseline_q/baseline. Lines152–164 find no valid candidate,165 returns current_q. Router65–66 passes q and that same q; gate45–46 evaluates q < .7*q. For q>=0 this is false. ISOLATED checks at q=1,.7,.2,0 all returned false. LIVE S2P baseline=q=.8826530612 corroborates the fallback.

**D — VERDICT.** The displayed relative layer is inert without a separate baseline source; lifetime q is not rolling400 accuracy either. Exact fallback: `return float(max(0.0, min(1.0, current_q)))`.

**E — CLASSIFY.** P2 incorrect gate telemetry/configuration; the separate production enforcement defect is counted once in F01.

### F05 — P2: S2P status cannot populate its G-RATE window

**A — LOCATE.** `_read_conservation_counts(...)`, `S2P/backend/app/routers/s2p.py:1005`; `cached_conservation_state_provider(app_state)`,1065; `outcomes_from_state(state)`, SDK scoring/composite_gate.py76.

**B — READ.** Full S2P count/cache/provider1005–1070; full extractor76–100; S2P mount359–364.

**C — TRACE.** S2P provider returns count/coverage/penalty fields only at1024–1031. Extractor79–83 finds none of verified_outcomes/recent_outcomes/outcomes;84 returns[]. Gate48 requires at least20 entries and cannot fire. LIVE verified_count196 with short_window_count0/short_accuracy=null exactly matches this trace.

**D — VERDICT.** The response advertises parameters for a layer that lacks a stream. Exact missing-stream branch: `return []` (extractor84); the later gate requires `len(short_values) >= self.w_short`.

**E — CLASSIFY.** P2 S2P provider/status wiring gap; not an ordinary <20-decision cold start.

### F06 — P2: SOC conservation and verified-count surfaces use incompatible populations

**A — LOCATE.** SOC `_query_soc_verified_conservation_stats`, learning_health.py570; `AGEClient.count_verified_decisions(self)`, `CI/ci_platform/graph/age_client.py:747`; `_write_outcome_impl(...)`, age_graph_store.py1111.

**B — READ.** Full health query570–621, AGEClient counter747–760, graph-store writer1076–1217, snapshot.from_graph60–99, learning-state route1017–1094, and SDK learn967–1228.

**C — TRACE.** Shared SDK learn1113–1119 supplies correctness and metadata.verified_at, not verified_at_epoch. Writer1135 creates a timestamp for Outcome;1148 leaves optional Decision.verified_at_epoch=None and1157–1159 skips it. Decision.status becomes confirmed/overridden and counts in AGEClient751–755. SOC health586 rejects it because d.verified_at_epoch is null;588 also rejects noncanonical/missing categories. With only such rows, health599–621 returns zeros, evaluate324–325 selects1e9, and the steady branch422–427 returnsRED. The current display can independently keep a snapshot count after graph failures.

**D — VERDICT.** Durable verified evidence can be included in the user-visible count yet excluded from safety coverage. Exact exclusion: `AND d.verified_at_epoch IS NOT NULL`. Health also accepts any nonnull status/outcome rather than the canonical verified-status set, a converse population inconsistency.

**E — CLASSIFY.** P2 state-contract mismatch, relevant to historical RED. The arithmetic and exclusion path are confirmed; the exact historical row distribution is unverified during today's outage.

### F07 — P2: Layer overrides leave contradictory status, passed, and reason fields

**A — LOCATE.** Shared route `status(request)`, `SDK/copilot_sdk/backend/conservation_router.py:45`; gate.evaluate29.

**B — READ.** Full route45–76, builder61–144, check_payload303–311, and gate29–73.

**C — TRACE.** ISOLATED disposable route input:400 verified,380 correct, full category coverage, outcomes380 true then20 false. Builder generates statusGREEN/passedtrue and a GREEN reason. CompositeGate returnsAMBER with g_rate.active=true. Router70 overlays only returned layer fields; it does not regenerate passed or reason. Actual response: statusAMBER, passedtrue, reason containing `Status is GREEN`. Gate50 also changes a baseRED toAMBER whenever any layer is active, rather than preserving severity.

**D — VERDICT.** Different consumers can draw different safety conclusions from the same payload. Exact merge: `payload.update(layer_status)`.

**E — CLASSIFY.** P2 response/state inconsistency. If passed is meant to describe ABS only, it needs an explicit scoped name plus a separate composite result; currently it is top-level.

### F08 — P2: SOC calibration returns before applying active G-REL/G-RATE to status

**A — LOCATE.** `LearningHealthMonitor.evaluate(graph_service=None)`, `SOC/backend/app/services/learning_health.py:288`.

**B — READ.** Full evaluate288–469 and layers80–142; effective-status helper triage335–360; GAE set_conservation_status712–734.

**C — TRACE.** Use decision_count100, full coverage,80 correct then20 incorrect history. At333 gate_layers includes a rate breach (short0 against baseline.8). ABS passes at this volume. At374 the <300 condition is true and384–415 returnsCALIBRATING with auto_pause_active=false and the active layer details. The conversion toAMBER at429–432 is never reached. Triage's effective-status helper sees no nestedRED/failedABS and returnsCALIBRATING, not the active rate warning.

**D — VERDICT.** Having the required20 observations is insufficient to enforce SOC G-RATE during its calibration interval. Exact early returned value: `"status":            "CALIBRATING",`.

**E — CLASSIFY.** P2 lifecycle inconsistency with the requested evaluate-at20 behavior; independent of the absent-history issue. Source-derived counterexample, not a live injected stream.

### F09 — P2: SDK pause prevents verified outcomes from advancing the recovery window

**A — LOCATE.** `CompoundingScorer.learn(...)`, `SDK/copilot_sdk/scoring/scorer.py:967`.

**B — READ.** Full learn967–1228 and pause2198–2300; existing regression `tests/scoring/test_conservation.py:test_conservation_snapshot_written_when_paused`.

**C — TRACE.** When recent100 quality is below.75, pause returns a dict at2255–2268. Learn1008–1009 enters the pause branch, persists optional snapshots, and returns at1074. The actual write_outcome1113 is unreachable, as is verified-cache invalidation1120. Submitting correct feedback through the same path leaves the verified window unchanged, so the next attempt meets the same pause condition. Existing test explicitly asserts count remains10 in its ABS-pause example.

**D — VERDICT.** Pausing learning also rejects the verified evidence needed to demonstrate recovery. Exact terminal line: `return conservation_pause`. Recovery requires another approved evidence path or operator action; helper recovery tests do not exercise this lifecycle.

**E — CLASSIFY.** P2 operational deadlock risk, not a claim of irrecoverability through every other API. SOC's separate outcome route does persist evidence when learning is blocked, so behavior differs across copilots.

### F10 — P2: Experiment numbers and focused tests do not validate the production gate policy

**A — LOCATE.** `rate_pause(values, threshold)`, `SDK/experiments/vld/harnesses/safety_layer_characterization_r2.py:45`; `relative_pause`,37; `trace`,53; production gate.evaluate29 and SOC layers80.

**B — READ.** Full experiment functions37–83, production calculations29–73/80–142, both executed test files in full, and saved safety_layer_narrative.md.

**C — TRACE.** Experiment rate46 waits for400 decisions; production gate48 activates at20. Experiment relative38 waits for800 then compares adjacent400 windows; SDK defaults baseline to current lifetime q, SOC fixes it to the first400. Experiment trace63–64 uses alpha=min(1,V/10) and a fixed supplied floor; production uses actual category coverage and23.53/(alpha*V), plus bootstrap/calibration branches. SDK sudden-drop test supplies380 true+20 false, not a15pp step; SOC tests provide prebuilt history rather than submitting verified outcomes.

**D — VERDICT.** Passing these tests and citing .87% simulated false pauses does not establish the advertised production detection/FPR across five apps. Exact experiment readiness guard: `if len(values) < LONG_WINDOW:`.

**E — CLASSIFY.** P2 critical integration/validation gap. Preserve the experiment as simulation evidence; add production-policy-matched tests before asserting deployment equivalence.

### F11 — P3: SOC AMBER interpretation still attributes G-RATE/G-REL breaches to sigma logic

**A — LOCATE.** `LearningHealthMonitor._interpret(status, signal, theta_min, red_days)`, `SOC/backend/app/services/learning_health.py:509`.

**B — READ.** Full interpretation509–527, `_build_calibration_baseline`269–281, evaluate288–469.

**C — TRACE.** The calibration baseline helper returns(0,0). A rate breach with ABS passing sets statusAMBER at429–432. Interpretation513–517 unconditionally describes baseline minus AMBER_SIGMA rather than the short-window threshold that actually fired.

**D — VERDICT.** Correct numeric layer flags are paired with misleading explanatory text. Exact text prefix: `f"Signal degraded below baseline-{LearningHealthMonitor.AMBER_SIGMA}sigma "`.

**E — CLASSIFY.** P3 stale diagnostic wording; not an additional enforcement defect.

## Recommended Fix Priority

1. **F03:** restore the graph-query dependency and return an explicit unavailable/fail-closed health contract. Do not relabel the failed query GREEN or substitute a stale count without provenance. Re-run the historical population comparison once graph reads work.
2. **F01/F02:** make one authoritative verified stream and gate decision reach learning and promotion. For SOC, connect outcome ingestion to the history/window used by the detector. For SDK/S2P, do not rely on visiting a GET status route to enforce safety.
3. **F04/F05/F06/F08/F09:** define baseline ownership, window ordering/readiness, verified schema, bootstrap policy, and evidence acceptance while learning is paused. Supply S2P's ordered outcomes and reconcile SOC's timestamp/category predicates before interpreting counts.
4. **F07/F11:** return consistent composite status/pass/reason alongside per-layer detail; preserve more severe base states and explain the layer that fired.
5. **F10:** add end-to-end tests for a verified clean stream,20-decision drop, sustained drift, pause-with-outcome-ingestion, recovery, and restart. Measure production-equivalent FPR/detection without changing thresholds to satisfy expected results.

## Verification Boundaries and Frozen Files

Frozen SHA-256 prefixes checked during review: investigation.py `3441dcbd`; investigation_router.py `08f4df7a`; scorer.py `24ac9e49`. No frozen file was edited.

This audit analyzed five copilots and all three layer definitions, but **did not verify three-layer production enforcement**. Four conservation endpoints were unavailable during live checks, and the original SOC RED response could not be reproduced as a successful current status response. These are reported limits, not passing checks.

Safety gate sweep complete. Copilots analyzed: 5. Gate layers inspected: 3. P1: 3 | P2: 7 | P3: 1. SOC historical RED immediate cause: zero qualifying coverage/count selects the1e9 sentinel and fails ABS; exact historical zero-population cause remains unconfirmed. Current SOC failure: uncaught AGE connection failure. **0 source/existing files modified; 1 report created.**
