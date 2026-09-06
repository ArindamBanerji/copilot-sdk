# Design drift audit

## Executive Summary

Audited on 2026-09-05/06 UTC, Windows, the requested Python 3.11 environment, live AGE graph, and one Uvicorn worker. All seven dimensions were examined. This builds on the [mutable-flow](../diagnostics/mutable_flow_diagnosis.md), [self-computation](../diagnostics/sc_endpoint_slowness.md), [workers](../design/workers_safety_audit.md), [graph-health](../diagnostics/age_graph_health.md), and [Vite](../diagnostics/vite_proxy_analysis.md) reports; it does not attribute their earlier fixes to this change. No git commands were used. Current code, real database probes, and browser requests are the evidence; the quoted commit history was not independently reconstructed.

The structural problem is distributed ownership of the same work: components independently fetch the same state, summaries repeatedly reconstruct the same event history, learning persists several independently maintained representations, and tests wait for an entire diagnostic dashboard before exercising another screen. The numerical score operation and ordinary middleware are small. Seven bounded fix groups address summary query multiplication, overlapping browser GETs, one blocking async handler, adapter-dependent variant ordering, implicit scorer discovery, two swallowed wrong-endpoint waits, and missing SDK frontend build types. Versioned model state, transactional mutation ownership, retention, and page-level request ownership require separate designs.

**Ranked inventory: 16 findings (4 P1, 8 P2, 4 P3). Seven fix groups implemented; five larger implementation packages deferred.** P1 means correctness or cross-process safety, P2 means material latency/scaling or unreliable validation, P3 means maintainability/observability. Larger designs are not silently represented as solved. Multi-worker mutable serving remains unsafe; sequential requests can still hit different workers.

**Purchasing: 47/47 passed without retries in 206.50s wall time**, versus the supplied approximately 9.4-minute baseline. That is **4.39s per test including runner overhead**, meeting the average target in this run; individual-test mean is 4.25s, p95 6.92s, and the first test took 11.41s. This is not an every-test-under-five-seconds or cold-start guarantee. Purchasing/Trading/DataOps backend suites pass 714/1,302/336 tests. Trading dashboard passes 10/10; DataOps has 25 clean passes and one first-load failure that passed on retry. Existing SDK documentation/package gates and cold browser reliability remain qualified below.

## Persistence Path Cascade (I/O ops per POST)

The requested legacy `scoring/compounding.py` and `scoring/storage.py` paths do not exist in this checkout. The implementation is `copilot_sdk/scoring/scorer.py`; the active Purchasing store is `PurchasingActiveAGEGraphStore`. `GraphStore`/SQLite and generic AGE contracts must not be counted as though all are called by every request. Evidence: `apps/purchasing/backend/app/graph_status.py:236`, `copilot_sdk/scoring/scorer.py:429`, and `../ci-platform/ci_platform/graph/age_sdk_adapter.py:50`.

`scripts/design_drift_backend_probe.py` profiled real AGE `_sync_execute` and transaction `_execute_cypher_on_connection` calls under the actual app. The captured query text is in `logs/design_drift_purchasing_io_before.json`. Counts below are logical Cypher executions, including reads; PostgreSQL transaction setup, advisory locking, driver protocol messages, filesystem operations and pool initialization are not separate counted graph queries. A query with SET/CREATE/DELETE is classified as a write even if it also reads.

| Endpoint | Observed total | Reads / writes | In-process HTTP time | Meaning |
|---|---:|---:|---:|---|
| POST `/api/score` | **4** | 3 / 1 | 320, 283ms | Two fresh variant streams, decision lookup, governed decision creation |
| POST `/api/purchasing/verify` | **38** | 29 / 9 | 602ms | Actual Confirm endpoint; this branch also archives old active decisions |
| POST `/api/learn` | **47** | 33 / 14 | 797ms | General SDK learning adds variant outcome and L5 state persistence |

There is no `/api/confirm` on this flow. The item/quantity-only sample in the task is not a valid score request: supply `category`, seven factors and `context`, as in `scripts/mutable_flow_probe.py:14`. A 422 response is not a score performance result.

| POST endpoint | Step (query positions in captured trace) | I/O type / target | Sync? |
|---|---|---|---|
| score | 1–2: choose variant from registrations/outcomes | 2 reads, AGE EvolutionEvent | Yes, in worker thread |
| score | 3–4: idempotency lookup and governed decision | 1 read + 1 write, AGE Decision | Yes, in worker thread |
| verify | 1–3: route lookup, verified-history duplicate check, scorer lookup | 3 reads, Decision/Outcome | Yes; sync route uses threadpool |
| verify | 4: commit outcome/status | 1 write, Decision/Outcome | Yes |
| verify | 5–10: governed receipt chain checks, create and read-back | 5 reads + 1 write, EvidenceReceipt | Yes; receipt bundle uses its own transaction |
| verify | 11–20: counts, history, archive check/write, conservation inputs | 9 reads + 1 write, Decision/Outcome | Yes |
| verify | 21–28: conservation and fingerprint snapshots plus Domain edges | 4 reads + 4 writes | Yes |
| verify | 29–34: decision/history/count and centroid checkpoint with lineage | 4 reads + 2 writes | Yes |
| verify | 35–38: response conservation inputs | 4 reads | Yes |
| learn | 1–9: lookups, outcome, receipt | 7 reads + 2 writes | Yes; sync route uses threadpool |
| learn | 10–16: history, archive check and conservation inputs | 7 reads | Yes |
| learn | 17–30: conservation/fingerprint/checkpoint with lineage and their input reads | 8 reads + 6 writes | Yes |
| learn | 31–33: variant outcome | 2 reads + 1 write, EvolutionEvent | Yes |
| learn | 34–38: current L5 centroid and SHAPED_BY lineage | 2 reads + 3 writes | Yes |
| learn | 39–47: response counts, current L5 conservation and DK | 7 reads + 2 writes | Yes |

Source lifecycle: `copilot_sdk/backend/scoring_router.py:204`, `:244`, `:306`; `scoring/scorer.py:923`, `:1065`, `:1153`, `:1269`, `:1658`, `:2281`; Purchasing `routers/verify_router.py:75`. The scorer's governed snapshots and router's L5 state are explicitly distinct contracts (`scoring_router.py:317`), not safe-to-delete duplicate calls. Receipt/checkpoint transactions are local boundaries, not one transaction around the whole HTTP operation. Outcome persistence, in-memory mutation, projections, and optional artifact persistence can fail at different times. Some persistence exceptions are logged and skipped (`scoring_router.py:679`, `:799`).

These are branch-dependent budgets, not universal constants. Archive work, periodic evolution, first-time nodes and conflict handling change counts. The older claim of seven writes per score describes another path/version. In this active path, selection reads dominate score; decision persistence is one lookup plus one creation. A threadpool releases the event loop but does not eliminate scorer locks, synchronous graph bridges, or limited downstream capacity.

## Middleware Cost Stack (per copilot)

Measured 20 paired requests to an identical small JSON route in the real middleware stack and a bare FastAPI route. The median paired difference estimates incremental middleware cost, not all HTTP overhead. SOC/S2P use the registered middleware on a measurement app without startup; SOC explicitly uses the same local demo auth setting as `demo.py:1015`. These samples do not benchmark authenticated production JWT/SAML processing or large claim-body rewrites.

| Copilot | Outer → inner application middleware | Paired added median | Reads/rebuilds body? |
|---|---|---:|---|
| Purchasing | direct-TestClient seed hook → evidence → CORS → tenant | **0.359ms** | Evidence rewrites successful JSON only for eight claim prefixes; score gets headers only |
| Trading | CORS → seed hook → invalidation headers → evidence → tenant | **0.513ms** | Selected claim responses only |
| DataOps | evidence headers → seed hook → CORS → tenant | **0.362ms** | These layers add headers/request context; no equivalent claim JSON rewrite |
| SOC | PII annotation → auth → CORS | **0.421ms** | PII middleware is header-only; redaction moved to handlers despite stale module prose |
| S2P | invalidation headers → CORS | **0.569ms** | Header-only; optional AuthMiddleware is off in this local configuration |

Common framework exception/error handling exists in both sides of the comparison. Reproduction/artifacts: `scripts/design_drift_backend_probe.py`, `logs/design_drift_{purchasing_before,trading,dataops,soc,s2p}.json`. Full/bare medians in milliseconds: P 1.913/1.467, T 2.231/1.314, D 1.262/0.952, SOC 3.052/2.625, S2P 3.656/3.279. Paired differences need not equal the difference between those independent medians.

Sources: Purchasing `main.py:455`, `services/purchasing_control.py:98`; Trading `main.py:330`, `:474`, `:621`, `:666` and `services/claim_gate.py:158`; DataOps `main.py:586`, `:905`, `:911`; `copilot_sdk/tenant_middleware.py:17`; SOC `../gen-ai-roi-demo-v4-v50/backend/app/main.py:67` and `middleware/pii_redaction.py:28`; S2P `../s2p-copilot/backend/app/main.py:270`. Purchasing's body buffering/parsing/metadata injection/re-serialization (`purchasing_control.py:115`) has O(response size) memory/CPU and changes streaming semantics. Do not remove evidence to optimize sub-millisecond header overhead. Moving claim decoration into typed response construction belongs to the response-ownership redesign.

## Unbounded Growth Inventory

Eight growth categories were found. A returned-list LIMIT is not a retention policy. No historical graph records were deleted in this audit.

| Entity family | Growth mechanism / evidence | Existing bound | Required policy |
|---|---|---|---|
| Proof events | UUID per `GraphProofLedger.record`, `evolution/graph_store.py:270` | Read limit only; earlier prompt stopped replay-on-GET | Stable semantic identity, retention tiers and audited archival |
| Evolution registrations/status/outcomes | Event append on status and outcome, `graph_store.py:162` | Adapter caps a query, not the stored history | Durable current-state projection plus paged complete history |
| Decisions/outcomes and their edges | Each score/learn; `scoring/scorer.py:429`, `:1065` | `_maybe_archive(keep_recent=800)`, `:2395`, only marks active decisions archived | Physical retention must preserve outcome/receipt lineage |
| Receipts/audit chains | Governed outcome receipt per intent | Uniqueness/chain checks; no age expiry observed | Keep legal/evidence requirements; archive verifiably without breaking hashes |
| Fingerprint/conservation/checkpoint snapshots | Learning artifacts per operation/checkpoint, `scorer.py:1269`, `:1658`, `:2281` | Some content IDs deduplicate; no overall retention window | Keep latest state and selected historic milestones |
| JSON metadata and local ledgers | Persistent order/trade records, full-file metadata writes, fallback SQLite proof tables | File locks prevent concurrent corruption, not growth | Paged store rather than ever-larger JSON rewrites |
| In-memory event history / parameterized tab entries | `evolution/ledger.py:25`, `:35`; `state/tab_state_cache.py:183` | Explicit event clear exists; no automatic event or key eviction | Capacity bound or lifecycle owner for each long-lived map/list |
| Failed/replayed outbox rows | `graph/outbox.py:69`, `:118`, `:135` | Durable state/retry tracking; explicit `purge_replayed(before)` at `:141`, no automatic schedule | Schedule successful-row cleanup and define dead-letter capacity/alerting |

The earlier graph audit measured 632,005 nodes, including 571,825 EvolutionEvents; mutable-flow diagnosis counted 571,690 Purchasing proof events. These are historical measurements from the linked reports, not a new count of the changing live graph. That backlog makes repeated event-label scans expensive even though individual decision lookups are fast. The audit does not infer an index plan from elapsed time alone.

Local database inventory at audit start: **29 `.db`/`.sqlite`/`.sqlite3` files, 136,396,800 bytes (130.08 MiB)**, excluding node_modules/tool caches and not including WAL/SHM sidecars. Largest: `copilot_sdk/data/trading.db` 120.39 MiB, app Trading 2.38 MiB, DataOps 1.91 MiB, Purchasing 1.50 MiB. This includes test/legacy/tool databases; their presence does not mean the active AGE backend is using them. Full file/byte list: `logs/design_drift_inventory.json`, reproducible with `scripts/design_drift_inventory.py`.

A separate live sidecar scan found **10 WAL/SHM files, 5,128,600 bytes (4.89 MiB)**; these fluctuate while connections are open. Full list: `logs/design_drift_db_sidecars.json`. No vacuum, purge or checkpoint operation was run to manipulate these measurements.

## Scorer Architecture Assessment

`FreshScorerProxy` constructs and retains one scorer lazily behind a per-process RLock (`backend/scorer_proxy.py:17`, `:33`). The current docstring correctly calls it cached; the class name remains misleading. `_close_scorer_store` is intentionally a no-op for the borrowed store. There is no external model-version check or automatic reconstruction when another process learns.

Measured construction against each real selected graph: Purchasing **66.52ms**, Trading **72.96ms**, DataOps **83.61ms**. These measure `CompoundingScorer.from_preset` with evolution/consolidation enabled, not complete application initialization or restoration of every L5/control artifact. App imports in those probes took about 4.81s, 4.00s and 1.02s respectively, a separate startup cost.

Recreating the scorer on every request is therefore neither free nor a demonstrated complete state-restoration mechanism. Centroids, posterior/Welford state, DK, authority/evolution state and invalidation generations need an atomic versioned snapshot. A stateless prediction facade can read a small immutable snapshot cached by version; mutations need a single authority or compare-and-swap transaction. See deferred package D1. SQLite WAL and additional AGE pool connections do not solve stale model state. Sequential browser requests with two workers do not establish safety: request two can use worker two's old scorer after request one changes worker one.

The audit also found a hidden dependency in Trading: `_trust_scorer` inspected score endpoint closure cells to discover its provider. The prior threadpool wrapper changed that closure and the trust route fell back to constructing another scorer. Full Trading testing exposed eleven failures. It now uses the existing explicit `app.state.trading_regime_conditioning` registration (`main.py:469`; `context_router.py:198`) and fails with 503 if unavailable. This restores one owner and avoids silent model substitution.

## Frontend Request Budget (per screen per copilot)

Source inventory covers all 22 screen files under `apps/*/frontend/src/screens` and the seven SOC tab components. Source regex counts are call sites, not request counts: local `getTime`, getter helpers, conditionals, StrictMode and child panels invalidate that shortcut. The browser probe below observes network calls from the whole component tree. Path-level unique counts collapse query parameters and therefore are lower bounds on distinct resources.

`e2e/diagnostics/design-drift-screen-budget.mjs` visits each tab, observes seven seconds, records method/path/status/failure, and includes children. The first screen includes shell mount; subsequent screens reflect navigation in the same page. Empty Trade Detail/Triage states are not equivalent to selecting an entity. This is a request budget observation, not a successful-render assertion or a steady-state upper bound.

Current counts from `logs/design_drift_screen_budget_after.json`:

| Copilot | Screen | Total calls | Unique paths |
|---|---|---:|---:|
| Purchasing | Dashboard | 43 | 34 |
| Purchasing | Order | 10 | 10 |
| Purchasing | Analysis | 15 | 13 |
| Purchasing | Inventory | 16 | 16 |
| Purchasing | Performance | 37 | 24 |
| Trading | Dashboard | 39 | 29 |
| Trading | Log Trade | 4 | 4 |
| Trading | Analysis | 49 | 27 |
| Trading | Performance | 37 | 34 |
| Trading | Journal | 3 | 2 |
| Trading | Trade Detail, no selection | 0 | 0 |
| DataOps | Dashboard | 35 | 25 |
| DataOps | Triage, no selection | 0 | 0 |
| DataOps | Insight | 29 | 20 |
| DataOps | Evidence | 18 | 17 |
| DataOps | Curve | 3 | 2 |
| SOC | Runtime Evolution | 30 | 14 |
| SOC | SOC Analytics | 20 | 10 |
| SOC | Alert Triage | 11 | 6 |
| SOC | Compounding | **54** | 23 |
| SOC | Executive Narrative | 8 | 4 |
| SOC | S2P Preview | 34 | 17 |
| SOC | Evidence Room | 12 | 6 |
| S2P | Dashboard | 24 | 10 |
| S2P | Exception Triage | 9 | 5 |
| S2P | Insight | 17 | 9 |
| S2P | Evidence | 27 | 14 |
| S2P | Suppliers | 12 | 7 |
| S2P | Performance | 18 | 9 |

The observed maximum after these fixes is **54, SOC Compounding**. A second populated-detail probe could not locate a uniquely named card with its selectors (`logs/design_drift_selected_budget_after.json`); it does not prove those screens are broken or cheap. Code gives Trade Detail two parallel history/metadata reads followed by an optional ticker (`TradeDetailScreen.tsx:101`), and selected DataOps Triage seven initial reads followed by up to three context/similar reads (`TriageScreen.tsx:105`), before any additional child requests. These selected-state budgets are source-derived, not measured totals.

Historical pre-fix browser counts from mutable-flow diagnostics are preserved for comparison: Purchasing Dashboard 68/34, Order 18/10, Analysis 36/13, Inventory 34/16, Performance 56/24; Trading Dashboard 57/29, Log 8/4, Analysis 61/27, Performance **100/34**, Journal 6/2; DataOps Dashboard 60/25, Insight 47/20, Evidence 40/17, Curve 6/2. Values are total / unique paths in seven seconds. These historical runs are not relabeled as this audit's after numbers. Request counts include attempted/aborted requests; StrictMode cleanup and navigation cancellation are not automatically backend failures.

The high-count screens were traced through their children. Purchasing Dashboard's effect runs six parallel reads, then per-item waste requests (`DashboardScreen.tsx:103`, `:110`, `:133`); it waits on variants even to show core items. Performance's three top-level reads expand through diagnostic/beat panels. Trading Performance starts only three top-level reads (`PerformanceScreen.tsx:77`) but its child panels account for the historical 100 calls. DataOps Dashboard combines alert/process context with global SC and evidence panels. SOC/S2P have separate fetch ownership and are observed, not modified by the new helper.

Implemented coalescing shares only *overlapping* same-base/path/timeout GETs in Purchasing/Trading/DataOps `src/api.ts`; normalized objects remain separate per caller. Entries are removed on completion or failure, and POST boundaries clear them. There is no completed-value cache or model freshness promise. Raw SDK panel fetches and DataOps raw API wrappers remain separate owners. The architectural next step is explicit page resources and lazy optional diagnostics, not another cache layered over inconsistent ownership.

## Test Architecture Risks

All **47 Purchasing tests** pay the shared screen-readiness and backend fixture cost. **Nine** initiate score (five in order, four in flows); five of these verify. Their model-dependent follow-up assertions are at risk under multi-worker learning. Shared persistent decisions permit some cross-worker lookups, but that does not make learned centroids/control state coherent. Tests create fresh pages, not fresh backend domains.

`e2e/fixtures/copilot-fixture.ts:47` checks health per test and warms fingerprint/conservation; failures are swallowed for the warm calls and health failure skips a test. The retries can spend 25s in request timeouts plus 15s backoff. `helpers/ui.ts:43` waits for the screen and all loading panels; page tests commonly load Dashboard before the actual target. Global setup also warms frontends outside the selected test's domain. These are runtime costs not covered by unit-test success.

Two `flows.spec.ts` tests waited 15s for `/api/learn` while Confirm calls `/api/purchasing/verify`, then caught the timeout as null: **30s of guaranteed avoidable waiting across two passing tests**. The new helper installs the exact verify POST waiter before the click and asserts the HTTP result. The lifecycle test also waits for completed confirmation instead of accepting in-progress copy. No timeout was increased; no backend failure was hidden to obtain a pass.

Readiness markers can also indicate completed *error handling*, and some broad text assertions accept loading or empty content (`helpers/ui.ts:49`, existing flow navigation assertions). In the audit's first after probe, cold Dashboard ended at 12.75s with all 19 API calls aborted at about 10s; a marker alone did not certify useful content. Later warmed pages reached readiness in 1.95–2.85s. This cold failure is unresolved and must not be omitted from performance reporting. Earlier work recorded intermittent Windows connection resets too; there is insufficient evidence here to call them the same root cause.

Static timeout/waiter inventory at audit start spans 173 spec files, with **58 `waitForResponse` sites across 23 files**, in `logs/design_drift_inventory.json`. It is a screening inventory, not a claim that every matching timeout is defective. Flow waits, route-specific content checks, per-test request counts and backend traces must be checked together. A passing test duration of 19s never establishes that score itself took 19s.

## Async/Sync Analysis

The AST inventory found **379 route declarations, 22 async** (16 DataOps, six SDK), under SDK backend and app Python sources. Async is not automatically faster: synchronous SQLite, AGE bridging, file reads, or waiting on a threading lock inside `async def` blocks the event loop. Conversely FastAPI dispatches ordinary sync routes in the threadpool; one Uvicorn worker does not mean all those requests execute serially.

The previously fixed SDK score handler awaits stable context, then runs locked synchronous scoring/invalidation in `run_in_threadpool` (`scoring_router.py:204`). Most SC/graph-backed routes are sync and already use threadpool dispatch. DataOps graph handlers await `DataOpsGraphClient`, whose AGE async client offloads synchronous driver work. The remaining concrete violation found here was the recommendation handler's direct synchronous `store_variants()` scan after its awaited alert read; it now awaits `run_in_threadpool(store_variants)` in `apps/dataops/backend/app/ae_router.py`.

Other async work needs explicit budgets: DataOps enterprise health performs several sequential connector reads/checks; fallback JSON reads and auth XML/crypto can execute synchronously. These are source-level risks, not measured causes of Purchasing's latency. CPU-bound work, per-process scorer locks, AnyIO thread capacity, and AGE pool size can still bound throughput after thread offloading. Browser abort is not cooperative cancellation of already-running sync database work. The system needs queue-time/lock-time/query-count spans and bounded request concurrency, not a blanket conversion of every handler to async.

## Ranked Findings (P1→P3 with evidence)

| ID | Severity | Structural finding / evidence | Effort and disposition |
|---|---|---|---|
| F01 | P1 | Cached model has no cross-worker revision; `scorer_proxy.py:33` | D1, 3–5 days, >200 lines |
| F02 | P1 | Outcome, learned state, governed artifacts and L5 state have different commit/failure boundaries; 38/47-call trace | D2, 4–7 days, >200 lines |
| F03 | P1 | Variant status depended on opposite AGE/SQLite event orders; `evolution/graph_store.py:54` | Fixed, <60 production lines; ~0.5 day with focused validation |
| F04 | P1 | Trading discovers provider from endpoint closure and silently substitutes a scorer; `context_router.py:198` | Fixed, <20 production lines; ~0.25 day; 1,302 backend tests pass |
| F05 | P2 | Summary loops make repeated complete event reads; 14 calls/1,999ms | Fixed, <15 production lines; ~0.25 day, single fresh summary snapshot |
| F06 | P2 | Multiple components/StrictMode issue identical overlapping reads; historical 100 calls on Trading Performance | Partly fixed, <100 production lines total; ~0.5–1 day; ownership redesign D4 remains |
| F07 | P2 | Dashboard-first navigation and global diagnostic readiness make optional work critical | D4, 3–5 days, >200 lines across screens |
| F08 | P2 | Read LIMIT/archive flags mistaken for retention; eight growth families | D3, 3–5 days, >200 lines, includes safe migration |
| F09 | P2 | Complete-history consumers silently receive adapter-capped windows: `_events` requests 10,000, AGE clamps to 1,000 | D3, paged projections and explicit completeness contract |
| F10 | P2 | Sync graph scan inside DataOps async recommendation | Fixed, <5 production lines; ~0.1 day; 336 backend tests pass |
| F11 | P2 | Wrong-endpoint timeouts swallowed in two passing flow tests | Fixed, <20 test lines plus replacement/deletion; ~0.25 day, real verify assertion |
| F12 | P2 | Fresh browser pages share mutable backend/load; retries and warmups amplify outstanding work | D5, 2–4 days, >200 lines for isolated fixture/perf harness |
| F13 | P3 | Evidence middleware owns response shape and buffers selected bodies; tiny measured header cost | D4 response ownership; do not remove evidence headers |
| F14 | P3 | Build/naming/documentation contracts diverge from actual dependencies; missing Vite types, stale PII prose and legacy paths | SDK frontend types fixed in one config line (~0.1 day); naming/documentation drift recorded |
| F15 | P3 | Unit gates do not enforce query/request budgets or per-screen tail latency | D5, shared performance gates and trace artifacts |
| F16 | P3 | Error-complete readiness and broad text checks can hide cold request failures | D5, typed loaded/error state and content assertions; cold failure unresolved |

AGE cap evidence: `../ci-platform/ci_platform/graph/age_graph_store.py:361`, `:3415`, versus `copilot_sdk/evolution/graph_store.py:22`. The summary fix reduces redundant reads; it does not claim to repair historical completeness or add an event index.

## Fixes Implemented

1. **One fresh summary snapshot.** `PromptVariantEvolver.get_summary` uses the existing optional `selection_snapshot` capability once; in-memory stores retain their path. The new real SQLite regression observes two summary SELECTs and sees an outcome written by another connection on the next call. Its before run failed with 13 reads versus expected two. Purchasing's HTTP route adds one history query, so its endpoint budget is three, not two. Final actual AGE profile: **14 → 3 queries, 1,999 → 670ms** (`logs/design_drift_purchasing_io_after.json`).
2. **Overlap-only GET sharing.** Added `frontend/requestCoalescing.ts`, used by three app API clients. Real HTTP tests verify 12 concurrent consumers produce one call, later calls are fresh, failures are evicted, and reads spanning a POST cannot join an earlier generation. Normalization happens per consumer; timeout includes body consumption. No API response schema changed.
3. **DataOps async boundary.** Only its synchronous variant-store read is offloaded. No connector response or recommendation policy changed.
4. **Latest variant by timestamp.** ISO and numeric timestamps are supported; newest status wins regardless of adapter order. Unknown/equal timestamps retain the prior last-seen fallback because inventing chronology would be unsafe. Real SQLite status transitions are exercised in both row orders.
5. **Truthful Confirm waits.** Verify response is awaited and checked; the two nonexistent learn waits and swallowed timeout paths are removed. The first lifecycle also checks completed confirmation.
6. **Explicit Trading scorer ownership.** Trust uses its existing app-state provider. Missing provider is a 503, not a different reconstructed model. Test helpers use the same explicit registration instead of closure inspection.
7. **Standalone SDK frontend type context.** Added `vite/client` to `copilot_sdk/frontend/tsconfig.json`; the SDK's own typecheck now understands the existing `DayZeroPanel` use of `import.meta.env`. Host app typechecks had supplied these types indirectly and hidden the standalone configuration defect. No runtime code or build output changed.

Every group adds fewer than 200 implementation lines. The shared GET change crosses the SDK and three copilots; its behavior and tests are reviewed as one cross-copilot mitigation. The diagnostic scripts are measurement tooling, not per-request instrumentation left enabled in the server.

### Changed files

Source hashes were compared with `logs/design_drift_baseline_hashes.json`; no git diff was used. **20 source/config/test/tooling/documentation files**:

- `copilot_sdk/evolution/prompt_evolver.py`
- `copilot_sdk/evolution/graph_store.py`
- `copilot_sdk/frontend/requestCoalescing.ts` (new)
- `copilot_sdk/frontend/tsconfig.json`
- `apps/purchasing/frontend/src/api.ts`
- `apps/trading/frontend/src/api.ts`
- `apps/dataops/frontend/src/api.ts`
- `apps/dataops/backend/app/ae_router.py`
- `apps/trading/backend/app/context_router.py`
- `apps/trading/backend/tests/test_trust_analysis.py`
- `tests/evolution/test_summary_snapshot.py` (new)
- `tests/evolution/test_variant_event_order.py` (new)
- `e2e/purchasing/flows.spec.ts`
- `e2e/diagnostics/request-coalescing.test.ts` (new)
- `e2e/diagnostics/design-drift-page-probe.mjs` (new)
- `e2e/diagnostics/design-drift-screen-budget.mjs` (new)
- `scripts/design_drift_inventory.py` (new)
- `scripts/design_drift_backend_probe.py` (new)
- `docs/quality/design_drift_audit.md` (new)
- `docs/session_state.md` (new)

Required `graphify update .` refreshed generated `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`, and `graphify-out/manifest.json` (plus root marker/cache metadata). It completed with 21,375 nodes and 40,552 edges; HTML visualization was skipped by its configured size limit. Logs, traces, PID/runtime files and database changes from authorized real writes are diagnostic/runtime artifacts, not source fixes.

### Verification and before/after measurements

| Gate | Result |
|---|---|
| Changed Python mypy | **All nine files pass**, each with `--follow-imports=skip --no-error-summary`. Trading files run from their backend import root; running them from SDK root initially produced unresolved `app.*` imports. `logs/design_drift_mypy_final.log` |
| Purchasing full backend | **714 passed, 1 skipped, 0 failed**, 372.49s |
| Trading full backend | **1,302 passed, 0 failed**, 200.13s after explicit provider fix; initial audit run exposed 11 failures |
| DataOps full backend | **336 passed, 0 failed**, 97.41s |
| Evolution targeted suite | 229 passed before final timestamp-test correction; final two new regressions **2 passed**, 0.51s |
| SDK full root | **3,354 passed, 2 failed**, 865.43s. One new test had been collected before its ISO timestamp conversion correction; corrected test passes. Existing `test_no_incorrect_rl_naming` still fails only on `docs/design/product_integrity_execution_strategy_v3_0.md:38`, `:839`, `:1480`, `:1506`; isolated recheck after this report confirms that same failure. No all-green full rerun is claimed |
| Coalescing real HTTP tests | **2 passed** |
| P/T/D frontend, standalone SDK frontend and E2E typechecks | **All five pass**, final `npx tsc --noEmit` checks; standalone SDK required the one-line type configuration fix |
| Purchasing 47 browser tests | **47 passed, zero failed/skipped/flaky**, 204.669s runner / 206.496s wall; `logs/design_drift_purchasing_pw.json` |
| Trading/DataOps dashboard regressions | Trading **10 clean passes**; DataOps **25 clean + one flaky pass**; zero final failures. Combined runner 96.487s. `logs/design_drift_cross_pw.json`; initial DataOps error retained in `logs/design_drift_dataops_cold_trace.zip` |
| Direct score and endpoint profile after | **291 / 307 / 311ms**, median **307ms**, 496-byte HTTP 200 bodies; concurrent with six GETs **380ms**, all seven responses 200. Verify **574ms**, learn **618ms**. `logs/design_drift_http_after.json` |
| Package installation/import contract | Failed before installation: existing `setuptools.backends._legacy` build backend cannot be imported. `pip install . --no-deps --no-build-isolation`, `logs/design_drift_package_gate.log`; no package configuration changed |

Before fresh-page readiness probe (separate fresh context, Dashboard then target, real fixture-style warm calls): Dashboard 15.41s, Order 8.09s, Analysis 8.61s, Inventory 14.49s, Performance 12.00s. Initial after probe: cold Dashboard 12.75s with 19 aborted requests, then warm Order 1.95s, Analysis 1.95s, Inventory 2.85s, Performance 2.83s. These include all panel readiness and navigation, are not individual Playwright test durations, and do not establish a cold p95 SLA. Artifacts: `logs/design_drift_pages_before_complete.json`, `logs/design_drift_pages_after.json`.

| Purchasing spec | Tests passed | Sum of test durations after | Supplied earlier suite baseline |
|---|---:|---:|---:|
| Dashboard | 10 | 27.674s | 97.7s |
| Order | 9 | 32.117s | 98.0s |
| Analysis | 6 | 24.097s | 57.0s |
| Inventory | 3 | 13.992s | approximately 30s |
| Performance | 5 | 21.063s | 56.0s |
| Flows | 14 | 80.966s | 235.5s |

The after column sums per-test results from one combined run; the earlier numbers are separate suite runs, so their setup overhead is not identical. Final Purchasing mean is 4.253s, nearest-rank p95 6.919s, max 11.414s; wall average is 4.394s. Target average is met in this run; tail latency remains work.

The cross-copilot flaky test failed to find Pipeline Status after its dashboard error state reported an aborted signal. Fixture fingerprint/conservation had succeeded in 12/60ms, but all 21 browser API attempts (including raw SC fetches outside the coalescer) aborted. It passed on retry in 1.631s. This is consistent with the broader cold-browser symptom but does not identify its root cause or prove it predates this patch. The trace is retained; timeouts/retries were not increased. Consequently the audit does **not** issue an unconditional platform-wide “zero new regressions” certification.

## Fixes Deferred (with design)

**D1 — Versioned model state / mutation authority (400–700 lines, 3–5 engineering days).** Define a domain+tenant model revision and immutable snapshot containing centroids plus sufficient statistics, posterior, DK and control/evolution state. Commit via compare-and-swap or one domain mutation service; cache prediction snapshots by revision. Persist and restore one complete state contract. Tests must spawn real Windows processes, alternate learn/read, collide writes, and restart during checkpoint publication. Until then retain one worker for mutable demonstrations; a renamed proxy alone is not a fix.

**D2 — One mutation orchestration contract (400–800 lines, 4–7 days).** Give score/verify/learn explicit idempotency keys and result states. Make decision outcome, receipt and model-revision publication atomic where they share AGE; publish secondary/read-model updates through a durable outbox with replay semantics. Reuse one decision and conservation-input snapshot within the operation. Keep governed evidence and current L5 projections distinct until consumers migrate. Inject failures at each real transaction boundary and verify restart/retry does not duplicate learning. Deleting redundant-looking writes without this migration is incorrect.

**D3 — Event projections, pagination and retention (300–600 lines plus migration, 3–5 days).** Add protocol capabilities for paged history and direct aggregate/current-state queries; specify order and completeness. Preserve event-time tie breakers. Build current variant/category stats from complete history with a watermark, then increment on new outcomes. Measure AGE plans before choosing property indexes. Define policy by entity/evidence tier; export/archive with hash/lineage verification before deletion. Add bounded in-memory/tab-cache policies and outbox success/dead-letter management. A LIMIT increase or unconditional old-event purge is not this fix.

**D4 — Page-owned data and response contracts (350–650 lines, 3–5 days).** Declare required core resources per screen; fetch them once, independently render optional diagnostics, and mount expensive panels on demand. Support direct target-screen URLs so tests need not load Dashboard first. Share resource loaders between shell/panels/screens, including raw SDK fetches; carry mutation revisions through invalidation. Publish core score immediately while optional similar matches load independently. Move claim metadata into typed response construction where feasible, preserving evidence tier and headers. Test render, unmount/cancellation and mutation refresh across all three clients; keep the new overlap helper as a narrow interim optimization.

**D5 — Performance and reliability contracts (300–500 lines, 2–4 days).** Introduce isolated test-domain fixtures with one per-worker readiness check, explicit required-data/error state, and response predicates that expose non-2xx responses. Record backend lock wait, thread queue, graph calls, bytes and browser critical-path timings. Gate warm p95 under 5s per read-only screen and separately budget cold startup and mutation workflows; no single average should conceal a cold failure. Run a sequential 47-test budget and controlled read/write concurrency on one worker in CI. Preserve failed traces, forbid swallowed expected-response timeouts, and profile cold browser resets before changing limits.

## Recommended Architecture Changes

Keep mutation ownership explicit and use immutable versioned read models. Enforce bounded query/request budgets at integration boundaries: three graph calls for the current Purchasing variants route, one overlapping request per identical API-client key, and a separately reviewed persistence budget per mutation branch. One model revision should identify the read state shown by fingerprint, conservation and learning responses.

Do not add workers as a substitute for model coherence, treat all evidence writes as disposable, or claim middleware removal saves seconds based on HTTP-minus-handler timing. Retain the previous IPv4, JSON, SC and score-threadpool fixes; the current changes complement them. No production data retention or authentication policy was changed by this audit.

## Estimated Timeline

The seven bounded groups are implemented in this task. Complete D1/D2 first for mutable correctness (about 7–12 days together, with some overlap), then D3/D4 for sustainable performance (6–10 days), with D5 instrumentation starting alongside D4 (2–4 days). Allow roughly **3–5 engineering weeks** including migration/review and Windows process/concurrency testing. These are scope estimates, not measured coding durations or guaranteed delivery dates.
