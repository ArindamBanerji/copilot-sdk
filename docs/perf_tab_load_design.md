# Performance Tab Load Optimization Design

Date: 2026-09-24. Architecture proposal only; no backend changes or new performance measurements in this task.

## Problem

The supplied measurements put Trading's ten-endpoint Performance API burst at 5.35 seconds on average, versus a target below 1.5 seconds. The listed warm sequential endpoint times sum to approximately 3.58 seconds. Other experiments measured 17.22 seconds sequential and 7.76 seconds with six clients. These are different runs/cache conditions, not interchangeable baselines.

**Recommendation: an app-scoped, prewarmed Performance read model that materializes final display responses from shared inputs, refreshes in one coordinated background job, and is actually consulted by the existing HTTP handlers.** Keep the ten URLs and their response contracts. Do not merely add another TTL around a registry that the handlers bypass.

The target is **API data readiness below 1.5 seconds after materialization is ready**, including bursts during ordinary background refresh. It is not an unconditional cold-process or post-reset guarantee. S2P's approximately eight-second history read alone rules out that guarantee. The separately measured React/Playwright overhead also prevents claiming a complete browser load below 1.5 seconds from this backend change alone.

## Current Architecture (why it's slow)

### 1. TabStateCache exists, but registration is not HTTP integration

In `copilot_sdk/state/tab_state_cache.py`:

- `ttl_seconds` is supported; Trading and S2P registries now pass `5.0`.
- `get_entry()` returns an entry without checking expiry. `get()` and `warm_up()` call `_expire_stale()`, which clears `computed_at` but leaves the previous data and ready status. A caller checking only `get_entry().status/data` can therefore keep serving stale data.
- `get()` can warm every missing registered key, not just the requested keys. `warm_up()` processes batches of five, including cold-tier entries. Warming all Trading keys is not a focused Performance-tab optimization.
- `_run_compute()` executes synchronous callbacks directly on the event loop. `asyncio.gather()` does not make those blocking graph reads or Python computations parallel.
- A registry URL describes a computation; it does not replace the corresponding FastAPI handler.

`copilot_sdk/state/cached_static.py` still exists and some endpoints retain the decorator. Its entry lookup does not enforce TTL. Its single-flight wait can time out after three seconds and allow another computation. Restoring this decorator everywhere would recreate correctness and duplication problems.

Trading's `main.py` constructs the registry and mounts tab-state routes, but its startup hook seeds/restores state without warming tab state. The slow context, analytics, regime, scoring, conservation, and self-computation routes mostly call their own live computations. They do not obtain their responses from that registry.

### 2. CoalescedRead is deliberately not a cache

`copilot_sdk/backend/coalesced_read.py` uses a lock-protected map of in-flight futures. One caller loads; overlapping callers wait for the same result. The map entry is removed when loading completes. Every caller, including the leader, receives a `deepcopy`.

In `self_computation_router.py`, one such reader shares verified-history reads within that router, keyed by store identity, domain, and tenant. It does not coordinate the independent Trading analytics/context routers.

TTL retention is technically possible, but changing the default would break the explicit fresh-read and ownership contract in `tests/backend/test_coalesced_reads.py`. Keep this class unchanged for authoritative reads. Build an opt-in display materializer using the same single-flight principle. Do not pass large result sets through its per-caller deepcopy path. The measured 0.258-second copy of 3,648 rows shows why; ten such copies would cost about 2.58 seconds, although the code does not establish that all ten current endpoints perform that exact copy.

### 3. What Trading actually registers

`apps/trading/backend/app/state/key_manifest.py` defines 43 keys. `trading_registry.py` registers analytics, history, measurement, fingerprints, trajectory, conservation, journal, regime, trust, correlation, bootstrap analytics, and other tab data.

The current registry has one direct `graph_store_factory()` call site, inside `graph_store()`, and five direct `graph_store()` call expressions: centroid history and analytics/cohort entries in the compute and service dictionaries. Additional helpers receive the factory and invoke it indirectly. These are source-site counts, not the number of database calls per refresh; the two dictionaries are not automatically both executed.

Its `_SharedDecisionStore` caches only `get_all_decisions()`. Other methods, particularly `get_verified_decisions()`, pass through uncached. The four vol/VRP/dispersion computations each call `verified()`. Journal, regime, and other helpers can request history again. Expiry is calculated before the fetch, and the shared dictionary has no concurrent-miss coordination or tenant/generation key.

More importantly, `main.py` supplies raw graph-store factories to the live routers, bypassing this wrapper. There are also contract mismatches: the actual `/api/trading/regime/detail` is not the registry's regime summary; `/api/self/evolution/summary` is not the registered Trading evolution log; the registry's conservation helper omits the HTTP route's composite-gate and projection enrichment. Reusing similarly named entries would change responses.

The scoring router exposes both `/api/measurement-state` and `/api/trading/measurement-state`; both aliases must resolve to the same prepared result.

### 4. The herd explanation is incomplete

The code confirms disconnected caches and repeated reads/computation. It does not prove that pool contention or cold TTL misses alone cause the whole 5.35-second floor. The supplied herd experiment improved only from 3.32 to 2.79 seconds with coordination plus TTL, approximately 16%.

Other relevant serialization points include the `FreshScorerProxy` lock, synchronous work executed on the event loop, repeated verified-history reads, result copying, JSON construction, and the market-service work in `routers/regime.py`. Python threads do not generally parallelize Python CPU work. Measure these components instead of attributing all latency to the GIL or pool.

The actual Trading `PerformanceScreen.tsx` first awaits analytics, trajectory, and conservation, then renders child panels that issue additional requests. Thus the real screen includes a waterfall and more work than the fixed ten-request simulation. Its `data-screen-ready` marker does not mean every child panel has finished.

### 5. Other copilot wiring

| Copilot | Observed implementation | Consequence |
|---|---|---|
| Purchasing | `main.py` shares order-history rows with a five-second cache. A separate cached conservation helper serves internal callers, while the public conservation router still receives the scorer. | Some warm paths work; this does not establish caching of the public conservation endpoint. |
| DataOps | `main.py` has entity-context/intelligence caches, but no equivalent Performance TabStateCache registry. | Existing caches do not automatically materialize all display analytics. |
| S2P | `s2p_registry.py` has TTL and startup warm-up, but preview paths use `services/s2p_preview_data.py`. That reader records time before loading and reloads verified rows even on a hit. | An eight-second load can arrive already older than a five-second TTL; registry warm-up does not fix a bypassing route. |
| SOC | Startup-populated graph snapshot and mutation updates, described below. | Several display paths already avoid repeated graph work. |

Increasing latency across two calls is not evidence of a growing list or memory leak. This design does not assume an accumulation bug without identifying retained state and measuring its growth.

## SOC Architecture (why it's fast)

The first 100 lines of `../gen-ai-roi-demo-v4-v50/backend/app/main.py` do not contain a universal response cache. Following startup reveals the relevant mechanism:

- `main.py` initializes `GraphSnapshot.from_graph(graph_client)` and installs it through `set_snapshot()`.
- `backend/app/state/graph_snapshot.py` holds verified/correct counts, override statistics, category counts, and IKS in memory.
- Successful verification paths update that snapshot through `on_verified_decision()`; IKS has a corresponding update method.
- SOC display handlers and balance-sheet/evidence/governance services consume `get_snapshot()` instead of independently rebuilding the same statistics.
- Cross-graph discovery separately has a 60-second cache warmed during startup. Fixture caches also exist, but they are not a suitable production pattern for mutable decisions.

This explains a concrete architectural advantage, not proof that every SOC endpoint shares one cache. Reuse its existing snapshot in the common adapter; do not replace it with a new full-history scan every five seconds. Preserve graph-first writes and post-commit snapshot updates.

## Proposed Fix

### One read model per application scope

Add `PerformanceReadModel` in the SDK. Each app owns an instance on `app.state`; scope it by domain, authenticated tenant, and a stable store/backend epoch. Do not use a module-global domain-only dictionary or the identity of a freshly constructed adapter as the entire key.

Each scope retains one published generation, at most one in-flight refresh, and an explicit bounded set of display keys. Do not cache arbitrary URLs, invoice IDs, filters, or credentials. Canonicalize the known frontend parameter sets; unsupported variants follow their existing live paths. Tenant contexts must be explicitly bound inside background work, not inferred from whichever request happened to start a refresh. Bound active tenant scopes and evict idle ones; never enumerate or prewarm all tenants implicitly.

```text
startup / committed mutation / refresh due
                    |
             one refresh future
                    |
       shared input snapshot, once per build
                    |
       pure existing response computations
                    |
       validate + atomically publish generation
                    |
       existing HTTP handlers -> prepared responses
```

A snapshot build obtains all decisions once and verified decisions once when both are required. Do not assume they are semantically interchangeable: verified queries can include joined outcome data and ordering needed by the gate. Fetch checkpoints, governance, and market state once per applicable build as well. Use cheap count queries where equivalent; do not introduce general Cypher aggregation.

The input view is private to the builder, exposes only explicitly supported read methods, and must fail visibly on an unplanned full-scan request rather than silently forwarding it to the database. Pure computations share read-only rows and precomputed indexes. If a helper mutates its input, fix that helper or copy only its working data. Never attach the read view to the live scorer's graph store.

Cache **final validated display payloads**, not just database rows. This removes repeated bootstrap, aggregation, scorer access, and large-row copying from request time. Return a copy of the small response payload under normal FastAPI response-model validation. Pre-serialized bytes are a later optimization if profiling justifies the extra response-contract handling.

### Refresh and freshness contract

Use a monotonic clock and record both input acquisition time and successful publication time. Cache reuse starts at successful completion, not before loading. Publication time alone must not be presented as the age of the underlying data.

| State | Request behavior |
|---|---|
| Ready, within five seconds of publication | Serve prepared response; no graph/scorer/analytics work. |
| Soft TTL elapsed, refresh active | Serve last valid display response within the maximum input-age bound; join/schedule only one refresh. |
| Missing, explicitly invalidated, or too old | Join one refresh; await asynchronously with a bounded timeout. Return a truthful unavailable error on failure, not fabricated empty/success data. |
| Committed mutation changed generation during build | Discard the obsolete build. Never republish pre-mutation data as current. |

Proposed display-only maximum input age: **30 seconds**, with refresh eligible five seconds after the previous completion. This is a bounded-staleness design choice, not a claim of strict five-second source freshness. For S2P, five seconds plus an eight-second build produces roughly thirteen-second publication intervals; a strict five-second fresh-data SLA would require incremental materialization or faster source reads, beyond this prompt. Instrument actual input age and reject publication/serving beyond the bound.

Expose generation, input age, and fresh/refreshing state in response headers/diagnostics without changing JSON bodies. Health/liveness stays cheap; track Performance readiness separately. Start warm-up after seed/restore; report not-ready while it runs rather than silently moving its delay into a success metric. Cancel timers and close the dedicated worker on shutdown.

Use one background build worker per app, with non-overlapping refreshes and failure backoff. Run blocking graph reads and synchronous calculations outside the event loop; do not share checked-out database connections across threads. This isolates blocking work, not Python CPU execution. Record event-loop lag and refresh CPU time, and avoid continuous rebuild loops when builds exceed five seconds.

Keep the integration API small: `start()/stop()`, `read(scope, key, canonical_params)`, `refresh(scope)`, and `invalidate(scope, reason)`. The app adapter supplies input acquisition and pure payload builders. A request timeout must not cancel the shared refresh or permit a second leader while its thread is still running. Track errors per display key so an unavailable market provider does not discard successful unrelated analytics; retained prior payloads keep their original input ages and generations, never a falsely renewed timestamp.

### Mutation correctness and authoritative paths

Wire a generation bump to existing successful-write/invalidation hooks for learn/outcome, reset/seed, rollback/restore, transfer, and any regime/config change consumed by the display. Bump when relevant state actually changes, including a partially successful learn; do not rely only on an overall `status=complete`. Coordinate generation transitions with the existing mutation lock. Copy only small scorer state under that lock, then release it before graph IO or analytics; do not introduce reversed lock ordering.

Do not run HTTP handlers as background jobs. Extract read-only payload builders, including a non-persisting fingerprint calculation where necessary. Do not construct a new scorer each refresh or let refresh write checkpoints/fingerprints.

Conservation display must preserve the **entire** current router payload: composite-gate layers, mode overrides, and projection fields. Background computation must retain ordered outcomes where required. Internal score/learn authorization always reads live authoritative state. Cached `/conservation/status` is a display projection, not permission to act; review its consumers before enabling caching.

Leave authoritative decision lists, audit/replay/export reads, and mutation responses outside this response cache. In particular, retain `/api/self/decisions` limit pushdown and CoalescedRead's default fresh semantics. Its remaining full verified-history merge is a separate optimization, not solved by this design.

External writers are detected through the bounded refresh interval, not immediate local invalidation. Strict read-after-write applies to observed application mutations; claiming it for arbitrary external writes would require a shared revision/event mechanism.

### HTTP integration and all-five applicability

Use optional, explicit read-model hooks in route factories, retaining existing live behavior when no materializer is configured. All production apps opt in during startup. Do not globally monkeypatch GraphStore or restore `@cached_static`.

Trading's initial allowlist must cover all ten measured paths: context analytics, vol-sharpe, regime/detail, conservation/status, self accuracy-by-category, self centroid-history, self evolution/summary, `/api/fingerprint`, VRP attribution, and prefixed measurement-state. Add trajectory because the actual screen awaits it. Validate the frontend's default query parameters and response schemas; similarly named registry entries are not substitutes.

Purchasing and DataOps use the same engine with their existing display payload builders. S2P uses it for Performance summary and shared display inputs; its preview reader needs the completion-time/input-age fix and common snapshot input, but queue eligibility must still overlay fresh outcomes so a confirmed invoice disappears immediately. Do not cache actionable queue contents as a stale display response. SOC publishes from its existing incrementally maintained GraphSnapshot and only refreshes additional expensive display dependencies as needed.

For keys already represented in Trading/S2P TabStateCache, make the selected registrations delegate to the read model's prepared payloads. The read model owns freshness for these keys; do not maintain a second independent TTL/value for the same payload. Keep unrelated registration, invalidation, and dynamic-query behavior unchanged. Fix expiry-aware lookup separately within this integration so a legacy decorator cannot bypass configured TTL; preserve no-TTL defaults.

## Implementation Plan (specific files, specific changes)

Keep this to one shared implementation, thin adapters, and focused tests. No frontend rewrite, database migration, Redis, process pool, new GraphStore protocol, or blanket conversion of 43 Trading keys.

1. **SDK core:** add `copilot_sdk/state/performance_read_model.py` containing the scope, single-flight refresh, private input view, immutable publication, TTL/max-age, generation invalidation, and lifecycle API. Add deterministic tests under `tests/state/`. Keep `backend/coalesced_read.py` behavior unchanged.
2. **SDK HTTP and invalidation:** extract reusable pure payload builders and add optional hooks in `copilot_sdk/backend/{scoring_router,self_computation_router,conservation_router}.py`. Connect app-owned invalidation through `copilot_sdk/state/invalidation.py` without making the existing global domain registry the isolation boundary. Update `state/tab_state_cache.py` and `state/cached_static.py` only for explicit expiry-aware access and selected read-model delegation; do not change all warm-up semantics.
3. **Trading:** update `apps/trading/backend/app/main.py`, `state/trading_registry.py`, `context_router.py`, `routers/analytics.py`, and `routers/regime.py`. Replace the registry-local decision-cache wrapper for selected computations with the shared build view. Extract exact live payload builders, add missing measured keys, wire the live routes, and start/stop the materializer after seed/restore. Keep bootstrap `n_boot=50` with batch override support; no further sample reduction. Preserve market-provider behavior with bounded refresh timeouts.
4. **Purchasing:** update `apps/purchasing/backend/app/main.py`. Move existing order-row/waste display computation into the adapter using one build input; route waste analysis/summary and display analytics through prepared results. Wire the public conservation router, not just `_conservation_status()`. Preserve live conservation checks used by purchasing actions.
5. **DataOps:** update `apps/dataops/backend/app/main.py` and its context display payload builders in `context_router.py`. Install the same lifecycle/hook integration for analytics and shared scoring/self/conservation displays. Reuse entity-context and intelligence caches for their own dependencies; do not flush or rebuild them unnecessarily.
6. **S2P:** update `../s2p-copilot/backend/app/main.py`, `state/s2p_registry.py`, `services/s2p_preview_data.py`, and `routers/s2p_performance.py`. Use the common materializer for Performance, remove duplicate selected-key warm-up, correct timing/isolation of shared history, and preserve immediate outcome visibility in previews. Forward S2P's own mutation hooks to the read model, not only the SDK learn hook.
7. **SOC:** update `../gen-ai-roi-demo-v4-v50/backend/app/main.py` and `state/graph_snapshot.py`, plus thin lookup integration in the consuming display handlers/services. Use existing snapshot updates to invalidate/publish prepared displays. No repeated all-decision scan and no replacement of authoritative graph-first writes.

Where an app needs several builders, put them in one small `state/performance_read_model.py` adapter rather than expanding `main.py`. The above is one coordinated change set; do not broaden it to unrelated tabs or every parameter variant. Source code tests must determine whether any existing route has a stronger freshness contract and must stay live.

### Required verification before calling the implementation complete

- Preserve all existing response schemas, numerical calculations, error handling, and tests. Compare prepared payloads with the current live builders on the same InMemoryGraphStore data. Do not remove assertions or blanket-disable materialization for tests.
- Keep `tests/backend/test_coalesced_reads.py` passing unchanged: independent nested results, fresh later reads, tenant isolation, and immediate authoritative visibility after committed writes.
- Add a ten-route concurrent-burst test proving one all-decision read and at most one verified-history read per build, and zero such reads/analytics calls per ready display request. Test a slow load longer than TTL, clock-driven expiry, refresh failure/retry, stale cutoff, generation changes during refresh, nested payload ownership, and bounded scope/variant memory.
- Test conservation composite gates/projections, fingerprint non-persistence, S2P confirmation visibility, startup readiness, and shutdown cancellation. Tests must cover explicitly enabled materialization, not only the fallback path.
- Run SDK tests and the Trading, Purchasing, DataOps, S2P, and SOC backend suites in their established environments, then the affected mypy checks and Performance PW specs. Module names such as `app` require app-specific test invocations, not one mixed Python import environment.
- Benchmark the ten endpoint burst with 6 and 10 clients: process cold, ready warm, soft-expiry refresh, post-mutation, and refresh failure. Run at least 30 ready bursts spanning multiple refresh cycles, reporting p50/p95, database-call counts, build time, input age, scorer-lock wait, and event-loop lag. Gate ready/refresh-period p95 at **<1.5 seconds**, with correctness gates independent of timing.
- Capture the real frontend request waterfall separately, through completion of required child panels, not only `data-screen-ready`. Record startup/post-mutation rebuild cost honestly; no invented before/after numbers.

## Expected Improvement (with numbers)

| Workload | Evidence/baseline | Expected result or bound |
|---|---|---|
| Three independent history reads | 2.665 seconds versus 0.861 shared | Approximately 1.804 seconds saved in that experiment; not the whole tab speedup. |
| Cold Trading build | All rows 0.65 + verified rows 0.666 + bootstrap 0.118 seconds | About 1.43 seconds before other analytics/IO/serialization; cold <1.5 seconds is not supported. |
| Prepared Trading ten-response burst | 5.35-second supplied average | Engineering budget 0.5–1.0 seconds, acceptance p95 <1.5 seconds; unmeasured until implemented. At 1.5 seconds, reduction is approximately 72%. |
| Prepared request graph/analytics work | Repeated independent work currently | Zero on ready display paths; the worker performs one bounded build. |
| Cold S2P | Approximately eight seconds for all-history IO alone | Startup/rebuild still takes at least that read duration; prepared Performance responses target the same <1.5-second burst gate, subject to response size and refresh contention. |
| Purchasing/DataOps/SOC | Some warm paths already 0.1–0.7 seconds | Preserve existing speed and reduce burst duplication; no justified universal speedup multiplier. |
| End-to-end browser/PW | Additional supplied 1.7–2.5 seconds | Backend fix does not remove this overhead or the frontend waterfall. |

These are budgets and bounds derived from supplied data, not benchmark results. A background thread can still contend for the GIL during refresh; the during-refresh gate is essential. If it fails after eliminating repeated work, profile and narrow the offending computation before considering process isolation.

## Risks

- **Staleness versus latency:** serving during refresh requires the explicit bounded-staleness contract. Strict five-second freshness for S2P is not achievable with its current eight-second scan. Post-mutation latency can exceed the target when correctness requires a rebuild.
- **Semantic drift:** registry summaries differ from actual endpoints; reuse extracted live builders and schemas, including full gate/projection data, not approximate replacements.
- **Safety boundaries:** stale display state must never become an authorization/score/learn gate. Actionable S2P queues retain fresh outcome checks.
- **Races and mutable ownership:** reject obsolete generations; isolate stores/tenants; never expose mutable cached row lists to callers. Local generation checks do not create a transactionally consistent snapshot across arbitrary external database writes.
- **Refresh side effects:** scorer fingerprint/trajectory helpers and providers must be audited for writes. Background materialization is read-only; mutations remain in their existing workflows.
- **Load and memory:** S2P rebuilds are expensive. One worker, one active generation plus one build, bounded scopes, explicit age limits, and failure backoff prevent unbounded work. Large CPU phases can still affect a single-worker API.
- **Unavailable dependencies:** market-data or AGE failures must not silently publish empty healthy results. Preserve the last valid generation only within its declared age bound and expose failure/readiness.
- **Compatibility:** existing tests may depend on fresh reads outside display routes. Optional integration preserves unconfigured router behavior, but production-configured integration must also be tested; a passing fallback-only suite is insufficient.

### Uvicorn workers

`demo.ps1` launches uvicorn without `--workers`. That ordinarily means one worker unless environment/configuration such as `WEB_CONCURRENCY` overrides it. This is a launcher observation, not verification of the running process topology.

Four workers may improve CPU throughput but create four independent caches, scorers, mutation locks, and background jobs; they can multiply cold AGE load and disagree after learn/reset. Process memory is not shared, as described in the [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/#memory-per-process). Shared revisions/invalidation and authoritative scorer ownership would be prerequisites. Keep one worker for this bounded fix.

## Alternative Approaches Considered

| Approach | Decision |
|---|---|
| Per-endpoint five-second TTL alone | Insufficient: independent misses, bypassed caches, and recomputation remain. |
| Extend CoalescedRead with TTL globally | Reject: changes fresh-read/ownership semantics and retains deep-copy costs. An opt-in materializer provides retention without changing that contract. |
| Request-scoped cache | Useful inside one bundle build, but ten HTTP requests have ten request scopes. The sharing boundary must be app/tenant/generation, not a request-local variable. |
| Shared raw decisions only | Necessary input optimization, insufficient for repeated verified reads, analytics, scorer locks, and serialization. Materialize responses as well. |
| Warm all TabStateCache entries every five seconds | Reject: warms unrelated keys, executes synchronous callbacks inline today, and still does not wire the HTTP handlers. Refresh an explicit display allowlist. |
| Single aggregate Performance HTTP endpoint | Reasonable later for frontend waterfall and cross-panel generation pinning. Not necessary for the first fix; bundling alone still recomputes expensive work unless backed by this read model. |
| More AGE connections or uvicorn workers | Does not address repeated work; workers introduce scorer/cache coherence problems. |
| Cypher aggregation | Reject given measured 10.369 seconds versus 1.244 seconds for fetch plus Python. Keep efficient count queries. |
| Further bootstrap reduction or UI polling changes | Bootstrap is already 50; these do not explain or remove the multi-second API floor. |
| Redis/distributed materialization or full incremental graph projections | Longer-term options for multiworker coordination or strict large-dataset freshness. Too broad for this one-prompt implementation. Reuse SOC's existing incremental projection now. |
