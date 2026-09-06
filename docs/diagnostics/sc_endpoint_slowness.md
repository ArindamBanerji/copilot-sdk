# Self-computation endpoint latency diagnosis

## Summary

Measured on Windows on 2026-09-05, using the requested Python 3.11 environment, the live AGE `soc_graph`, and **one uvicorn worker per backend**. The historical browser measurements of 4.4–7.5 seconds are not reproducible as intrinsic handler times in the current checkout. Before these fixes, direct HTTP calls to the six reported endpoints took **43.605–780.432ms**. A browser page trace recorded 63 completed API requests, paired initial waves, SC responses completing within 746ms, and two today-summary calls completing at 834ms and 1,579ms. Browser request queueing and external weather I/O contribute to the visible delay; a browser request duration must not be equated with Python handler execution time.

Three bounded fixes were implemented: coalesce overlapping verified-history reads, reuse external weather forecasts with bounded expiry, and remove trajectory's unused checkpoint read plus quadratic prefix scans. No learning-state cache was introduced. Database-side pagination/projection/aggregation and durable cross-worker read-cache invalidation need the larger designs below. Existing endpoint response schemas, limits, filtering, ordering and complete-population statistics remain unchanged. This report distinguishes the historical measurements, the current before/after measurements, and conclusions that remain unproven.

The requested `copilot_sdk/scoring/compounding.py` and `storage.py` paths do not exist. The active facade is `scoring/scorer.py`; the active backend in these measurements is AGE. SQLiteGraphStore is used by development and regression tests. The legacy sibling DecisionStore is not on these HTTP read paths. Purchasing mounts the SC router against its selected active GraphStore at `apps/purchasing/backend/app/main.py:803`.

## Per-Endpoint Trace Table

Paths beginning `backend/` or `scoring/` are relative to `copilot_sdk/`. AGE paths refer to `../ci-platform/ci_platform/graph/age_graph_store.py`. Counts and bytes are observations of this prepared graph, not a general capacity bound.

| Endpoint | Handler file:line | Data source | Query type | Record count read → returned | Response bytes | Why it costs time |
|---|---|---|---|---|---|---|
| `/api/self/decisions` | `backend/self_computation_router.py:482` | GraphStore directly; no scorer traversal | `get_all_decisions` (`AGE:3084`) plus `get_verified_decisions` (`AGE:2624`), merge by ID, filter, slice | 808 active + 504 verified → 50; total 808 | 72,021 | Full domain reads, Outcome join, decoding and Python merge happen before the existing limit. About 2,103,228 bytes of decoded intermediate JSON for a 72KB response. Overlapping verified reads now share work |
| `/api/self/audit-trail` | `backend/self_computation_router.py:526` | GraphStore ledger, then verified history fallback | `list_ledgers` (`AGE:209`, `_list_platform_state:138`); on empty ledger, read all verified decisions then slice | 0 ledgers + 504 verified → 20 | 29,538 | Two sequential store calls; empty-ledger fallback loads far more than the response. A decision-specific lookup also searched all verified records. Coalescing applies to that history read |
| `/api/self/accuracy-alerts` | `backend/self_computation_router.py:459`, `:423` | GraphStore verified decisions | Direct Python call to accuracy handler; full verified query and category aggregation | 504 verified → 5 categories | 442 | Approximately 884,876 bytes of decoded verified data for a tiny aggregate. Same work also requested by accuracy-by-category; overlapping reads now coalesce. No internal HTTP request |
| `/api/self/rule-lifecycle/active` | `backend/self_computation_router.py:515` | EvolutionState and PromotionState | Two domain/key lookups (`AGE:176`, `:194`, `_get_platform_state:117`), ordered latest, LIMIT 1 | 0 + 0 records → two null fields | 76 | Two graph round trips; no decision scan or expensive computation in this handler. Direct store calls measured 7.0ms and 6.1ms in the separate probe. Historical multi-second browser duration is not evidence of an intrinsically slow lookup |
| `/api/context/today-summary` | `apps/purchasing/backend/app/context_router.py:243`, `_get_weather:195` | Open-Meteo HTTP, with existing fixture fallback | `get_weather_factor(use_live=True)` made an external request on every call, with a 5s timeout | One forecast | 278 | External I/O; `events` is an empty list and date formatting is trivial. Both today-summary and weather requests repeat the same lookup. The live forecast now expires after 300s; failure fallback after 15s |
| `/api/trajectory` | `backend/scoring_router.py:343`, `scoring/scorer.py:1722` | Proxy → cached scorer → **fresh GraphStore reads** | Before: checkpoint query plus verified query; `compute_trajectory` discards checkpoints. Before: two growing-prefix win-rate scans per point | 2 legacy checkpoints + 504 verified → 52 points | 4,163 | One unnecessary query and O(n²) prefix work; fixed to one verified read and a cumulative pass after sorting. Proxy RLock can add waiting behind other scorer operations |

Supporting endpoints were also traced: `/api/self/centroid-timeline` calls `centroid_history` and requests 50 checkpoints with `include_v2=True` (`self_computation_router.py:155`, `:103`); `/api/self/accuracy-by-category` is the same aggregate used by alerts (`:423`). The timeline's 188,945-byte response includes existing centroid tensors and metadata. Removing them by default would change the public response contract.

There is no evidence that cached centroid traversal or scorer construction makes the SC list/accuracy/audit/lifecycle endpoints slow: they call the injected GraphStore. `FreshScorerProxy` is involved in trajectory, whose data still comes from the store on each invocation.

## Root Cause Classification

| Endpoint | Classification | Supported conclusion |
|---|---|---|
| Decisions | **B, F**, secondary A/C | Limit is applied after two complete domain reads; server-side filtering/projection is missing on this path. Merge cost and result serialization are secondary at 808 decisions |
| Audit trail | **B, F**, conditional E | Ledger lookup followed by full verified-history fallback. The cascade is a second store call, not an HTTP call |
| Accuracy alerts/by-category | **B, F**, secondary C | Repeated verified reads dominate a five-category Python aggregation. Coalescing reduces concurrent duplicate I/O without retaining stale aggregates |
| Rule lifecycle | **F**, browser queueing | Two small lookups. No A/B/C/D/G explanation for a five-second handler was observed; current direct call was 44ms |
| Today summary | **F, E**, browser queueing | External weather call/fallback, repeated across route consumers; formerly uncached live I/O |
| Trajectory | **B, C, F**, possible proxy lock waiting | Unused checkpoint query and quadratic prefix scans are proven in source. G is a separate correctness risk, not scorer recreation per request |

**A (returned data volume)** and **D (Pydantic serialization)** are not established as the primary causes of the historical latency. Response sizes are bounded and direct HTTP timings include validation/serialization. Intermediate decision data is much larger than the response. The query patterns load all matching domain rows, but this audit did not run an EXPLAIN plan and does **not** claim to have proved a missing PostgreSQL index. A Python limit added after those reads would not fix the query cost.

In the current pre-fix browser trace, second-wave `/decisions` had **553ms before requestStart**, approximately **184ms between requestStart and responseStart**, and completed at **746ms**. The second today-summary request had **826ms before requestStart**, then about **747ms TTFB**, completing at **1,579ms**. This distinguishes browser queueing from time after dispatch, although TTFB still includes server queueing, middleware and network overhead. The historical report does not contain equivalent server spans, so an exact retrospective split of its 7,478ms is unavailable.

The previously documented ROI render/fetch loop is already fixed in the starting checkout: the component passes the stable module function `fetchRoiSummary` (`apps/purchasing/frontend/src/components/PurchasingBeatPanels.tsx:47`, `:88`). It was not changed or claimed as a new fix here. React StrictMode remains enabled. Global Playwright setup still warms four frontends; its time is included in command wall time (`e2e/global-setup.ts:5`, `:16`).

## Response Size Table

Before measurements: `logs/sc_before_sequential_elevated_client.json`. The endpoint probe reads complete bodies and saves parsed payloads for comparison; the counts below are actual domain/response counts, not its approximate generic `entries` display.

| Endpoint suffix | Current before HTTP ms | Bytes | Returned records / domain total |
|---|---:|---:|---|
| `/self/decisions` | 86.472 | 72,021 | 50 / 808 |
| `/self/audit-trail` | 82.631 | 29,538 | 20 fallback trails; existing total field is 20 |
| `/self/accuracy-alerts` | 45.630 | 442 | 5 categories / 504 verified |
| `/self/rule-lifecycle/active` | 43.605 | 76 | Evolution and promotion absent |
| `/self/centroid-timeline` | 50.199 | 188,945 | 50 checkpoints |
| `/self/accuracy-by-category` | 63.289 | 442 | 5 categories / 504 verified |
| `/context/today-summary` | 780.432 | 278 | One forecast |
| `/trajectory` | 80.539 | 4,163 | 52 points / 504 verified |

Health reported `iks_verified_count=504`, `cache_hits=0`, `cache_misses=0`, `cache_size=0`. Those cache counters describe the existing entity-context cache; they do not instrument all application caches. GraphStore is AGE and domain is Purchasing.

A separate **read-only** AGE method probe measured: all decisions 186.2ms / 808 rows; verified decisions 63.0ms / 504 rows; 50 timeline checkpoints 87.0ms; unused legacy trajectory checkpoints 33.7ms / 2 rows; empty ledger lookup 40.8ms; evolution 7.0ms; promotion 6.1ms. These calls used a separate client and ran at a different time, so they must not be added or subtracted to explain the sequential HTTP measurements. Decoded intermediate sizes use Python JSON encoding, not PostgreSQL wire byte counts. Evidence: `logs/sc_store_profile.log`, helper `../.codex_tmp/sc_store_profile.py`.

Initial sandboxed HTTP probes suffered intermittent ~19s connection resets after the backend logged 200, and sandboxed startup could not access the existing outbox. Restarting with normal permissions and repeating sequential HTTP measurements outside the sandbox produced complete, sub-second responses. However, a later 16-request concurrent probe outside the sandbox also had one reset, so the resets cannot be attributed solely to sandboxing. They existed before these changes and remain an unresolved transport/concurrency observation, not a proven expensive-handler cause. Failed probes remain in `logs/sc_before_*.json` and `logs/sc_after_waves.json`; only completed sequential requests are used for the before/after table. No reset-masking retry was added to the probe.

## Fixes Implemented (with before/after timing)

1. **Coalesce overlapping verified-history reads.** `backend/coalesced_read.py:13` owns only in-progress futures. The SC router keys them by store identity, domain and current tenant (`self_computation_router.py:62`). Decisions, accuracy/alerts, audit fallback, counterfactual and decision-flow share an overlapping verified read. The lock protects the future registry, not the database call; waiters receive independent deep copies. Completed reads are removed, errors propagate and are removed, and requests after completion read the store again. No result is retained as a TTL cache. Overlapping callers share the producer's database snapshot: this does not guarantee strict read-after-write if a mutation commits during that in-flight read. The helper is for diagnostic reads, is per router/app/process, and does not coordinate workers or learning transactions. Implementation plus its focused tests is below 200 new lines.

2. **Bounded weather reuse.** `scoring/verification/weather.py:33` caches immutable forecasts for 300 seconds and cached fallback for 15 seconds, with a lock spanning refresh, at most 128 ZIP keys and existing five-second HTTP timeout. Frozen inputs are checked before the live cache on every call. The source label remains `live`, `cached` or the freeze file's source; failure is not relabeled as live. No model/control state is cached. The cold external fetch can still be slow during provider failure; this is not a guarantee that every cold request meets a one-second SLO. Implementation and local-HTTP tests are below 200 new lines.

3. **Trajectory query/computation reduction.** `scoring/scorer.py:1722` no longer fetches checkpoints that `compute_trajectory` immediately discarded. Existing checkpoint filter arguments remain accepted; they never affected the returned decision-derived trajectory. `scoring/trajectory.py:51` computes cumulative correct/outcome counts once, retaining existing sort order, point spacing, rounding, missing/null outcome semantics and final partial point. Complexity becomes O(n log n) sorting plus O(n) computation, rather than quadratic repeated prefixes. The local 504-record benchmark measured roughly **2.40ms for the old repeated-prefix portion vs 0.31ms for the complete new computation**; this is a microbenchmark, not an HTTP speedup claim. The removed checkpoint call independently cost 33.7ms. Implementation and focused tests are below 200 new lines.

After-fix measurements, outside the sandbox with pytest finished:

| Endpoint suffix | Before ms | After cold ms | After warm ms |
|---|---:|---:|---:|
| `/self/decisions` | 86.472 | 115.771 | 98.383 |
| `/self/audit-trail` | 82.631 | 67.216 | 86.108 |
| `/self/accuracy-alerts` | 45.630 | 63.440 | 63.117 |
| `/self/rule-lifecycle/active` | 43.605 | 16.553 | 28.412 |
| `/self/centroid-timeline` | 50.199 | 79.595 | 63.372 |
| `/self/accuracy-by-category` | 63.289 | 67.235 | 63.218 |
| `/context/today-summary` | 780.432 | 782.760 | 16.719 |
| `/trajectory` | 80.539 | 49.130 | 49.831 |

All six target endpoints met **<1,000ms** in both sequential after passes. Weather shows the expected warm reuse; trajectory removes one read. The other point measurements vary and do not establish a sequential speedup from in-flight coalescing, which only applies to overlapping reads. Evidence: `logs/sc_after_cold.json`, `logs/sc_after_warm.json`.

All seven non-weather response bodies were **identical parsed JSON**, with identical byte sizes, before and after. Today-summary kept the same schema/byte size and live provenance; the external forecast changed from 67.6°F/4.8mph to 66.9°F/4.6mph between measurement times. Cold and warm after requests reused the same forecast. The 16-request concurrent probe had 15 completions in 29–350ms and one `/self/decisions` connection reset at 19.24s; it is not presented as an all-green concurrency gate.

## Fixes Deferred (>200 lines, with design)

**Database-side page/projection/aggregate read contract (estimated 300–450 new lines with adapter/contract tests).** Introduce an optional read-model capability without adding required members to the runtime-checkable GraphStore protocol. Define decision page results with stable `(created_at, decision_id)` ordering, an exact matched total, complete existing fields by default and an opt-in summary projection; filters must preserve the current recommended/actual/action OR match and outcome behavior. Define ledger pages with the existing verified-history fallback, and category aggregates with the exact correctness/null semantics used today. SQLite implements WHERE/JOIN/ORDER BY/LIMIT plus aggregate queries; AGE implements equivalent projections/aggregates and bounded records; in-memory, tenant and dual-write wrappers preserve domain/tenant filtering before pagination. Use actual query plans to choose indexes. A limit on base rows before tenant filtering or before joining outcomes would silently change results.

Add `limit=all` only as an explicit export path alongside the current integer defaults; do not remove the existing 50-decision, 20-trail and 50-checkpoint defaults. Keep accuracy and trajectory statistics over the entire verified population. Acceptance: filtered/unfiltered pages match the existing complete-read reference, duplicate timestamps, confirmed/overridden/null outcomes, archived rows, empty-ledger fallback, multiple tenants and equal results across real SQLite/AGE stores. Reducing the public response fields by default or slicing before filtering is not a compatible shortcut. This is deferred under the requested size limit, not because returning 50 records alone is sufficient query pagination.

**Durable cache/model revision and invalidation (estimated >400 new lines; see workers audit).** A TTL alone does not preserve immediate read-after-write semantics. A persistent revision must advance atomically with each learn/reset/rollback/promotion/transfer/import and authoritative model commit. Snapshot and response cache keys must include store, tenant, domain, all query parameters and revision; use bounded TTL only as a fallback freshness bound, not as the sole invalidation channel. Direct store writers and SOC/S2P bridges must participate. A cache hit must not mix a fresh count with old category or model state. Test alternating worker reads/writes and crash/retry boundaries against serial reference behavior. This audit uses in-flight coalescing instead of adding a retained SC response cache, and leaves FreshScorerProxy construction/lifetime unchanged.

## Cross-Copilot Impact

Trading and DataOps mount the same SC router, so overlapping verified reads are coalesced there too. Trajectory's implementation is shared by all CompoundingScorer consumers. Weather affects consumers of the Purchasing weather helper, including today-summary/weather/factors, without changing non-live preset fixtures. No GraphStore interface, AGEClient, SQL/Cypher write path, frontend selector, Playwright retry, timeout or worker count was changed.

The default responses are preserved: decisions still default to 50/max 500 and filter before slicing; audit still defaults to 20/max 100; accuracy uses all verified records; timeline still defaults to 50/max 500; trajectory still includes all ten-decision points and the final partial point. No new `limit=all` parameter is claimed: the problem is store-side reads, and the compatible cross-store design is deferred above. Existing PW assertions referencing decisions/audit/accuracy/lifecycle were inspected; no selector or expected count was altered.

Changed files for this task:

- `copilot_sdk/backend/coalesced_read.py`
- `copilot_sdk/backend/self_computation_router.py`
- `copilot_sdk/scoring/scorer.py`
- `copilot_sdk/scoring/trajectory.py`
- `copilot_sdk/scoring/verification/weather.py`
- `tests/backend/test_coalesced_reads.py`
- `tests/scoring/test_weather_cache.py`
- `tests/scoring/test_trajectory_scaling.py`
- `scripts/sc_endpoint_probe.py`
- `e2e/diagnostics/sc-network-probe.mjs`
- `docs/diagnostics/sc_endpoint_slowness.md`

Required generated graph refresh: `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`, `graphify-out/manifest.json`. Validation outputs are in `logs/sc_*`, `e2e/test-results/`, and the temporary store probe under `../.codex_tmp/`. Changes from the prior workers audit and unrelated pre-existing work were retained.

## Connection to FreshScorerProxy caching (workers audit)

`backend/scorer_proxy.py:33` lazily retains one scorer under an RLock. It does not create a scorer and connection per request. SC list/accuracy/audit/lifecycle handlers use GraphStore directly; they do not traverse that cached scorer's centroids or verified-history cache. Trajectory calls the proxy (`:102`) and the scorer reads persisted verified decisions, so making the proxy recreate its scorer would add construction/restore work without fixing these query patterns.

The workers audit's stale-centroid finding remains valid: another process can learn without refreshing this scorer. The new weather cache stores external context; the SC helper only shares an overlapping read and retains no result across completed calls. Neither claims to solve multiworker model consistency. Timings and PW gates here use one backend worker; increasing workers is not part of the performance fix.

## Validation Results

Mypy passed on all nine changed Python files using `--follow-imports=skip --no-error-summary` and existing repository configuration (`logs/sc_mypy.log`). Focused tests: **51 passed**, including actual SQLite reads, overlapping callers, immediate outcome visibility, caller-copy isolation, error recovery, real local HTTP weather requests/expiry/fallback/freeze priority and trajectory result/scaling checks (`logs/sc_focused_tests.log`).

| Gate | Result | Evidence / limitation |
|---|---|---|
| A: mypy | **9/9 changed Python files passed** | `logs/sc_mypy.log`; no new ignore/suppression or configuration relaxation |
| B: full SDK | **3,349 passed, 1 failed**, 839.38s | `logs/sc_sdk_tests.log`; the failure is the existing documentation naming check described below |
| C: Purchasing backend | **713 passed, 1 skipped, 0 failed**, 408.40s | `logs/sc_purchasing_tests.log` |
| D: sequential endpoint timing | **All six <1,000ms**, cold and warm | Cold maximum 782.760ms, warm maximum 98.383ms; full body reads, no pytest load, one backend worker |
| E: Purchasing dashboard | **10 passed without retries**, **97.729s command wall time** | `logs/sc_pw_purchasing.log`; exact requested command; below historical 144s but **90s target missed** |
| F: Trading dashboard | **10 passed without retries**, 85.499s command wall time | `logs/sc_pw_trading.log` |
| F: DataOps dashboard | **26 passed without retries**, 163.603s command wall time | `logs/sc_pw_dataops.log` |

The SDK failure is `tests/test_ent03_models.py::test_no_incorrect_rl_naming`, flagging the pre-existing `docs/design/product_integrity_execution_strategy_v3_0.md` at lines 38, 839, 1480 and 1506. It was also present in the workers audit. Neither the document nor the naming test was edited to obtain a pass. All newly added tests passed in the full suite.

The additional install/import command required by CLAUDE.md also remains unsuccessful: `pyproject.toml:61` names the existing unimportable `setuptools.backends._legacy:_Backend` build backend, and `CopilotFramework` is not an export of the existing `copilot_sdk/__init__.py`. `pip install . --no-deps --no-build-isolation` and the requested import were attempted; no package configuration/public export was changed for this latency task. Evidence: `logs/sc_package_check.log` and the import command output. The current scorer/backend imports and live starts succeeded.

Historical 144s and current 97.729s dashboard totals are not a controlled causal comparison: the workers audit used two backend workers and its first timing overlapped other test load; this task uses one worker and idle test infrastructure during timing. The endpoint/trajectory measurements and behavioral tests demonstrate the implemented reductions; they do not justify attributing the whole dashboard difference to these three changes.

The final page probe (`logs/sc_browser_after.json`) still took **8,842ms** overall: DOM content loaded at 1,520ms, screen-ready at 6,934ms, then approximately 1,909ms until all panels were ready. It completed 63 API requests, with three aborted requests involving evolution variants and transfer status. The second `/self/decisions` finished at 2,879ms, including 2,070ms before requestStart and approximately 809ms after dispatch through response completion. The second today-summary finished at 1,547ms, including 1,503ms before dispatch; its actual sent request completed in about 43ms using the cached forecast. This browser workload still shows queueing and a broad readiness dependency chain despite the sub-second sequential endpoint gate. Direct endpoint timings therefore must not be advertised as a universal browser latency bound, and the 90s dashboard target remains unmet.

Final scope: **8 endpoints analyzed** (six reported slow endpoints and two supporting endpoints), **3 fixes implemented**, **2 larger designs deferred**, **11 source/test/probe/report files plus 3 generated graph files** changed for this task. Graph refresh passed. All 46 dashboard tests passed without retries; no newly introduced test failure was observed. The full SDK/package gates remain unsuccessful for the existing issues above, the parallel HTTP reset is unresolved, and multiworker learning correctness is not certified. The updated demo stack is left running with one worker per backend for review.
