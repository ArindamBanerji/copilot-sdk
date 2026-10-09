# Judgment Memory Design Compliance Audit

**Document version:** 2  
**Date:** 2026-10-05  
**Scope:** Current copilot-sdk source and app wiring, including the files named in the audit request and directly relevant implementations/callers.  
**Canonical rules:** [design_principles_v2.md](design_principles_v2.md), P1–P10.

## Section A: Executive summary

The audit found **9 violations: 8 P1 critical and 1 P2 high**. The known S2P experiment violation is confirmed. Newly confirmed issues include a non-rolling conservation accuracy calculation, retained SQLite/DualWrite graph implementations, three production apps persisting cross-copilot signals in SQLite, graph-derived state held in query-serving caches, and transfer execution that can apply generated demo patterns as if they were validated memory artifacts. V-07 is P1 because P8 directly prohibits query-serving caches.

The app composition roots otherwise create one selected store and inject it into their scoring and graph consumers. In production, GraphConfig requires the authorized shared AGE graph; the factory selects only memory or AGE. These compliant boundaries do not offset the specific violations below. `persistence_outbox.py` and `graph/outbox.py` are not violations: they buffer pending writes and do not serve memory reads.

| ID | Severity | Principle(s) | Summary |
|---|---|---|---|
| V-01 | P1 | P1, P8, P9 | S2P reasoning experiment creates a separate InMemoryGraphStore per governed arm. |
| V-02 | P1 | P4 | Conservation uses all-time accuracy for `q`, not the required rolling 400 verified decisions. |
| V-03 | P1 | P1, P8 | SQLiteGraphStore and DualWriteStore implementations remain importable; migration CLI still constructs SQLiteGraphStore as a GraphStore. |
| V-04 | P1 | P1, P2, P8 | Trading, Purchasing, and DataOps wire cross-copilot signal routes to persistent SQLiteSignalStore. |
| V-05 | P1 | P1, P5, P8 | Persistent outcome, promotion, variant, proof, and frozen-judgment stores retain SQLite/file fallbacks outside the graph. |
| V-06 | P1 | P1, P4, P8 | CompoundingScorer retains a cross-request verified-decision cache used by conservation and learning paths. |
| V-07 | P1 | P1, P2, P8 | DI answers, scoring context, and conservation status can be served from query/materialization caches instead of fresh governed reads/context resolution. |
| V-08 | P2 | P1, P2 | Demo preseed creates one InMemoryGraphStore per domain and represents cross-copilot signaling as a detached payload. |
| V-09 | P1 | P2, P4, P10 | Transfer can apply synthetic demo patterns and mark them validated; persisted artifact omits source conservation context. |

## Section B: Violations table

### V-01 — Per-arm in-memory stores in the S2P reasoning experiment

**File:** `apps/s2p_differentiation/engine.py`  
**Lines:** 178–186, 278–280  
**Principle:** P1, P8, P9  
**Severity:** P1

`_make_scorer()` unconditionally creates `InMemoryGraphStore(domain="s2p")` with the offline/development profile. `run_three_arms()` calls it separately for `ci` and `hand`, so the arms do not exercise the durable shared AGE graph or the same graph identity. The results are therefore scorer-local algorithm results, not evidence about integrated reasoning or cross-memory behavior. The baseline has no graph, and the synthetic cross-copilot capabilities are not represented by the experiment's graph.

**Current code:**

```python
def _make_scorer(*, enable_rl: bool) -> CompoundingScorer:
    store = InMemoryGraphStore(domain="s2p")
    return CompoundingScorer.from_preset(
        "s2p", graph_store=store, enable_rl=enable_rl,
        evolve=False, profile="development",
    )

ci = _make_scorer(enable_rl=True)
hand = _make_scorer(enable_rl=False)
```

**Design fix:** Build one AGE GraphStore for the run from explicit production-grade AGE configuration and inject that same store object into every graph-backed arm. Add a scorer storage-domain/namespace parameter so each arm reads and writes only its own domain namespace inside the same physical AGE graph; do not create per-arm store objects or caches. For example, after adding `storage_domain` to `CompoundingScorer.from_preset`:

```python
shared_store = create_graph_store(config=experiment_graph_config)
ci = CompoundingScorer.from_preset(
    "s2p", graph_store=shared_store, profile="production",
    storage_domain=f"s2p:{run_id}:ci",
)
hand = CompoundingScorer.from_preset(
    "s2p", graph_store=shared_store, profile="production",
    storage_domain=f"s2p:{run_id}:hand",
)
```

The run must fail closed when AGE is unavailable; it must not fall back to memory. All arms must use the same generator stream and the configured shared graph. Use a run ID in stored evidence and perform cleanup only through an explicit, scoped graph maintenance operation.

**Blast radius:** `engine.py`, `CompoundingScorer.from_preset` and its store-domain use, S2P experiment tests/scripts, AGE test/deployment configuration, experiment cleanup tooling.  
**Dependencies:** None; implement before claiming reasoning-quality experiment results.

### V-02 — Conservation `q` is lifetime accuracy, not rolling-400 accuracy

**Files:** `copilot_sdk/scoring/scorer.py`; `copilot_sdk/backend/conservation_utils.py`  
**Lines:** `scorer.py:2388–2426, 2963–2979`; `conservation_utils.py:61–100, 315–350`  
**Principle:** P4  
**Severity:** P1

The paper defines `q` over a rolling window of 400 verified decisions while `V` remains the verified-decision count. `_conservation_pause()` currently receives `correct` and `verified` from `_conservation_stats()` and computes `q = correct / verified`; `_conservation_stats()` counts all verified decisions. `compute_conservation_status_payload()` independently uses the same all-time ratio. The scorer does calculate a 400-decision rolling value for checkpoint metadata, but that value does not drive the primary conservation signal. Recent deterioration can therefore be diluted by old outcomes when the gate evaluates `alpha * q * V`.

**Current code:**

```python
q = correct / verified
theta_min = compute_theta_min(category_coverage, verified)
conservation_signal = category_coverage * effective_q * verified
```

and:

```python
verified = len(decisions)
correct = sum(1 for decision in decisions if _is_correct_decision(decision))
```

**Design fix:** Preserve lifetime `V` and category coverage, but compute `q` from the most recent `QUALITY_WINDOW_SIZE == 400` verified, non-benchmark decisions, in deterministic chronological order. Use the same helper for scorer gates and the status API so UI/reporting cannot disagree with the gate. If the graph cannot provide enough verified records or ordering is invalid, return the existing fail-closed unavailable/calibration state; never substitute lifetime accuracy. Keep `theta_min` computed from the canonical `alpha` and lifetime `V` calibration.

```python
def rolling_verified_accuracy(
    decisions: Sequence[Mapping[str, Any]], window_size: int = QUALITY_WINDOW_SIZE,
) -> tuple[int, float | None]:
    recent = [d for d in decisions if _is_verified_decision(dict(d))][-window_size:]
    if not recent:
        return 0, None
    return len(recent), sum(_is_correct_decision(dict(d)) for d in recent) / len(recent)
```

Pass the returned accuracy into `check_conservation(alpha, q, V, theta_min)` and its API projection. Do not redefine `V` as the window length.

**Blast radius:** scorer pause/checkpoint logic; conservation status route and utilities; conformance and boundary tests for 399/400/401 outcomes and a recent-degradation sequence.  
**Dependencies:** None; keep as one shared semantic fix so both gate and status use identical math.

### V-03 — Retired SQLite and dual-write graph backends remain available

**Files:** `copilot_sdk/graph/sqlite_store.py`; `copilot_sdk/graph/dual_write_store.py`; `copilot_sdk/migrate/__main__.py`; `copilot_sdk/graph/outcome_service.py`  
**Lines:** `sqlite_store.py:393+`; `dual_write_store.py:19, 36–76`; `migrate/__main__.py:91–110`; `outcome_service.py:20–24`  
**Principle:** P1, P8  
**Severity:** P1

The factory's `_VALID_BACKENDS` is correctly limited to `{"memory", "age"}`, but the complete SQLiteGraphStore and DualWriteStore implementations remain directly importable. The migration CLI constructs SQLiteGraphStore as a general GraphStore source. This keeps a third graph-store implementation and dual-write architecture in the package, outside the declared two-backend protocol boundary. `ProtocolV2OutcomeService` also has a stale docstring claiming the canonical V store is SQLite, which perpetuates the wrong persistence model.

**Current code:**

```python
class SQLiteGraphStore:
    """SQLite-backed GraphStore that owns decisions, outcomes and graph tables."""
```

```python
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
sqlite_store = SQLiteGraphStore(args.source, domain=args.domain)
reconciler = ArchiveReconciler(sqlite_store, age_store, args.domain)
```

**Design fix:** Preserve data cutover as a migration concern, but remove the SQLite object from the GraphStore role. Replace the migration CLI's use of SQLiteGraphStore with a read-only, migration-scoped source reader that yields typed archived rows from the legacy file; the reader must not implement or be accepted as GraphStore. Keep `sqlite3` only inside migration code needed to read historical sources and in the explicitly exempt outboxes. After migrating all call sites/tests, delete `sqlite_store.py` and `dual_write_store.py`, remove stale exports/imports, and correct the OutcomeService docstring to say the injected GraphStore is canonical and the outbox only buffers pending writes.

```python
class LegacySQLiteArchiveReader:
    """Read-only migration source; not a GraphStore and never used for runtime writes."""
    def iter_verified_records(self, domain: str) -> Iterator[ArchivedDecision]:
        ...  # SELECT and validate legacy rows; no GraphStore methods
```

The reconciler should consume an `Iterable[ArchivedDecision]` and write only to the AGE GraphStore. Once source data is cut over and verified, retire the reader under the separate data-cutover plan; do not re-enable SQLite as a selectable backend.

**Blast radius:** migration reconciliation/verification, old backend-specific tests, package exports, dependency docs, graph factory regression tests.  
**Dependencies:** Convert migration CLI and all remaining direct imports before deleting the implementation files. Historical source data cutover remains a separately verified operation.

### V-04 — Cross-copilot signals use a separate persistent SQLite store

**Files:** `copilot_sdk/backend/signal_store.py`; `copilot_sdk/backend/cross_signal_router.py`; `apps/trading/backend/app/main.py`; `apps/purchasing/backend/app/main.py`; `apps/dataops/backend/app/main.py`  
**Lines:** `signal_store.py:24+`; `cross_signal_router.py:58–86`; app mains at Trading 579, Purchasing 930, DataOps 936  
**Principle:** P1, P2, P8  
**Severity:** P1

The cross-copilot signal route is wired in all three apps to `SQLiteSignalStore(shared_signal_path())`. The router also defaults to constructing SQLiteSignalStore when no store is injected. These signals are cross-copilot semantic/episodic facts, but they live and are queried outside the shared graph, so graph traversals cannot join them with decisions, entities, judgment state, and conservation state.

**Current code:**

```python
signal_store = store if store is not None else SQLiteSignalStore(...)
active, count = signal_store.page(...)
```

```python
create_cross_signal_router(SQLiteSignalStore(shared_signal_path()))
```

**Design fix:** Make the route require the selected shared `ProtocolV2GraphStore`; remove its SQLite default. Implement the signal projection as a graph adapter over evolution/signal events on that same store (or existing graph signal methods), with event type, stable signal ID, source/target domains, timestamps, TTL, and payload recorded as inspectable graph properties. Reads must traverse/query the graph and apply target/source/TTL filtering there. Wire each app's existing `selected_graph_store_factory` result into the route.

```python
def create_cross_signal_router(store: ProtocolV2GraphStore) -> APIRouter:
    signal_store = GraphSignalStore(store)
    ...
```

No independent SQLite database, event bus, or cache may serve these signal reads. Keep `PersistenceOutbox` only for pending writes during a graph outage; if a signal write cannot reach AGE, return pending/unavailable according to the existing outbox contract and never read it from the buffer.

**Blast radius:** cross-signal router tests, SDK signal-store tests, three app main wirings, signal ID/TTL contract tests, graph event query tests.  
**Dependencies:** None; coordinate with V-03 if signal events depend on ProtocolV2 methods during backend retirement.

### V-05 — Authoritative outcomes and learned state have SQLite/file fallbacks

**Files:** `copilot_sdk/outcome/ledger.py`; `copilot_sdk/promotion/core.py`; `copilot_sdk/evolution/variant_store.py`; `copilot_sdk/twin/store.py`; `apps/purchasing/backend/app/services/purchasing_control.py`; `apps/trading/backend/app/services/claim_gate.py`  
**Lines:** `ledger.py:14–63`; `promotion/core.py:111–165, 220–225`; `variant_store.py:191–237`; `twin/store.py:14–52, 65–108`; `purchasing_control.py:195–218`; `claim_gate.py:131–138`  
**Principles:** P1, P2, P3, P5, P8  
**Severity:** P1

The codebase retains durable non-graph stores for verified outcome receipts (`OutcomeLedger`), promotion/procedural state (`PromotionStore`), variants and outcomes (`SQLiteVariantStore`), and frozen judgment snapshots (`FrozenTwinStore`). PurchasingControl can select SQLite ledgers or JSON snapshots when GraphStore capabilities are absent; TradingPromotionGuard defaults to SQLite when no graph store is supplied; PromotionEngine silently constructs PromotionStore when omitted. These stores can become a second authority for facts already represented by Decision, Outcome, EvolutionEvent, Promotion, or centroid/conservation records in the graph. The SQLite classes are also publicly exported or testable, so the non-graph fallback remains a supported persistence design.

**Current code:**

```python
self.store = store or PromotionStore()
```

```python
self.outcomes = GraphOutcomeLedger(graph_store, "purchasing") if age_events else OutcomeLedger(...)
self.twin = FrozenTwin(GraphFrozenTwinStore(...) if has_save_promotion else FrozenTwinStore(...))
```

**Design fix:** Make production and integrated-app constructors require an injected graph adapter and fail closed when the supplied GraphStore lacks the needed graph protocol. Use the already-present `GraphOutcomeLedger`, `GraphProofLedger`, `GraphPromotionStore`, `GraphVariantStore`, and `GraphFrozenTwinStore` for graph-backed state. Remove SQLite/file fallback branches from app wiring and remove or quarantine the legacy durable classes after their tests/callers are migrated. Unit tests should use explicit in-memory test doubles or the InMemoryGraphStore-backed graph adapters; they must not create durable SQLite authorities. `PromotionEngine` should require a `PromotionStore` interface argument rather than defaulting to SQLite; app factories pass GraphPromotionStore. Retain an explicitly named in-memory implementation only for isolated unit tests if needed.

```python
class PromotionEngine:
    def __init__(self, policy: PromotionPolicy, store: PromotionStoreProtocol) -> None:
        self.policy = policy
        self.store = store
```

For PurchasingControl, type `graph_store_factory` to return `ProtocolV2GraphStore`, require graph proof/outcome/frozen-twin/promotion adapters unconditionally, and surface a clear configuration error when the graph contract is missing. Do not solve this by adding SQLite to the graph or by creating a second database.

**Blast radius:** outcome protocol/processor tests, promotion and variant-store tests, twin persistence tests, Purchasing control service tests, Trading promotion guard tests, exports and app composition roots.  
**Dependencies:** V-03 should remove SQLiteGraphStore before final retirement; graph adapters already available can be used in parallel with V-04.

### V-06 — Cross-request verified-decision cache can stale conservation inputs

**File:** `copilot_sdk/scoring/scorer.py`  
**Lines:** 196; 986, 1163, 1962; 2837–2843  
**Principles:** P1, P4, P8  
**Severity:** P1

`CompoundingScorer` retains `_verified_decisions_cache` across calls. It is invalidated by local scorer paths, but another process or GraphStore client can append a verified outcome without invalidating this object. Subsequent conservation and learning reads can then use stale V/accuracy/coverage evidence even though the graph has newer records. This is a query-serving cache over governed graph memory and can undermine the circuit breaker.

**Current code:**

```python
def _verified_decisions(self) -> list[dict[str, Any]]:
    if self._verified_decisions_cache is None:
        decisions = self._graph_store.get_verified_decisions(self._domain)
        self._verified_decisions_cache = [...]
    return self._verified_decisions_cache
```

**Design fix:** Remove the retained field and invalidation logic. Read verified decisions from the shared GraphStore at each decision/conservation boundary. If one operation needs a consistent snapshot across several calculations, read once at the start of that operation and pass that local immutable snapshot to the helper calls; do not retain it after the operation returns.

```python
def _verified_decisions(self) -> list[dict[str, Any]]:
    rows = self._graph_store.get_verified_decisions(self._domain)
    return [row for row in rows if _is_verified_decision(row)]
```

**Blast radius:** scoring/learning, conservation gates, IKS/fingerprint calculations, tests that currently expect caching, concurrent multi-client store tests.  
**Dependencies:** Coordinate with V-02 because both change conservation input freshness; remove cache first or in the same prompt as the rolling-400 calculation.

### V-07 — Query and score context responses are served from caches

**Files:** `copilot_sdk/di/query_service.py`; `copilot_sdk/backend/scoring_router.py`; `copilot_sdk/backend/conservation_router.py`; `copilot_sdk/backend/response_materializer.py`; all three app `main.py` files  
**Lines:** `query_service.py:54–69, 215–230, 292`; `scoring_router.py:182–208`; `conservation_router.py:46–48, 152–159`; `response_materializer.py:14–31, 37–72, 91–110`; app cache wiring Trading 367–372, Purchasing 549–554, DataOps 697–702  
**Principles:** P1, P2, P8  
**Severity:** P1

`DIQueryService` caches complete graph/data-derived `QueryResponse` objects and returns them on a hit without rerunning its provider. `EntityContextCacheAdapter` supplies prior stable context to scoring requests across requests. `ResponseMaterializer` also caches graph-derived payloads; `conservation_router.status()` returns a materialized conservation response before consulting its live state provider. These are query-serving caches, not request-local memoization; P8 directly prohibits them because they can suppress fresh graph/context reads and prevent current cross-type state from influencing decisions or displayed conservation status. The app mains enable these materializers/cache adapters in integrated request paths.

**Current code:**

```python
cached = self._response_cache.get(cache_key)
if cached is not None and time.monotonic() - cached[0] < self.cache_ttl_seconds:
    return cached_response
```

```python
cached = await entity_context_cache.get_context(...)
if isinstance(cached, dict):
    request.context = {**cached, **context}
```

```python
materialized = _materialized_response(request, "conservation")
if materialized is not None:
    return materialized
```

**Design fix:** Remove response caching for graph-derived query results, entity-context read-through from the scoring path, and graph-derived `ResponseMaterializer` reads from integrated request paths. `conservation_router.status()` must resolve its current state provider and compute status on every request. Execute each read against its source and the shared graph each time; unchanged request-local calculations may be memoized only inside one request and discarded before the next request. Preserve caches only for explicitly static, non-memory configuration that cannot affect graph-derived decisions or answers, and document that boundary.

**Blast radius:** DI query tests (cache hit/expiry/invalidation assertions), scoring and conservation router tests, response materializer tests, three app main dependency wiring, cache metrics/health payload fields.  
**Dependencies:** None; implement after V-04 graph signal wiring if DI providers begin traversing the same signal events.

### V-08 — Demo preseed presents isolated per-domain graphs as one system

**File:** `copilot_sdk/demo/preseed.py`  
**Lines:** 118–137, 224–235, 175–198  
**Principles:** P1, P2  
**Severity:** P2

`preseed_all()` seeds five domains, and `_preseed_domain()` creates a new InMemoryGraphStore for each domain. The cross-copilot signal is returned as a detached dictionary rather than being represented in that graph. This is acceptable only as isolated fixture data; as the integrated multi-copilot demo seed it does not demonstrate shared-graph traversal or a persistent signal artifact.

**Current code:**

```python
def _preseed_domain(self, domain: str) -> CopilotPreseedResult:
    store = InMemoryGraphStore(domain=domain)
    scorer = CompoundingScorer.from_preset(domain, graph_store=store, enable_rl=False)
```

**Design fix:** For offline demo mode, create one InMemoryGraphStore in `DemoPreseeder.__init__` and inject that same instance into every domain scorer; retain domain scoping on each record. Persist the cross-copilot signal as an event/artifact in that same graph and make the demo read it back through the graph API. For an integrated/reasoning-quality demo, use one AGE GraphStore on the authorized shared graph and fail closed if unavailable. Do not describe per-domain in-memory instances as integrated graph behavior.

**Blast radius:** demo preseed tests, all demo bundle/preseed consumers, cleanup/close lifecycle, signal readback tests.  
**Dependencies:** V-04 establishes the graph event shape for shared signals; otherwise independent.

### V-09 — Transfer can apply fabricated demo patterns and marks them validated

**File:** `copilot_sdk/backend/transfer_router.py`  
**Lines:** 290–357, 623–642, 725–758  
**Principles:** P2, P4, P10  
**Severity:** P1

When no registered source pattern is found, `_patterns_for_execute()` synthesizes patterns with fixed `win_rate=0.75`, `confidence=0.8`, and `centroid_delta=[0.03, ...]`, labels them `provenance="demo"`, then the transfer route applies them through `warm_start()` and persists the resulting artifact with `validation_status="validated"`. The graph record stores factor mapping and target conservation status, but does not preserve the source conservation state that authorized the transfer. This is detached synthetic data being presented as a governed transfer.

**Current code:**

```python
if registered:
    return registered, "transfer"
return _demo_patterns_for_mapping(...), "demo"
```

```python
store.write_transfer_pattern(
    ..., validation_status="validated", conservation_status=target_state,
    metadata={"provenance": provenance, "patterns_applied": applied},
)
```

**Design fix:** Remove generated demo patterns from the execution path. If there is no validated, persisted source artifact with inspectable source evidence and factor schema, return a blocked/skipped response without calling `warm_start`. Validate source and target conservation from the shared graph immediately before transfer. Persist the full governed transfer artifact with source/target domains, mapping, source artifact IDs/schema, validation evidence, and both conservation states; only label it `validated` after this validation succeeds.

```python
patterns = _registered_patterns_for_mapping(source_domain, target_domain, mapping)
if not patterns:
    return {"status": "blocked", "reason": "no_governed_source_artifact"}
source_state = _source_conservation_state_from_graph(...)
target_state = _target_conservation_state_from_graph(...)
if source_state != "GREEN" or target_state != "GREEN":
    return _blocked_transfer(source_state, target_state)
store.write_transfer_pattern(
    ..., validation_status="validated", conservation_status=target_state,
    metadata={
        "source_conservation": source_state,
        "target_conservation": target_state,
        "factor_mapping": mapping,
        "source_artifact_ids": [pattern.pattern_id for pattern in patterns],
        "source_validation": "persisted_and_schema_checked",
    },
)
```

The source evidence, mappings, and transfer record must remain in the same shared graph; do not copy detached rules to a private target store.

**Blast radius:** transfer router contract, `TransferPattern`/SharedPatternRegistry validation, GraphStore transfer APIs/readback, tests for no-pattern behavior, transfer persistence, conservation gating, UI reasons.  
**Dependencies:** None. Coordinate with V-04 if cross-copilot signals become source evidence; a signal alone must not become a judgment transfer artifact.

## Section C: Fix order

1. **Group 1 — F-02 / V-02:** Correct conservation math first: lifetime `V`, rolling-400 `q`, verified-only inputs; unify scorer and status API.
2. **Group 2 — F-06 / V-06 and F-07 / V-07:** Remove retained graph-derived caches so the corrected gate and query paths read current graph state. This shares scorer files with Group 1, so run sequentially.
3. **Group 3 — F-01 / V-01:** Rebuild S2P experiment around one AGE GraphStore with explicit run/arm domain namespaces. This requires the scorer domain-scope design to be settled in Group 1/2 if scorer internals are being changed.
4. **Group 4 — F-03 / V-03:** Replace migration CLI's GraphStore-shaped SQLite source with a read-only migration reader; then retire SQLiteGraphStore and DualWriteStore. Keep source-data cutover and its verification separate.
5. **Group 5 — F-04 / V-04:** Move cross-copilot signals from SQLiteSignalStore to graph events and wire all apps to the one selected store.
6. **Group 6 — F-05 / V-05:** Remove SQLite/file authority fallbacks for outcomes, proofs, promotion, variants, and frozen judgment; require existing graph adapters and explicit test doubles.
7. **Group 7 — F-09 / V-09:** Make transfer execution require persisted, validated artifacts and store both source and target governance evidence.
8. **Group 8 — F-08 / V-08:** Share one InMemoryGraphStore across offline demo domains and persist/read the demo signal from that graph; use AGE for an integrated demo.

Groups 4 and 5 can be developed in parallel after interface decisions are recorded. Groups 1 and 2 are sequential because they touch scorer cache and conservation behavior. Group 3 follows their scorer API decision. Groups 6 and 7 can proceed in parallel with Group 4 after `ProtocolV2GraphStore` event/transfer contracts are settled; final integration tests are sequential after all graph rewiring. Group 8 depends on the graph signal shape from Group 5.

## Section D: Test impact

| Group | Tests to modify | New tests | Expected count delta | Verification suites |
|---|---|---|---|---|
| 1 / F-02 | `tests/test_conservation*.py`, `tests/scoring/test_conservation.py`, status/router tests that currently expect lifetime `q` | Window boundary and ordering tests at 399/400/401; lifetime V plus rolling q; recent degradation closes gate; status and scorer agree | 0 (replace assertions) | `tests/` and all three app backend suites |
| 2 / F-06/F-07 | `tests/test_scorer*.py`, `tests/test_di_query_service.py`, `tests/test_scoring_router.py`, conservation-router/materializer tests, app query/scoring tests | External graph write becomes visible to existing scorer; repeated DI query invokes provider and sees changed graph; scoring uses fresh context; conservation status ignores stale materialized payloads | 0 (replace cache-specific tests, replace with freshness tests) | `tests/`, app backend suites; concurrency test for two store clients |
| 3 / F-01 | `apps/s2p_differentiation` tests/scripts and scorer constructor tests | Same GraphStore object for CI/hand arms; arm namespace isolation within one AGE graph; AGE unavailable fails closed | 0 (replace per-memory tests; add integration cases) | S2P tests; `tests/`; live AGE experiment integration |
| 4 / F-03 | `tests/graph/test_sqlite*`, `tests/test_dual_write*`, migration reconciliation/CLI tests, exports tests | Migration reader is not a GraphStore; CLI copies historical rows into AGE; factory rejects old backend names | Negative delta equal to retired backend-only tests; keep migration coverage | `tests/`; migration integration suite; mypy for touched migration/graph files |
| 5 / F-04 | `tests/test_cross_signal*`, graph event tests, Trading/Purchasing/DataOps router tests | Signals round-trip in shared graph; filters by source/target; no SQLite default; AGE outage never reads outbox | 0 (replace SQLite-store tests with graph adapter tests) | `tests/`; all three app backend suites; live AGE signal probe |
| 6 / F-05 | `tests/test_outcome_protocol.py`, `tests/test_promotion_engine.py`, `tests/evolution/test_sqlite_variant_store.py`, twin/purchasing-control tests | Each record type round-trips through graph adapters; absent GraphStore capability fails closed; explicit InMemoryGraphStore test adapter remains usable | Negative delta from SQLite-only behavior tests; replace rather than drop lifecycle coverage | `tests/`; all app backend suites; AGE graph lifecycle integration |
| 7 / F-09 | `tests/test_transfer_router.py`, graph transfer API tests, SharedPatternRegistry tests | No source artifact blocks without writes; synthetic/demo artifact cannot transfer; persisted record contains both conservation states, source IDs, and mapping | 0 | `tests/`; all app backend suites; AGE transfer integration |
| 8 / F-08 | `tests/test_preseed.py`, demo integration/preseed tests | All seeded domains share one store identity; signal is written/read from graph; production/integrated mode refuses memory fallback | 0 | `tests/`; demo integration suite; AGE demo smoke test |

Exact final counts should be captured by the implementation prompts after the current baseline is rerun; counts are not asserted here because this audit is read-only and the current working tree contains unrelated edits.

## Section E: What is already compliant

- `copilot_sdk/graph/factory.py:19, 98–195` exposes only `memory` and `age`; production config fails closed and requires the authorized shared AGE graph.
- `copilot_sdk/graph/protocol.py` defines protocol surfaces for decisions, outcomes, evolution, traversal, centroids, transfer and conservation; there are no `DecisionStore` references in `copilot_sdk/` or `apps/`.
- The selected graph store is injected and reused by the principal scoring/learning/router wiring in Trading, Purchasing and DataOps app roots. The production AGE destination is the shared graph; store client instances do not imply separate logical graphs.
- `copilot_sdk/backend/scoring_router.py` distinguishes mutation (`POST /score`) from read-only calculations; `CompoundingScorer.score_read_only()` does not create a verified decision. The POST scoring path creates a pending decision, and `learn()` persists its verified outcome, preserving P3's lifecycle boundary.
- `copilot_sdk/evolution/graph_store.py` provides GraphVariantStore, GraphPromotionStore, GraphOutcomeLedger and GraphProofLedger adapters over ProtocolV2GraphStore. These are suitable replacements for their remaining durable fallback classes.
- `copilot_sdk/graph/outbox.py` / `DurableOutbox` and `copilot_sdk/scoring/persistence_outbox.py` are write buffers, not graph readers. They are exempt under P8 and are not flagged.
- `copilot_sdk/backend/self_computation_router.py` uses the injected scorer's read-only scoring path for previews; no evidence found in the reviewed path that preview reads write a Decision or increment V.
- `copilot_sdk/backend/evolution_router.py` and the Trading, Purchasing, and DataOps mount sites were checked for memory authority and cross-type access. Each production app mount supplies both a graph-store factory and an app-scoped evolver; the route's process-local fallback is used only when a caller omits those dependencies and is not used by these integrated app roots. Preserve the injected graph composition and add a regression test if changing the router.
- `copilot_sdk/backend/conservation_router.py` is covered by V-07, not compliant: `status()` can return a materialized graph-derived payload before calling its live state provider.
- `copilot_sdk/backend/transfer_router.py` already checks both source and target conservation before execution and persists a transfer record in GraphStore; V-09 concerns the fabricated-pattern fallback, validation claim, and omitted source-state evidence, not the existence of the graph transfer API itself.
- App graph-status tests that mention `sqlite`/`dual_write` are rejection tests for retired backend names; their strings are not evidence that the runtime factory accepts those backends.

## Scan evidence

- `DecisionStore`: 0 matches in `copilot_sdk/` and `apps/` Python files.
- `SQLiteGraphStore`: 6 source matches: its implementation, the DualWrite import/check, and the migration CLI import/construction. No active app main imports it.
- `DualWriteStore`: one class implementation remains in `copilot_sdk/graph/dual_write_store.py`.
- `InMemoryGraphStore`: 132 matches, predominantly tests and explicit test/dev fixtures. Runtime-risk matches reviewed here are S2P engine and demo preseed; the Trading clone-fingerprint endpoint creates a disposable, empty local store and does not act as an authority.
- Non-outbox SQLite scan finds persistent stores in graph legacy code, migration readers, `signal_store.py`, `outcome/ledger.py`, `promotion/core.py`, `evolution/variant_store.py`, purchasing control, and measurement/migration modules. Only graph-memory/authority cases are violations above; migration source readers and experiment-measurement storage are not treated as GraphStore backends.
- Principle headings P1 through P10 are present in `docs/design_principles_v2.md`.
