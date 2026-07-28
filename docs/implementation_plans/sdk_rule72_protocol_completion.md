# SDK Rule #72 — Protocol Completion Design

Status: design only; no source or test changes are part of this document.

## 1. Executive summary

The SDK contains 18 Decision-access compatibility probes: dynamic
`getattr` dispatch and `TypeError` retries around methods that are already
part of the shared graph contract. These probes allow a missing or legacy
store method to become an empty list, zero count, or an unscoped retry.
That conflates a valid cold start with a graph or contract failure and can
make cross-domain data errors invisible.

The selected approach is Protocol completion (Approach A): make the
Decision-read contract complete, verify every production store implements
it, and replace Decision-method probing with direct domain-aware calls.
No domain-bound facade is introduced in the SDK because the SDK is shared by
all copilots; each caller already has its domain.

Four `TypeError` handlers are explicitly outside Rule #72: three legacy
payload-shape handlers in `scoring/startup_restore.py` and one JSON
serialization handler in `state/tab_state_cache.py`. The migration shadow
reader remains a deliberate exception, but must warn and label its output
non-authoritative.

## 2. Protocol change

### 2.1 Promotion

Promote this method from `ProtocolV2GraphStore` into `GraphStore`:

```python
def count_verified_decisions(self, domain: str) -> int: ...
```

All SDK code treats it as a standard Decision method. It belongs beside
`count_verified`, `count_correct`, and `count_decisions`, rather than only in
the V2 extension. The existing declaration at
`copilot_sdk/graph/protocol.py:304` should be retained only once the method
has been promoted.

### 2.2 Store verification

The required stores already implement the promoted method:

| Store | Evidence | Result |
|---|---|---|
| AGE GraphStore | `ci-platform/ci_platform/graph/age_graph_store.py:1614` | Present |
| AGE adapter | `ci-platform/ci_platform/graph/age_sdk_adapter.py:291` | Present |
| SQLiteGraphStore | `copilot_sdk/graph/sqlite_store.py:1936` | Present |
| InMemoryGraphStore | `copilot_sdk/graph/memory_store.py:937` | Present |
| DualWriteStore | `copilot_sdk/graph/dual_write_store.py:364` | Present |

No production store gap was found. Structural test doubles and migration
fakes must be audited and updated where they are used as `GraphStore`
instances. `count_categories_with_n` remains an L5 method at
`protocol.py:375`; it is not promoted into core `GraphStore` by this plan.
`get_decision_links` and `query_context` remain in `GraphTraversalStore`.

### 2.3 Contract semantics

- Every Decision read receives the caller's domain.
- A successful zero-row query returns an empty list or zero as appropriate.
- A graph/query exception is raised to the caller; it is never converted to
  a synthetic empty result or measurement.
- Router boundaries may map the graph exception to HTTP 503. Library services
  propagate it.
- Missing required methods are contract violations and should fail loudly.

## 3. Caller migration table

The table contains all 18 Decision-access instances identified in the
inventory. The shadow-scorer entry is warning/label-only by decision; the
other 17 are direct-call migrations.

### 3.1 Hot path and conservation

| # | File:line | Current pattern | New pattern | Risk | Call path |
|---:|---|---|---|---|---|
| 1 | `backend/scoring_router.py:339-344` | `getattr(store, "get_decision", None)` then `get_decision(decision_id)` | `store.get_decision(decision_id, domain=domain)`; preserve `KeyError` for missing ID | High: fixes domain omission in learning | `/learn` hot path |
| 2 | `scoring/scorer.py:528-531` | Probe count methods, then probe `get_verified_decisions`, else `0` | Direct `count_verified_decisions(self._domain)` or the declared count contract | High: zero fallback can corrupt state | Scorer verified-count API |
| 3 | `scoring/scorer.py:1261-1277` | Probe count methods, then `get_all_decisions`, else `(0,0,0)` | Direct `count_verified`, `count_correct`, and required count API; propagate errors | High: conservation and V metrics | Scoring/learning conservation |
| 4 | `scoring/scorer.py:1283-1289` | Optional `get_verified_decisions` probe | Direct `store.get_verified_decisions(domain)` | High: failed reads must not become unavailable-as-empty | Conservation calculations |
| 5 | `backend/conservation_utils.py:152-156` | Detect whether state itself is store-like | Use the typed store/state boundary; avoid probing Decision methods | Medium: affects wrapper compatibility | Conservation payload construction |
| 6 | `backend/conservation_utils.py:202-209` | Call count with domain, retry without domain | Direct domain-aware count call; remove retry | High: unscoped count | Conservation metrics |
| 7 | `backend/conservation_utils.py:212-219` | Optional `count_verified_decisions` and no-domain retry | Direct `store.count_verified_decisions(domain)` | High: distinguish empty from failure | Conservation metrics |

### 3.2 Reporting and measurement

| # | File:line | Current pattern | New pattern | Risk | Call path |
|---:|---|---|---|---|---|
| 8 | `backend/scoring_router.py:216-221` | Probe `get_decisions`, fallback to `get_all_decisions`, then `[]` | Direct `store.get_decisions(domain, limit=10**12)` under the complete contract | Medium: history endpoint changes on broken stores | `/history` |
| 9 | `backend/self_computation_router.py:221-225` | Probe all decisions, fallback to verified, else `[]` | Direct `store.get_all_decisions(domain)` | Medium | Self-computation reporting |
| 10 | `backend/self_computation_router.py:229-230` | Probe verified decisions, else `[]` | Direct `store.get_verified_decisions(domain)` | Medium | Self-computation reporting |
| 11 | `backend/self_computation_router.py:238-252` | Probe count methods, fallback to list length/Python count | Direct `count_verified(domain)` and `count_correct(domain)` | Medium | Self-computation reporting |
| 12 | `scoring/iks_service.py:46-54` | Probe `get_verified_decisions`, else `[]` | Direct `self._graph_store.get_verified_decisions(self._domain)` | Medium: IKS must not fabricate empty availability | IKS summary |
| 13 | `scoring/measurement_state.py:115-124` | Probe verified rows, fallback to all rows | Direct `get_verified_decisions(domain)`; no graph fallback | Medium | Measurement state |
| 14 | `scoring/measurement_state.py:125-128` | Fallback to scorer `get_verified_count`, synthesize rows | Retain only as an explicitly non-graph test/state path, or raise when a graph store exists but failed | Medium | Measurement state |

### 3.3 Query, enrichment, and shadow paths

| # | File:line | Current pattern | New pattern | Risk | Call path |
|---:|---|---|---|---|---|
| 15 | `di/nl_query.py:76-88` | Probe verified/all methods; retry without domain on `TypeError`; return `[]` on errors | Direct domain-aware call selected by the existing contract; remove retry and propagate graph errors | High: current retry is unscoped | NL query execution |
| 16 | `di/enrichment.py:327-336` | Probe verified reads; convert missing/error to warnings and `[]` | Direct `graph_store.get_verified_decisions(self.domain)`; propagate graph failure; retain only explicit “unsupported enrichment” handling if separately typed | Medium | Enrichment computation |
| 17 | `migrate/shadow_scorer.py:351-365` | Probe verified reads and convert exceptions to coverage `0.0` | Keep the compatibility probe by decision, but log a warning on fallback and label the resulting shadow output non-authoritative | Low for production, high if consumed as production data | Migration shadow scoring |
| 18 | `backend/scoring_router.py:220-221` | The `get_all_decisions` branch is a separate fallback at the same history site | Remove branch as part of row 8; no dynamic fallback remains | Medium | `/history` |

Rows 8 and 18 refer to the two physical probes at the same history block;
they must be removed together. The implementation count is therefore 17
direct migration sites plus one retained, explicitly labeled migration
exception.

## 4. Excluded instances

These are not Decision-method compatibility shims and are not changed by
this plan:

| File:line | Reason | Decision |
|---|---|---|
| `scoring/startup_restore.py:156` | Non-iterable legacy vector shape | Out of scope; retain |
| `scoring/startup_restore.py:169` | Non-iterable legacy weight payload | Out of scope; retain |
| `scoring/startup_restore.py:176` | Non-iterable legacy weight row | Out of scope; retain |
| `state/tab_state_cache.py:502` | JSON serialization fallback | Out of scope; retain |
| `migrate/shadow_scorer.py:351` | Migration/shadow output is not authoritative | Retain, add warning and explicit provenance label |

The list/tuple handling in `di/nl_query.py:71-75` is also not a forbidden
dynamic method access; it supports callers that provide already-materialized
rows. It may remain, provided graph-store failures are not converted to
empty rows.

## 5. Test-double changes

The repository-wide AST inventory found 22 test doubles that implement at
least one GraphStore Decision method but do not currently define
`count_verified_decisions`: 

| Test file | Double |
|---|---|
| `tests/backend/test_conservation_router.py` | `GraphStoreLike` |
| `tests/backend/test_scoring_router.py` | `FakeStore` |
| `tests/test_di_enrichment.py` | `FakeGraphStore`, `ReadOnlyGraphStore` |
| `tests/test_entity_enrichment.py` | `DefaultGraphStore` |
| `tests/test_graph_entity_links.py` | `MinimalGraphStore` |
| `tests/test_graphstore_consolidation.py` | `MinimalStore` |
| `tests/test_iks_service.py` | `Store` |
| `tests/test_l5_protocol_extension.py` | `MinimalGraphStore` |
| `tests/test_nl_query_extended.py` | `FakeGraphStore` |
| `tests/test_read_diff_runner.py` | `ReadStore` |
| `tests/test_reconcile_archive.py` | `ArchiveSQLiteSource`, `ArchiveAGEStore` |
| `tests/test_response_models.py` | `FakeStore` |
| `tests/test_situation_analyzer.py` | `FakeGraphStore` |
| `apps/dataops/backend/tests/test_di.py` | `GraphStore` |
| `apps/purchasing/backend/tests/test_auto_order.py` | `_CategoryStore`, `_SampleMixedStore`, `_SampleOnlyStore` |
| `apps/purchasing/backend/tests/test_iks_trust.py` | `Store` |
| `apps/purchasing/backend/tests/test_match_queue.py` | `RecordingStore` |
| `apps/trading/backend/tests/test_execution_analysis.py` | `_Store` |
| `apps/trading/backend/tests/test_trust_analysis.py` | `FakeStore` |

These are candidates for the promoted method. A minimal double used only
for one narrow method need not grow unrelated APIs, but every double passed
to scorer/conservation/reporting code must implement the complete contract.
The two generic `*args/**kwargs` methods in
`tests/test_graphstore_consolidation.py:20-23` accept domain positionally but
should be made explicit for enforcement and readability.

1. Add `count_verified_decisions(domain)` to every fake that models a
   `GraphStore` and is used by scorer/conservation tests.
2. Ensure all Decision methods accept the domain argument, including
   `get_decision(..., domain=None)` and domain-bearing enumeration/count
   methods. The known inventory has no required Decision method with a
   missing explicit domain parameter except the generic consolidation double
   noted above.
3. Update fakes that previously relied on a no-argument retry. Do not add
   compatibility branches to production code.
4. Make doubles stateful: store domain-stamped decisions and filter by the
   requested domain. A double that merely accepts `domain` but returns rows
   from all domains violates Rule #72.
5. Add tests for:
   - every direct call passing the expected domain;
   - graph exception propagation;
   - valid empty query remaining empty rather than raising;
   - cross-domain rows never being returned;
   - `count_verified_decisions` agreement with verified-row enumeration.

## 6. Migration strategy

### Phase 1 — Protocol promotion and store verification

- Move `count_verified_decisions` to `GraphStore`.
- Verify AGE, adapter, SQLite, memory, and dual-write implementations.
- Add/update complete stateful test doubles.
- Run SDK graph protocol/store tests.

Rollback: restore the declaration location only if an implementation gap is
found; do not restore dynamic caller probing.

### Phase 2 — Hot-path fixes

Migrate `scoring/scorer.py`, `backend/conservation_utils.py`, and
`backend/scoring_router.py`. Pass the router's domain through `_get_decision`.
Remove no-domain retries and zero/empty fallbacks for graph failures.

Run scorer, conservation, scoring-router, and integration tests after each
file. Rollback is a source revert of the direct-call migration while keeping
the completed test doubles and Protocol contract; no compatibility retry is
to be restored.

### Phase 3 — Reporting fixes

Migrate `measurement_state.py`, `self_computation_router.py`, and
`iks_service.py`. Keep valid zero-row cold starts distinct from exceptions.
Map failures to 503 only in router boundaries.

### Phase 4 — Enrichment and NL query

Migrate `di/enrichment.py` and `di/nl_query.py`. Remove the unscoped
`TypeError` retry in NL query. Add explicit warning/provenance behavior to
the migration shadow path.

Run the complete SDK suite and every copilot suite after this phase.

## 7. Enforcement

Create an SDK equivalent of S2P's `test_rule72_enforcement.py` that walks
all `copilot_sdk/` production Python files with `ast` and rejects:

- `getattr`/`hasattr` whose string argument is a Decision method;
- `except TypeError` blocks containing Decision-method calls;
- direct Decision calls without a domain where the method contract requires
  one;
- no-domain retries around graph reads.

Allowlist only:

- the explicitly documented migration/shadow exception, which must emit a
  warning and mark output non-authoritative;
- non-graph data-shape and JSON serialization handlers listed in Section 4.

The test must report file and line for every violation. It must not ban
unrelated optional scorer attributes or ordinary object introspection.

Add a scanner rule that treats direct `store.<decision_method>(..., domain)`
as scoped, while retaining separate reporting for test, migration, and
shadow code. The allowlist must be narrow: it may exclude the four
non-graph handlers in Section 4 and the one explicitly labeled shadow path,
but it must not exclude all of `shadow_scorer.py` or all `nl_query.py`.

## 8. Review corrections and dependency notes

The cited store signatures are compatible with the promotion:

- AGE GraphStore: `get_decision` at `age_graph_store.py:1541`, the domain
  enumerations/counts at `:1555-1661`, and `get_all_decisions` at `:2033`.
- AGE adapter: corresponding methods at `age_sdk_adapter.py:268-300`.
- SQLite: methods at `sqlite_store.py:1841-1952`.
- In-memory: methods at `memory_store.py:891-955`.
- Dual-write: primary-only read delegation at `dual_write_store.py:351-364`.

All five implement `count_verified_decisions(domain)` with the same required
domain parameter. No second missing core Protocol method was found among the
Decision methods used by this plan. Traversal methods remain owned by
`GraphTraversalStore`.

The hot-path dependency order is safe but the call-site changes must be
explicit:

1. `create_scoring_router()` calls `_get_decision()` from `/learn` at
   `backend/scoring_router.py:94-124,337-345`; `_get_decision` must receive
   the router's `domain` and pass it to `store.get_decision`.
2. Scorer conservation paths call `_conservation_stats` from the scorer's
   scoring/learning paths; a graph exception should propagate to the existing
   scorer/router boundary rather than become zero.
3. `state_counts()` is used by conservation reporting and must preserve the
   distinction between an empty successful query and a failed query.
4. Reporting migration can follow hot-path migration because it depends on
   the same promoted signatures, not vice versa.

The enforcement test should scan the 18 Decision probe sites plus the
`nl_query.py:82` TypeError retry, which is a separate Decision retry path
and must be forbidden. It should exclude only the four non-graph handlers
and the one warning/labeled shadow exception. It should report direct
no-domain calls separately; an AST check that only searches `getattr` would
miss the `scoring_router.py:339` omission.

## Decisions

- **DECIDED — Protocol promotion:** promote `count_verified_decisions` into
  `GraphStore`.
- **DECIDED — Non-graph TypeErrors:** startup restore and tab-state handlers
  are out of scope and remain unchanged.
- **DECIDED — Migration/shadow:** retain the shadow probe, add warning and
  non-authoritative labeling.
- **DECIDED — Scoring router domain:** the `get_decision` omission is a
  correctness fix; pass the copilot domain through the router.
- **DECIDED — NL query retry:** remove the no-domain retry.
- **DECIDED — Conservation retry:** remove the no-domain retry.
- **DECIDED — Failure behavior:** raise on graph failure; return empty only
  for a successful empty query.
