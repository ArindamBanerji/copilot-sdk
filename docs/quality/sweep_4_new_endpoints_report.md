# Sweep 4 — New Endpoint Contract Verification

Date: 2026-09-18. Reviewer: GPT-6. Repositories: copilot-sdk, s2p-copilot, gen-ai-roi-demo-v4-v50; ci-platform inspected where SOC request data reaches the database.

## Summary (top 5 findings)

1. **P1 — Query injection through SOC cross-correlate.** A read-only UNION payload in an alert ID returned a real alert whose ID did not equal the requested ID. The apparent parameter API interpolates values using incomplete escaping. Entry: `gen-ai-roi-demo-v4-v50/backend/app/routers/discoveries_router.py:196`; sink: `ci-platform/ci_platform/graph/age_client.py:360` and `:462` (F01).
2. **P1 — Concurrent signal publishes overwrite records.** Two executions of the real publish handler both returned `sig-001`, while the store retained only one record (F02).
3. **P1 — Signal storage grows without a bound.** No expiry, capacity limit, deletion, or pagination; every publication retains its text indefinitely and every list call materializes all records (F03).
4. **P1 — Adaptive budget telemetry grows without a bound.** Every post-cold-start allocation appends a dictionary; every stats read traverses the lifetime history. An isolated 1,000-allocation probe retained all 1,000 records (F04).
5. **P2 — S2P adaptive investigation cannot execute its count callback.** A valid request omitting an explicit budget returned 503: `_s2p_verified_count() takes 0 positional arguments but 1 was given`. GET budget telemetry still returns 200, concealing the broken integration (F05).

**Totals: 4 P1, 12 P2, 1 P3 = 17 findings.** Priority follows bug_hunt_v5's definitions: unbounded production collections and silent concurrent overwrite are P1; the caught S2P exception is P2 because it returns a controlled 503. The method's five-P1 stop condition was not reached.

Scope: **21 primary method/path contracts across 11 router modules**, plus AdaptiveBudgetPolicy and five auxiliary GET contracts requested in the prompt: **26 endpoint contracts examined in total**. A parameterized concepts path counts once, despite probing all three IDs. Both reconvergence spellings count because both are registered routes. Repeated mounts do not inflate endpoint counts. Other existing discovery endpoints in the same SOC file were read as context, not counted as new endpoints.

Evidence: full primary router/policy bodies, downstream functions named in findings, mounts, dedicated tests, live GETs and malformed/read-only POSTs, and isolated in-memory probes of the real signal handlers and budget policy. **32 existing focused SDK tests passed**. The broader app suites were not rerun. No source, fixture, preseed, or session-state file was edited; this report is the sole deliverable.

### Evidence conventions

- Paths below are relative to `claude_projects/`; `SDK/`, `S2P/`, `SOC/`, and `CI/` abbreviate `copilot-sdk/`, `s2p-copilot/`, `gen-ai-roi-demo-v4-v50/`, and `ci-platform/`.
- LIVE = observed on the running service; ISOLATED = executed against the actual handler/helper in a disposable process; SOURCE = traced without mutating deployed state.
- HTTP 200 is transport success, not proof of a correct metric or a completed catalog story.
- OpenAPI retrieval encountered body-read timeouts, including on S2P; mount conclusions use source and direct endpoint responses rather than an assumed complete live OpenAPI inventory.
- Frozen SDK hashes checked: investigation `3441dcbd`, investigation_router `08f4df7a`, scorer `24ac9e49`.

## Request Validation Table

| Endpoint | Method | Pydantic model? | Required fields validated? | Bad input handling / evidence |
|---|---|---|---|---|
| `/api/platform/concepts/{concept_id}` | GET | Typed path string | Path segment required | LIVE unknown ID and omitted ID both 404; dictionary lookup at `SDK/copilot_sdk/backend/concepts_router.py:60–63` |
| `/api/self/investigation-budget` | GET | No body; typed return dictionary | N/A | Read-only `policy.get_stats()` at `SDK/copilot_sdk/backend/budget_router.py:15–16`; policy constructor checks budget order and negative lambda, not finite values/types |
| `/api/platform/cross-signals` | POST | CrossCopilotSignal | Five required fields; confidence in [0,1] | LIVE missing fields, wrong types, confidence=2 => 422. ISOLATED empty identifiers and malformed timestamp accepted => 201 (F16) |
| `/api/platform/cross-signals` | GET | Optional typed query | No required query | `target_copilot` filters exact string plus broadcasts; no enum validation (`cross_signal_router.py:46–52`) |
| `/api/platform/cross-signals/{signal_id}` | GET | Typed path string | Path segment required | LIVE missing record => 404 `Signal not found`, `cross_signal_router.py:60–67` |
| `/api/metrics/switching-cost` | GET | No request body | N/A | Source timestamps accept ISO/datetime only; numeric graph dates silently ignored (F10) |
| `/api/platform/domain-applicability` | GET | No request body | N/A | Scorer capability mismatch silently produces zeros, not an unavailable response (F07) |
| `/api/dataops/trust/perturb` | POST | TrustPerturbRequest | source_id min length 1; type enum; magnitude .05–.30; decisions 1–50 | LIVE missing/wrong fields => 422, unknown source => 400 before overlay mutation |
| `/api/dataops/trust/reset` | POST | TrustResetRequest | source_id min length 1 | LIVE missing => 422; path-like unknown source => 400; no path access |
| `/api/trading/entrant-comparison` | GET | No request body | N/A | Reads FingerprintResult; absent attribute defaults silently to zero (F09, F15) |
| `/api/trading/regime-analytics` | GET | No request body; Request injection | N/A | Reads domain-scoped decisions; database failures have no route-local error conversion |
| `/api/trading/regime-analytics/summary` | GET | Same | N/A | Separate cached key, same calculation as full analytics |
| `/api/trading/regime/mirror` | GET | No request body | N/A | Reads regime analytics and current-regime helper |
| `/api/trading/regime/abstention` | GET | No request body | N/A | Contradictory total-decision versus verified-decision checks (F14) |
| `/api/trading/regime/throttle` | GET | No request body | N/A | Reads RegimeMonitor status; unknown regime explicitly surfaced |
| `/api/trading/regime/rejection` | GET | No request body | N/A | Includes illustrative helper estimates and separate actual flagged-row counts |
| `/api/trading/regime/reconvergence` | GET | No request body | N/A | Reads monitor and historical analytics |
| `/api/trading/regime/reconvergenc` | GET | No request body | N/A | Registered spelling alias of the same handler; LIVE 200 |
| `/api/s2p/confidence/thresholds` | GET | No request body | N/A | Four configured bands, read-only |
| `/api/s2p/confidence/route` | POST | ConfidenceRouteRequest | amount >=0, confidence in [0,1], calibration enum | LIVE missing/wrong/range => 422; amount="Infinity" accepted and auto-approved (F11) |
| `/api/alert/cross-correlate` | POST | CrossCorrelateRequest | Exactly two string elements | LIVE missing/list item numeric =>422, simple unknown/path-like ID=>404; escaped quote/UNION bypasses exact-ID lookup (F01) |

The perturbation implementation is **not** `SDK/copilot_sdk/backend/trust_perturbation_router.py` (that file does not exist). It is `SDK/apps/dataops/backend/app/routers/trust_perturbation_router.py`. Both POST handlers, the service, source normalization, factor lookup, and conservation fallback were read in full (lines 23–156).

### Guard traces for validation that worked

- SOC: missing `alert_ids` is rejected by model line 17 before handler line 191; numeric members fail string validation. For `../../etc/passwd`, line 196 performs a graph lookup, line 197 sees no record, line 198 raises 404. No file is opened.
- Cross-signal: missing entity/confidence/detail fails model lines 19–21 before line 34 can allocate an ID. A supplied confidence=2 fails `le=1.0` at line 20. The provided incomplete script-tag payload therefore tests required-field enforcement, not XSS protection.
- Trust perturbation: magnitude=9 and decisions="bad" fail model lines 29–30. An unknown source reaches `_factor_for_source` line 135, raises ValueError before `_sources` access at line 61, and handler line 113 maps it to 400. Reset validates the same source mapping before `pop` at line 82.
- Threshold routing: missing fields fail lines 23–24. At amount=500, `_band_for` lines 43–45 excludes the first band's upper bound and chooses the .80 band. Confidence=.80 meets the inclusive comparison at line 75, yielding 200/auto_approve. This observed boundary is correct.
- Concepts: unknown ID gives `payload=None` at line 60; lines 61–62 raise 404. Success returns a deep copy at line 63, protecting static content from response-side mutation.

## Response Contract Table

| Endpoint family / method | Success shape | Empty shape | Error shape | Verdict |
|---|---|---|---|---|
| Concepts GET | concept_id, title, version, content object | No empty concept; unknown is 404 | `{detail:string}` | All three IDs LIVE 200; 4 clocks, 2 questions, 3 retraction entries |
| Budget GET | controller, decisions, safety_lambda; populated stats add 5 numeric fields | Only first 3 fields | No route-local conversion | LIVE S2P 200 with decisions=0; schema varies with history (F17); Trading 404 is an expected non-mount |
| Signals POST | signal_id, status, honesty_note (201) | Not applicable | 422 detail list | ID race F02; blank metadata F16 |
| Signals list GET | signals array, count, honesty_note | `signals:[],count:0` | No route-local conversion | LIVE Trading 3 signals versus Purchasing/DataOps 0; stores do not exchange data (F06) |
| Signal detail GET | Full record plus honesty_note | Unknown =>404 | `{detail:"Signal not found"}` | Lookup guard correct; persistence/concurrency problems affect records themselves |
| Switching-cost GET | decisions_accumulated, equivalent_calendar_days, labeled_stream_to_close_pct | Three zeros | Store exceptions propagate; not fault-injected live | LIVE Trading: 800, 0.0, 50.0; epoch incompatibility F10 |
| Applicability GET | domains[5], platform_summary, metric_tier | Five rows of zeros, not unavailable | Unsupported capabilities silently fall back | LIVE all verified counts/gains 0; wrong non-Trading tensor defaults (F07/F08) |
| Trust perturb POST | source_id, factor_name, trust_before/after, decisions_injected, simulated_verified_outcomes, simulation, learning_mode, conservation_status | No implicit unknown source creation | 400 ValueError, 422 model errors; conservation errors mapped to UNAVAILABLE | Explicit reversible demo overlay; `decisions` is descriptive simulation metadata, not injected real outcomes |
| Trust reset POST | source_id, trust_reset_to, simulation, learning_mode, conservation_status | Known source with no overlay reads current scorer baseline | 400/422 as above | Source-state reset, no database/file write in handler |
| Entrant GET | incumbent, entrant, gap | Fingerprint insufficient-data accuracy defaults 0 | No route-local conversion | LIVE .997 accuracy, 360 decisions, IKS 0, +49.7pp; gaps and IKS misleading under F09 |
| Regime analytics and summary GET | regimes dictionary, total_decisions, regime_count | Canonical regime entries with zero counts and null measurements | No route-local conversion | LIVE both 800 decisions; verified ranging 360, accuracy .997; nullable measurements explicit |
| Regime mirror GET | current_regime, regimes list, behavior_change, observation_only, evidence_tier, observation | Canonical zero-evidence rows | No route-local conversion | LIVE 200; current regime `choppy` versus analytics key `ranging` reflects separate normalizers, not a list-shape failure |
| Regime abstention GET | regime, decision_count, minimum_decisions, abstention_recommended, message, per_regime_day_zero, reasons, tier | Empty data recommends abstention | No route-local conversion | Mixed evidence rules demonstrated in F14 |
| Regime throttle GET | current/previous regime, break flag, authority levels, reconvergence timeline, tier | unknown/null, normal, 0 decisions | No route-local conversion | LIVE unknown regime, 0 decisions, remaining 20; correctly labeled T_S |
| Regime rejection GET | variants_tested/rejected, rejection reasons, per-regime actual counts, provenance, tier | Helper still emits 35 illustrative variants on empty rows | No route-local conversion | LIVE illustrative 133 variants, actual per-regime map empty. Do not interpret estimates as AE event history |
| Reconvergence GET, both spellings | monitor state, remaining, historical_regime_breaks, cold_start_curves, tier | Null current/previous, zero history counts | No route-local conversion | LIVE 200; historical_regime_breaks holds aggregates, not an event timeline |
| Thresholds GET | thresholds[4], k14_noise_rate, calibration_source, calibration_note | Static configuration, never empty | Framework errors | LIVE 4 bands and .92 noise annotation |
| Confidence route POST | invoice_amount, confidence, threshold_applied, routing, reason, calibration_source, noise_rate | Required body | 422 detail list | Nonfinite amount returns null with auto_approve (F11) |
| SOC cross-correlate POST | correlation, discovery_note; nested two alerts, detection, pattern, entities, severity, recommendation, confidence | No match => false/0, null pattern/severity/recommendation | 422 or 404; graph exceptions not caught locally | LIVE forward pair true/.91/critical; reverse false/0/null; provenance lost (F12/F13) |

### Five auxiliary response checks requested by the prompt

| Endpoint | Observed status / shape | Interpretation |
|---|---|---|
| S2P `/api/s2p/learning/frozen-twin` | 200; frozen_available=true, compared_decisions=0, delta_accuracy/current_accuracy/frozen_accuracy=null, visual_diff=[] | A pinned twin exists; no paired accuracy evidence is present |
| Purchasing `/api/purchasing/frozen-twin` | 200; available=false, status=NOT_INITIALIZED, evidence_tier=T_S | Explicit empty state, not a demonstrated two-store curve |
| DataOps `/api/self/rule-genealogy` | 200; domain=dataops, rules=[], total=0 | Valid empty contract; no promoted/demoted-rule evidence |
| DataOps `/api/di/acquisition-advice` | 200; recommendations array | Recommendations include catalog-derived cost/value estimates; successful response alone does not validate their empirical basis |
| SOC `/api/soc/checkpoint/list` | 200; checkpoints array with id/timestamp/reason/decision_count | Listing works; no create/rollback mutation performed in this review |

These five were response probes, not full re-audits of old implementations. SOC's existing `/api/platform/cross-signals` also responded 200 but uses `total/active/acknowledged/source_domains` and `source_domain/target_domain`, unlike the new SDK contract. It is a separate implementation, not an SDK mount.

## Mount Consistency Matrix

Y = explicit source mount; — = outside intended app scope. Live observations are noted separately.

| Router | Trading | Purchasing | DataOps | S2P | SOC | Should mount? |
|---|---|---|---|---|---|---|
| concepts | Y | Y | Y | — | — | Three SDK apps per Batch2; SOC machine spec intentionally uses Trading |
| cross_signal (SDK) | Y | Y | Y | — | Separate router | Three SDK apps mounted, but this does not implement cross-process transfer |
| switching_cost (SDK) | Y | Y | Y | — | Separate existing implementation | Three SDK apps per B1 |
| platform applicability | Y | Y | Y | — | — | Three SDK apps per B2 |
| budget | — | — | — | Y | — | S2P-only rollout; Trading 404 is not a missing required mount |
| trust perturbation/reset | — | — | Y | — | — | DataOps only, under `/api/dataops` |
| entrant comparison | Y | — | — | — | — | Trading only |
| regime analytics and summary | Y | — | — | — | — | Trading only |
| regime beats (6 paths) | Y | — | — | — | — | Trading only |
| s2p_thresholds (GET and POST) | — | — | — | Y | — | S2P only |
| discoveries/cross-correlate | — | — | — | — | Y | SOC only, prefix `/api` |

Source evidence:

- `SDK/apps/trading/backend/app/main.py:565–575`: switching/platform use external `/api` prefix; cross-signal uses `/api`; concepts and entrant carry their own absolute prefixes. Regime routers at `:667–675` carry `/api/trading` internally.
- `SDK/apps/purchasing/backend/app/main.py:832–841`: switching/platform/cross-signals/concepts mounted with the same prefix conventions.
- `SDK/apps/dataops/backend/app/main.py:851–867`: perturbation mounted with `/api/dataops`, then switching/platform/cross-signals/concepts.
- `S2P/backend/app/main.py:381–393`: investigation classifier and budget policy router; `:432`: confidence thresholds router.
- `SOC/backend/app/main.py:187`: discoveries_router mounted with `/api`, making the declaration at `discoveries_router.py:190` reachable as `/api/alert/cross-correlate`.
- `SDK/apps/s2p` supplies a frontend; its external backend is `s2p-copilot`, not a fourth SDK app/main.py to assume exists.

## Test Coverage Table

Counts are named `test_*` function definitions in each dedicated file, not parametrized case counts and not a claim that the whole file was rerun.

| Feature | Test file | Test count | Edge cases covered / gaps |
|---|---|---:|---|
| Concepts | `SDK/tests/test_concepts_router.py` | 4 | Three IDs and unknown 404; no mutation-isolation/content-source checks |
| Budget policy | `SDK/tests/test_budget_policy.py` | 9 | Cold start, easy/medium/hard, empty/populated stats, invalid budget ordering; no S2P classifier callback or retention test |
| Budget HTTP router | No dedicated router test file found | 0 | Isolated real-policy GET tested during this sweep; policy unit tests do not exercise app wiring |
| Cross-signals | `SDK/tests/test_cross_signal_router.py` | 6 | Publish/list/detail shape and honesty note; no concurrency, retention, cross-app delivery, target filtering, malformed payload, or missing-ID regression |
| Switching cost | `SDK/tests/test_switching_cost_router.py` | 8 | Empty, ISO dates, count, custom constant, no first date; no AGE epoch timestamp or production proxy/store path |
| Domain applicability | `SDK/tests/test_platform_router.py` | 5 | Five rows, Trading shape, tier, mean; fake scorer implements methods the production proxy lacks |
| Entrant comparison | `SDK/apps/trading/backend/tests/test_entrant_comparison.py` | 3 | Top-level keys and nonnegative gap; fake returns dict while handler reads attributes, silently making all incumbent values zero (F15) |
| Regime analytics | `SDK/apps/trading/backend/tests/test_regime_analytics.py` | 9 | Real-scorer isolation, grouping, verification, null/empty, conservation evidence, endpoint 200 |
| Regime beats | `SDK/apps/trading/backend/tests/test_regime_beats.py` | 12 | Shape/tier assertions; no unverified-only abstention contradiction, monitor error, or reconvergence alias test |
| Trust perturbation | `SDK/apps/dataops/backend/tests/test_trust_perturbation.py` | 6 | Degrade/improve/magnitude/reset/conservation shape; no invalid-source/range, concurrency, or scorer outage cases; fake scorer/store |
| S2P thresholds | `S2P/backend/tests/test_s2p_thresholds.py` | 6 | Low/high amount and confidence, GET/noise label; no nonfinite input, missing fields, 500/5000/50000 exact boundaries |
| SOC kill chain | `SOC/backend/tests/test_kill_chain.py` | 5 | Forward pair, duplicate pair, entities/severity, one-item 422; graph is mocked, so query interpolation/injection is completely bypassed |

**73 dedicated test functions found** across the 11 nonzero rows above. The following existing SDK files were run: concepts, cross_signal, budget_policy, switching_cost, platform_router. Command: `python -B -m pytest tests/test_concepts_router.py tests/test_cross_signal_router.py tests/test_budget_policy.py tests/test_switching_cost_router.py tests/test_platform_router.py -q -p no:cacheprovider --timeout=60`. Result: **32 passed, 64 warnings, 1.17s**. No new test files or source changes were made.

The earlier 56/56 demo result does not cover all catalog claims: current DO-04 accepts empty rules, DO-05 accepts identical actions, and MACH-03 includes alert_category in its signature. Those checks can pass without a demotion, K14 divergence, or a change in K-caused read order. They are not evidence against the findings here.

## Security Findings

- **Confirmed query injection, F01.** The malicious value is in a legitimate string field, survives model validation, reaches `get_alert()`, and changes the query structure. The live demonstration used only MATCH/RETURN/UNION with LIMIT 1. No mutation or destructive database query was attempted; no returned alert content is reproduced in this report.
- **No demonstrated script execution.** The supplied incomplete script-tag POST returned 422 for missing fields. A complete payload in an isolated signal router accepts the tag as text. The current banner renders `{signal.source_copilot}` and `{signal.detail}` as React text (`SDK/copilot_sdk/frontend/CrossCopilotSignalBanner.tsx:43–49`), not raw HTML. Accepting a string is not by itself proof of XSS.
- **Error detail leak reproduced.** The adaptive investigation 503 exposes the internal Python callback name and argument-count error (F05). No stack trace or filesystem path appeared in the tested 400/404/422 responses.
- **No shell/file-path sink found in the audited new POST handlers.** Trust source IDs pass through a fixed dictionary; cross-signals stay in memory; threshold routing performs arithmetic. SOC IDs reach AGE, where the escaping defect is confirmed.
- **Resource growth:** F03/F04. Large load tests were deliberately unnecessary: bounds are absent in the full bodies, and controlled isolated probes show retention. The deployed signal store was not polluted with successful audit publications.

## Ranked Findings (P1 → P2 → P3)

### F01 — P1: Cross-correlate exposes AGE query injection

**A — LOCATE.** `async def cross_correlate_alerts(request: CrossCorrelateRequest)` at `SOC/backend/app/routers/discoveries_router.py:191`; `async def get_alert(self, alert_id: str)` at `CI/ci_platform/graph/age_client.py:613`; `serialize_for_age` at `:342`, `_sync_execute` at `:447`.

**B — READ.** Full handler 191–225; helper 613–622; serializer 342–362; query executor 447–514 and SQL wrapper 418–425.

**C — TRACE.** Body has exactly two string IDs, so model line 17 accepts it. For the first ID use the Python literal `"\\'}) RETURN alert UNION MATCH (alert:Alert) RETURN alert LIMIT 1 //"`. Router line 196 calls get_alert. Client lines 615–618 construct a parameter-looking query and dictionary. Executor line 458 checks the query before substitution; line 462 replaces `$alert_id` with the serializer output. Serializer line 360 escapes a quote but not the preceding backslash. The resulting literal contains an escaped backslash followed by a terminating quote, allowing the UNION query. `_build_sql` then embeds the altered Cypher. LIVE result: HTTP 200; returned `alert_1.alert_id` differed from the attacker-supplied ID and was nonempty.

**D — VERDICT.** Exact-ID lookup is bypassed; the endpoint executes attacker-influenced query structure. Failing line: `escaped = value.replace("'", "\\'")`. The demonstrated effect is unauthorized query alteration/read, not an asserted destructive write.

**E — CLASSIFY.** P1, security bypass. Fix the shared serialization/execution boundary; Pydantic string validation at the new endpoint does not prevent it. A harmless unknown ID returning 404 is insufficient security evidence.

### F02 — P1: Concurrent publishes share an ID and lose a signal

**A — LOCATE.** `def publish_signal(signal: CrossCopilotSignal)` at `SDK/copilot_sdk/backend/cross_signal_router.py:33`.

**B — READ.** Complete factory and all handlers, lines 26–69.

**C — TRACE.** Start `signals={}`. A executes line 34: `signal_id='sig-001'`. Before A reaches line 38, B executes line 34 and gets the same value. Each writes its record at line 38; the last assignment replaces the first. Both line-39 responses say published. ISOLATED reproduction invoked the actual handler in two threads, with a trace barrier immediately after ID calculation; result was two published `sig-001` responses and list count=1.

**D — VERDICT.** Silent record loss under concurrent POSTs. Failing line: `signal_id = f"sig-{len(signals) + 1:03d}"`. FastAPI's synchronous handlers can run on concurrent worker threads; the GIL does not make this multi-line operation atomic.

**E — CLASSIFY.** P1, silent shared-state overwrite. Reproduction changed no deployed signal store.

### F03 — P1: Unbounded signal retention and full-list materialization

**A — LOCATE.** `create_cross_signal_router()` at `SDK/copilot_sdk/backend/cross_signal_router.py:26`; publish `:33`, list `:46`.

**B — READ.** Lines 16–69, including every route and model field.

**C — TRACE.** Line 30 creates lifetime storage. Each sequential valid POST adds a new dictionary at line 38. There is no TTL, delete route, cap, or trimming branch before return line 69. Text fields at lines 17–23 have no length limits. Every GET copies all values at line 47 before filtering; output grows with total publications, including old events.

**D — VERDICT.** Retained memory grows O(N × payload size); listing time and response size grow O(N). Exact retention line: `signals[signal_id] = record`. No production load saturation was attempted.

**E — CLASSIFY.** P1 under v5's explicit unbounded-production-collection rule. This is separate from F02's overwrite race.

### F04 — P1: Adaptive policy retains lifetime allocation history

**A — LOCATE.** `AdaptiveBudgetPolicy.allocate(...)` at `SDK/copilot_sdk/scoring/budget_policy.py:33`; `get_stats()` at `:54`.

**B — READ.** Full policy, lines 16–76; budget router 10–18; S2P mount 247–255 and 381–393.

**C — TRACE.** At verified_count=30, line 35's cold-start branch is false. Each call appends a dictionary at line 45. No subsequent branch removes entries. After 1,000 isolated calls, `_history` and stats decisions both equal 1,000. GET stats creates easy/hard lists at lines 63–64 and scans the entire history again at lines 70–72.

**D — VERDICT.** Allocation history and polling work grow without a bound. Exact line: `self._history.append(`. F05 currently blocks this path on the live S2P integration; fixing F05 exposes the already-reproduced policy retention problem.

**E — CLASSIFY.** P1 by v5's unbounded production collection criterion; not a claim that the current demo process is already out of memory.

### F05 — P2: S2P classifier binds the count callback as a method

**A — LOCATE.** `SituationClassifier.classify(...)` at `S2P/backend/app/main.py:59`; `_s2p_verified_count()` at `:250`; integration assignment `:255`.

**B — READ.** Full subclass 53–78, callback/assignments 247–255, investigation factory call 381–393, and SDK investigation handler 58–130.

**C — TRACE.** The class attribute receives a plain zero-argument function. Classify line 70 reads `self._verified_count_provider`, producing a bound method. Line 76 calls `provider()`, which supplies self to a function declared without parameters. A valid S2P eight-factor request without `budget` enters the classifier through `SDK/copilot_sdk/backend/investigation_router.py:74–78`. Its broad exception handler maps TypeError to HTTP 503. LIVE detail: `Investigation unavailable: _s2p_verified_count() takes 0 positional arguments but 1 was given`.

**D — VERDICT.** Automatic budget allocation is unavailable even though budget GET advertises an adaptive controller. Failing line: `verified_count=provider(),`. Explicit budget requests bypass the classifier and therefore fail to test this integration.

**E — CLASSIFY.** P2, caught but complete failure of the adaptive request path; includes internal-error-name leakage. Additionally, callback line 251 reads `decision_count` rather than the existing verified-count API, which requires correction/verification when wiring is fixed.

### F06 — P2: Cross-copilot signals never reach another mounted app

**A — LOCATE.** `create_cross_signal_router()` at `SDK/copilot_sdk/backend/cross_signal_router.py:26`; mounts Trading `main.py:573`, Purchasing `:840`, DataOps `:866`.

**B — READ.** Entire factory 26–69 and all three mount blocks.

**C — TRACE.** Each factory call creates a distinct `signals={}` at line 30. Publish writes only that closure. GET reads only its own closure at line 47. `target_copilot` filters local rows at line 51; it does not send data. LIVE Trading contains three pre-existing SOC-labeled PW signals; Purchasing and DataOps return empty lists. S2P has no SDK signal route; SOC has a different static/service contract.

**D — VERDICT.** A successful local publish/list test does not establish cross-copilot delivery. Exact isolation line: `signals: dict[str, dict[str, Any]] = {}`.

**E — CLASSIFY.** P2, missing functional delivery integration. In-memory demo storage is intentional, but isolated app stores cannot fulfill the advertised receiving-copilot flow.

### F07 — P2: Applicability silently reports zero for live scorer metrics

**A — LOCATE.** `_verified_decisions(scorer)` at `SDK/copilot_sdk/backend/platform_router.py:19`; `_compounding_gain_pp` at `:30`; `FreshScorerProxy.get_verified_count()` at `SDK/copilot_sdk/backend/scorer_proxy.py:126`.

**B — READ.** Platform router 19–77; complete FreshScorerProxy class 16–164; app mount blocks.

**C — TRACE.** All three mounts pass FreshScorerProxy. Count helper line 20 searches count_verified_decisions/count_verified/get_decision_count, none exposed by that proxy. Correct `get_verified_count` is never tried. It returns 0 at line 27. Gain helper similarly never calls proxy.trajectory and returns 0.0 at line 39. Handler lines 49–75 emits these as numbers, including in platform totals. LIVE Trading applicability: all five counts/gains zero; entrant and regime analytics report 360 verified decisions.

**D — VERDICT.** Unsupported access is indistinguishable from a real zero and persists despite preseed. Exact failing fallback: `return 0` at line 27.

**E — CLASSIFY.** P2, silent reporting error. Remote domains are also filled with zero without a collection/unavailable status.

### F08 — P2: Applicability invents non-Trading tensor dimensions

**A — LOCATE.** `domain_applicability()` at `SDK/copilot_sdk/backend/platform_router.py:48`, lines 57–58.

**B — READ.** Complete handler 48–75 and actual domain shape declarations.

**C — TRACE.** For every name other than trading, line 57 chooses `[5,4,8]`, line 58 chooses 160. Actual DataOps preset is `[6,5,6]=180` (`SDK/copilot_sdk/scoring/presets/dataops.py:30–35`); Purchasing is `[5,4,7]=140` (`.../purchasing.py:32–36`); S2P declares `[5,5,8]=200` (`S2P/backend/app/domains/s2p/config.py:4`, `:104–113`). LIVE response emits 160 for each of these domains.

**D — VERDICT.** At least three demonstrably wrong structural values. Failing line: `"tensor_size": 200 if name == "trading" else 160,`. EXPLORATORY labeling of depth metrics does not make the tensor topology correct.

**E — CLASSIFY.** P2, contract/data-definition error.

### F09 — P2: Entrant comparison clips losses and fabricates missing IKS

**A — LOCATE.** `entrant_comparison()` at `SDK/apps/trading/backend/app/routers/entrant_comparison.py:17`; FingerprintResult at `SDK/copilot_sdk/scoring/fingerprint.py:19`.

**B — READ.** Complete route 13–47; fingerprint dataclass and computation 19–83.

**C — TRACE.** A valid incumbent accuracy .40 and baseline .50 yields raw gap -10pp; line 22 clips it to 0.0, while the emitted accuracy fields still imply -10pp. Lines 28–31 look for iks/information_knowledge_score, neither of which exists in FingerprintResult; output is always 0.0 for that production type. LIVE incumbent has accuracy .997 and 360 decisions but IKS=0. No measured baseline is loaded; .50 is a configured assumption without a source label.

**D — VERDICT.** `gap.accuracy_pp` can contradict its inputs, and absent IKS is presented as a measured zero. Exact line: `gap = max(0.0, (accuracy - baseline) * 100.0)`.

**E — CLASSIFY.** P2, misleading comparison metrics. A default 50% baseline may be useful if explicitly identified as assumed; it is not evidence of a measured warm-start gain.

### F10 — P2: Switching-cost ignores AGE epoch timestamps

**A — LOCATE.** `_timestamp(value)` at `SDK/copilot_sdk/backend/switching_cost_router.py:11`; `_days_since_first` at `:50`.

**B — READ.** Entire switching router 11–100; AGE decision creation at `CI/ci_platform/graph/age_graph_store.py:960–985` and get_all_decisions 3093–3104.

**C — TRACE.** AGE writes numeric epoch seconds (`:962`, `:980`). `_timestamp` line 16 rejects numbers because they are neither datetime nor string. All dates become None; comprehension lines 51–57 produces `timestamps=[]`; line 59 returns 0.0. ISOLATED a September 1 epoch with September 18 clock yields 0.0 instead of 17 days. LIVE Trading returns 800 accumulated decisions and 0.0 equivalent days.

**D — VERDICT.** Standard production timestamp format is silently lost. Exact guard: `if not isinstance(value, str) or not value.strip():`.

**E — CLASSIFY.** P2, broken metric calculation. Tests cover ISO strings only, missing the actual store contract.

### F11 — P2: Infinite invoice amount is accepted and auto-approved

**A — LOCATE.** `ConfidenceRouteRequest` at `S2P/backend/app/routers/s2p_thresholds.py:22`; `route_confidence` at `:72`.

**B — READ.** Entire module, including model, four bands, band selection, and response construction.

**C — TRACE.** Submit JSON `{"invoice_amount":"Infinity","confidence":0.95}`. Pydantic coerces the string to positive infinity; line 23's ge=0 passes. At line 44 it qualifies for the final open-ended band. Line 75 evaluates .95 >= .90 as true. LIVE 200 response contains `invoice_amount:null`, `routing:"auto_approve"`, threshold .90, with no invalid-input error.

**D — VERDICT.** Unrepresentable monetary input receives an approval recommendation and violates the numeric amount response contract. Exact insufficient constraint: `invoice_amount: float = Field(ge=0.0)`.

**E — CLASSIFY.** P2, missing finite-number validation. This endpoint returns a recommendation; no actual invoice approval side effect was observed or claimed.

### F12 — P2: Kill-chain detection depends on request array order

**A — LOCATE.** `cross_correlate_alerts` at `SOC/backend/app/routers/discoveries_router.py:191`.

**B — READ.** Handler 191–225, pattern map 20–25, all category/entity helpers 28–61.

**C — TRACE.** Forward pair A,B resolves credential_access then lateral_movement; map lookup line 206 succeeds, shared entities is nonempty, line 207 detects. Reverse input B,A resolves lateral_movement then credential_access; no key exists, so detection is false although the same entities and same two timestamped alerts are present. LIVE forward=true/.91/critical, reverse=false/0/null. Neither sorting by alert timestamps nor a reverse-pattern lookup occurs.

**D — VERDICT.** Caller selection order suppresses an otherwise recognized chain. Exact line: `pattern = _KILL_CHAIN_PATTERNS.get((first_category, second_category))`.

**E — CLASSIFY.** P2, false negative. If ordered inputs are intentional, the API must specify and validate event order rather than silently treating array position as chronology.

### F13 — P2: Kill-chain output strips planted provenance and hardcodes confidence

**A — LOCATE.** `_correlation_alert` at `SOC/backend/app/routers/discoveries_router.py:55`; correlation response at `:209–225`.

**B — READ.** All output helpers and handler; `SOC/data/demo_fixtures/kill_chain_pair.json`; complete seed_alert/seed_kill_chain functions in `SOC/scripts/preseed_demo_scenarios.py:95–151`, `:204–217`.

**C — TRACE.** Seeded alerts carry sample=true, planted=true, origin=soc_demo_fixture (seed lines 125–129). `dict(alert)` retains these initially. Helper lines 56–61 select only ID/category/severity/action, dropping the tags. Line 216 emits confidence .91 for every matched category/entity pair without measuring it. LIVE response has .91 and the discovery claim but no sample/planted/source/tier field.

**D — VERDICT.** A planted heuristic demonstration becomes an unqualified confidence-bearing API result. Exact line: `"confidence": 0.91 if detected else 0.0,`.

**E — CLASSIFY.** P2, provenance/response-contract gap under repository Rules 63/67. The pair is planted; detection is real code execution, but .91 is a constant, not measured confidence.

### F14 — P2: Regime abstention uses incompatible evidence floors

**A — LOCATE.** `situational_abstention()` at `SDK/apps/trading/backend/app/routers/regime_beats.py:65`; `check_regime_data_sufficiency` at `SDK/apps/trading/backend/app/services/situation_analyzer.py:85`.

**B — READ.** Handler 65–88; sufficiency function 85–105; conditioned-stat function 34–65; tagging helpers 216–241 and verification helper.

**C — TRACE.** Ten rows all tagged trending with no outcomes produce count=10 at helper line 92. `count < min_decisions` at line 97 is false (minimum 10), so top-level abstention=false and message says scoring available. Conditioned stats report verified_count=0. Handler line 76 compares this with a fallback minimum 20, producing per-regime abstention=true. Lines 81–85 derive empty reasons and T_O from the opposite top-level result. ISOLATED helper probe confirms top-level false and zero verified rows.

**D — VERDICT.** One response can simultaneously recommend scoring and abstention for the same regime, and label unverified history as adequate evidence. Exact line: `"abstention_recommended": count < min_decisions,`.

**E — CLASSIFY.** P2, UI/reporting contradiction. This observation-only endpoint was not shown to change the production scorer's gate.

### F15 — P2: Entrant tests cannot detect broken production value extraction

**A — LOCATE.** `FakeScorer.fingerprint()` at `SDK/apps/trading/backend/tests/test_entrant_comparison.py:8`; production handler at `SDK/apps/trading/backend/app/routers/entrant_comparison.py:17`.

**B — READ.** Entire 36-line test file and complete route.

**C — TRACE.** Fake returns a dictionary with .75 accuracy/80 decisions/.42 IKS. Handler uses getattr, so all three supplied values are ignored; it emits 0/0/0. Test one checks only top-level keys, test two accepts nonnegative clipped gap, test three checks only entrant decisions=0. None asserts the fake's incumbent values survived. Platform tests have the complementary issue: their fake exposes methods absent from FreshScorerProxy, masking F07.

**D — VERDICT.** Happy-path tests give false confidence on the critical metrics path. Exact inadequate assertion: `assert body["gap"]["accuracy_pp"] >= 0`.

**E — CLASSIFY.** P2, critical integration coverage gap. Existing fake scorers also conflict with the repository's no-scorer-mock testing guidance. No tests were changed during this review.

### F16 — P2: Signals accept empty identity fields and invalid timestamps

**A — LOCATE.** `CrossCopilotSignal` at `SDK/copilot_sdk/backend/cross_signal_router.py:16`; publish at `:33`.

**B — READ.** Full model and publish/list/detail implementations.

**C — TRACE.** Required string presence passes even when signal_type/entity_id/detail are empty. timestamp="not-a-date" passes because line 22 types it as str. At line 37 its truthiness bypasses the generated timestamp fallback. ISOLATED complete payload, including a script-tag source name, returned 201 and persisted all those values unchanged.

**D — VERDICT.** Consumers cannot reliably identify, order, or age valid-looking published signals. Exact loose field: `timestamp: str | None = None`.

**E — CLASSIFY.** P2, missing semantic validation. This is not classified as XSS; current rendering treats these values as text. Unlimited length is counted separately under F03.

### F17 — P3: Budget telemetry fields disappear before the first warm allocation

**A — LOCATE.** `get_stats()` at `SDK/copilot_sdk/scoring/budget_policy.py:54`.

**B — READ.** Full policy 16–76 and HTTP router 10–18.

**C — TRACE.** Empty `_history` follows lines 56–61 and returns only controller/decisions/safety_lambda. After one .90-confidence allocation with verified_count=30, it follows lines 63–76 and adds mean_reads_easy, mean_reads_hard, total_reads_saved, easy_count, hard_count. Cold-start allocate returns before recording at line 36, so many actual allocations can still leave stats decisions=0. ISOLATED GETs reproduced both shapes; LIVE S2P currently has the minimal shape.

**D — VERDICT.** Empty-state clients need undocumented optional fields, and `decisions` actually means warm allocations recorded rather than all allocations. Exact branch: `if not self._history:`.

**E — CLASSIFY.** P3, inconsistent telemetry schema/meaning. Existing empty-state test intentionally expects the minimal shape, so this is a contract limitation, not an alleged regression against that test.

## Recommended Fix Priority

1. **F01:** repair the AGE query boundary first; add a real-database read-only regression for quote/backslash input, and verify safety checking applies to the actual executed query. The demonstrated endpoint bypass must be addressed before relying on these handlers with untrusted callers.
2. **F02/F03:** make signal identity/storage concurrency-safe and bounded; define expiry, list limits, and message ownership. Add concurrent-publish and missing/filter tests.
3. **F05/F04:** fix S2P callback binding and use verified-count semantics; exercise the real classifier with omitted budget. Replace lifetime allocation records with bounded history or sufficient aggregates before enabling sustained traffic.
4. **F07/F08/F09/F10:** correct production metric capabilities, domain shape sources, signed comparison semantics/IKS source, and epoch dates. These are currently plausible-looking 200 responses with wrong values.
5. **F06/F11/F12/F13/F14/F16:** define actual signal delivery; reject nonfinite amounts; make kill-chain order/provenance explicit; unify abstention evidence floors; validate signal identity and timestamps.
6. **F15/F17:** strengthen tests around actual production contracts and publish a stable budget telemetry schema.

No fixes were applied. No servers were started/stopped, no live seed scripts were executed, and no live signal publications or trust-overlay mutations were needed. Successful stateful signal probes ran in an isolated router instance. The security demonstration executed a read-only query. Existing source/fixture/session files modified: **0**. New files: **1**, this report.
