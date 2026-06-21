# P44 DI Graph Enrichment Framework Plan

Date: 2026-06-15

## Executive Verdict

READY_FOR_IMPLEMENTATION: YES

P44 can be implemented as a small SDK-level Data Intelligence enrichment
framework without GraphStore protocol changes. P39A already provides the
domain-neutral entity enrichment substrate through `write_entity_enrichment`,
`read_entity_enrichment`, and `list_entity_enrichments`
(`copilot_sdk/graph/protocol.py:94`, `copilot_sdk/graph/protocol.py:110`,
`copilot_sdk/graph/protocol.py:120`). SQLite and Memory implementations support
the API with dry-run receipts, protected-field rejection, readback, listing, and
idempotent upsert behavior (`copilot_sdk/graph/sqlite_store.py:2463`,
`copilot_sdk/graph/memory_store.py:1209`, `tests/test_entity_enrichment.py:248`,
`tests/test_entity_enrichment.py:287`, `tests/test_entity_enrichment.py:309`,
`tests/test_entity_enrichment.py:404`).

The implementation should live under `copilot_sdk/di/enrichment.py` and expose a
generic `BaseGraphEnricher` / `GraphEnricher` pattern. Domain copilots should
subclass or configure it for entity grouping and metric computation. P44 must
remain background/on-demand infrastructure and must not mutate scorer,
conservation, outcomes, DK, or factor inputs.

## Current Substrate

### P39A Status

P39A is present.

GraphStore enrichment API signatures:

```python
write_entity_enrichment(
    *,
    domain: str,
    entity_type: str,
    entity_id: str,
    namespace: str,
    metrics: dict[str, ProvenancedValue],
    computed_from: EnrichmentSourceSet,
    dry_run: bool = False,
    idempotency_key: str | None = None,
) -> EntityEnrichmentReceipt
```

Evidence: `copilot_sdk/graph/protocol.py:94`.

```python
read_entity_enrichment(
    *,
    domain: str,
    entity_type: str,
    entity_id: str,
    namespace: str | None = None,
) -> dict[str, ProvenancedValue]
```

Evidence: `copilot_sdk/graph/protocol.py:110`.

```python
list_entity_enrichments(
    *,
    domain: str,
    entity_type: str | None = None,
    namespace: str | None = None,
    limit: int = 500,
) -> list[EntityEnrichmentRecord]
```

Evidence: `copilot_sdk/graph/protocol.py:120`.

### Enrichment Data Types

Available types in `copilot_sdk/graph/enrichment.py`:

- `PROTECTED_ENTITY_FIELDS` includes identity and graph structural fields such
  as `id`, `entity_id`, `supplier_id`, `domain`, `entity_type`, `name`, and edge
  identifiers (`copilot_sdk/graph/enrichment.py:9`).
- `is_protected_metric_name()` checks metric names against that registry
  (`copilot_sdk/graph/enrichment.py:36`).
- `ProvenancedValue` carries `value`, `source`, `provenance_tier`,
  `source_count`, `factor_eligible`, `provenance_label`, `measured`, `verified`,
  `computed_at`, and warnings (`copilot_sdk/graph/enrichment.py:40`).
- `ProvenancedValue.from_verified()` creates learned, measured, verified values
  from verified outcomes and sets `factor_eligible` based on `n_min`
  (`copilot_sdk/graph/enrichment.py:69`).
- `ProvenancedValue.from_fixture()` creates context values that are not measured,
  not verified, and not factor eligible (`copilot_sdk/graph/enrichment.py:93`).
- `ProvenancedValue.unavailable()` creates unavailable values that are not
  factor eligible (`copilot_sdk/graph/enrichment.py:114`).
- `EnrichmentSourceSet` records verified/unverified counts, decision IDs,
  outcome IDs, fixture sources, integration sources, and computation version
  (`copilot_sdk/graph/enrichment.py:153`).
- `EntityEnrichmentReceipt` records persistence, dry-run, metrics written,
  rejected/protected metrics, idempotency key, timestamp, and warnings
  (`copilot_sdk/graph/enrichment.py:170`).
- `EntityEnrichmentRecord` is the list/read record type
  (`copilot_sdk/graph/enrichment.py:186`).

### Provenance Guards

`ProvenancedValue.__post_init__()` rejects unsafe provenance combinations:
fixture values cannot be verified or measured, unavailable values cannot be
factor eligible, verified-outcome values must be verified and measured, and
learned provenance requires `verified=True` (`copilot_sdk/graph/enrichment.py:53`).
Tests cover those guards (`tests/test_entity_enrichment.py:41`,
`tests/test_entity_enrichment.py:51`, `tests/test_entity_enrichment.py:61`,
`tests/test_entity_enrichment.py:70`, `tests/test_entity_enrichment.py:90`,
`tests/test_entity_enrichment.py:109`).

### Store Behavior

Default protocol behavior:

- Default `write_entity_enrichment()` raises `NotImplementedError`
  (`copilot_sdk/graph/protocol.py:105`, `tests/test_entity_enrichment.py:204`).
- Default reads return `{}` and default lists return `[]`
  (`copilot_sdk/graph/protocol.py:110`, `copilot_sdk/graph/protocol.py:120`,
  `tests/test_entity_enrichment.py:216`, `tests/test_entity_enrichment.py:228`).

SQLite behavior:

- Validates values are `ProvenancedValue` instances and rejects protected metric
  names (`copilot_sdk/graph/sqlite_store.py:2485`).
- Returns a non-persisted receipt when no allowed metrics exist
  (`copilot_sdk/graph/sqlite_store.py:2497`).
- Supports dry-run receipts without writing (`copilot_sdk/graph/sqlite_store.py:2514`,
  `tests/test_entity_enrichment.py:287`).
- Persists via upsert on `(domain, entity_type, entity_id, namespace,
  metric_name)` (`copilot_sdk/graph/sqlite_store.py:2532`).
- Reads namespace-scoped metrics as bare metric names and all namespaces as
  `namespace.metric` keys (`copilot_sdk/graph/sqlite_store.py:2579`).
- Lists records by domain/entity type/namespace with a limit
  (`copilot_sdk/graph/sqlite_store.py:2610`).

Memory behavior:

- Mirrors validation, protected-field rejection, dry-run, persistence, read, and
  list behavior in memory (`copilot_sdk/graph/memory_store.py:1209`,
  `copilot_sdk/graph/memory_store.py:1259`, `copilot_sdk/graph/memory_store.py:1275`,
  `copilot_sdk/graph/memory_store.py:1303`, `copilot_sdk/graph/memory_store.py:1323`).
- Readback returns deep copies (`tests/test_entity_enrichment.py:416`).

AGE behavior:

- The current `ci-platform` AGE adapter is tested as write-unsupported for
  entity enrichment, while reads/lists return empty safe values
  (`tests/test_entity_enrichment.py:454`, `tests/test_entity_enrichment.py:467`,
  `tests/test_entity_enrichment.py:477`).
- P44 must therefore treat AGE writes as unsupported unless a later adapter
  implements P39A persistence. It must return honest warnings/reports rather
  than fake persistence.

GraphStore changes needed: NO.

## P39B Pattern Reference

S2P supplier enrichment is the best reference for how domain copilots should use
P44, but it should not be extracted wholesale into the SDK.

Reusable concepts:

- Enrichment is an on-demand service, not hot scoring path code
  (`s2p-copilot/backend/app/services/s2p_enrichment.py:27`).
- It reads verified and all decisions separately
  (`s2p-copilot/backend/app/services/s2p_enrichment.py:48`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:49`).
- It groups by domain entity key, here supplier ID
  (`s2p-copilot/backend/app/services/s2p_enrichment.py:104`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:377`).
- It builds an `EnrichmentSourceSet` with verified/unverified counts, decision
  IDs, fixture sources, integration sources, and computation version
  (`s2p-copilot/backend/app/services/s2p_enrichment.py:120`).
- It writes through `write_entity_enrichment()` only
  (`s2p-copilot/backend/app/services/s2p_enrichment.py:287`).
- It calls GraphStore dry-run when possible and otherwise synthesizes a
  non-persisted dry-run receipt (`s2p-copilot/backend/app/services/s2p_enrichment.py:307`).
- It returns unsupported write receipts when write support is missing or raises
  `NotImplementedError` (`s2p-copilot/backend/app/services/s2p_enrichment.py:284`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:298`).
- It serializes provenance fields for display
  (`s2p-copilot/backend/app/services/s2p_enrichment.py:424`).

Domain-specific concepts that should remain outside SDK:

- S2P constants: `DOMAIN`, `ENTITY_TYPE`, `NAMESPACE`,
  `COMPUTATION_VERSION` (`s2p-copilot/backend/app/services/s2p_enrichment.py:20`).
- Supplier fixture and invoice loading
  (`s2p-copilot/backend/app/services/s2p_enrichment.py:17`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:38`).
- Lead-time and OTIF metric logic
  (`s2p-copilot/backend/app/services/s2p_enrichment.py:394`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:405`).
- Supplier-specific helper fields and category/trend calculations
  (`s2p-copilot/backend/app/services/s2p_enrichment.py:518`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:540`).
- S2P FastAPI route surface
  (`s2p-copilot/backend/app/routers/s2p_enrichment.py:12`).

Verified-only boundary:

- S2P uses verified decisions for exception rate, accuracy, quarterly counts,
  and trend (`s2p-copilot/backend/app/services/s2p_enrichment.py:158`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:164`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:192`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:197`).
- Zero-verified rate/quarter/trend metrics are unavailable or insufficient
  rather than learned/measured (`s2p-copilot/backend/app/services/s2p_enrichment.py:455`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:464`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:485`).
- GraphStore read counts and unverified history remain context, not verified
  performance facts (`s2p-copilot/backend/app/services/s2p_enrichment.py:136`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:147`,
  `s2p-copilot/backend/app/services/s2p_enrichment.py:170`).

Display integration:

- P38 context builder reads enrichment with `read_entity_enrichment()` and adds
  it under `properties["enrichment"]` only when present
  (`s2p-copilot/backend/app/services/s2p_context_builder.py:201`,
  `s2p-copilot/backend/app/services/s2p_context_builder.py:228`).
- Base supplier node source remains `fixture`
  (`s2p-copilot/backend/app/services/s2p_context_builder.py:212`).

## DI Module State

Current DI package files:

- `copilot_sdk/di/__init__.py`
- `copilot_sdk/di/combination_discovery.py`
- `copilot_sdk/di/models.py`
- `copilot_sdk/di/nl_query.py`
- `copilot_sdk/di/profiler.py`
- `copilot_sdk/di/query_patterns.py`

Current exports include P30/P42/P43 symbols:

- `NLQueryRouter`
- `ProfileConfig`
- `SourceProfile`
- `BaseSourceProfiler`
- `QueryResult`
- `QueryPattern`
- `MultiEntityPattern`
- `TimeWindowPattern`
- `AggregationPattern`
- `ComparisonPattern`
- `AccuracyPattern`
- `CombinationCandidate`
- `DiscoveryReport`
- `CombinationDiscoveryEngine`
- `discover_combinations`

Evidence: `copilot_sdk/di/__init__.py:22`.

There is no existing `copilot_sdk/di/enrichment.py`. The new SDK framework
should live there to avoid name conflicts with `copilot_sdk/graph/enrichment.py`.
Naming should use `GraphEnricher`, `BaseGraphEnricher`,
`GraphEnrichmentReport`, and `GraphEnrichmentResult`; do not reuse
`EntityEnrichmentRecord` for run reports because that name already belongs to
the GraphStore read/list model (`copilot_sdk/graph/enrichment.py:186`).

Planned new exports:

- `BaseGraphEnricher`
- `GraphEnricher`
- `GraphEnrichmentResult`
- `GraphEnrichmentReport`

Existing exports must remain exactly available.

## GraphStore Surface

Decision reads already exist:

- `get_decision(decision_id)` (`copilot_sdk/graph/protocol.py:39`)
- `get_decisions(domain, category=None, limit=400)`
  (`copilot_sdk/graph/protocol.py:42`)
- `get_all_decisions(domain)` (`copilot_sdk/graph/protocol.py:50`)
- `get_verified_decisions(domain)` (`copilot_sdk/graph/protocol.py:53`)

P44 should support two input modes:

1. `enrich(decisions, dry_run=False, graph_store=None)`
   - Accept caller-provided decision dictionaries.
   - Group and compute metrics without requiring a store.
   - Persist only if `graph_store` is provided and `dry_run=False`.

2. `enrich_from_store(graph_store, domain, dry_run=False)`
   - Prefer `graph_store.get_verified_decisions(domain)` for verified-outcome
     jobs.
   - If the concrete subclass needs all decisions, it should either accept
     caller-supplied decisions or explicitly override store-reading behavior.
   - Do not add GraphStore methods.

Stores without enrichment write support are expected: default GraphStore raises
`NotImplementedError` for writes (`copilot_sdk/graph/protocol.py:105`) and AGE
adapter tests currently expect unsupported writes
(`tests/test_entity_enrichment.py:454`).

## P44 Design

### BaseGraphEnricher

Create an abstract/configurable class in `copilot_sdk/di/enrichment.py`.

Core configuration:

- `domain: str`
- `entity_type: str`
- `namespace: str`
- `min_decisions: int = 1`
- `computation_version: str = ""`

Required subclass hooks:

```python
def group_key(self, decision: dict[str, Any]) -> str | None:
    ...

def compute_metrics(
    self,
    entity_id: str,
    decisions: list[dict[str, Any]],
) -> dict[str, ProvenancedValue]:
    ...
```

Optional override hooks:

```python
def build_source_set(
    self,
    entity_id: str,
    decisions: list[dict[str, Any]],
) -> EnrichmentSourceSet:
    ...

def idempotency_key(
    self,
    entity_id: str,
    source_set: EnrichmentSourceSet,
) -> str:
    ...

def read_decisions_from_store(
    self,
    graph_store: Any,
    domain: str,
) -> list[dict[str, Any]]:
    ...
```

Default `build_source_set()` should:

- set `verified_decision_count=len(decisions)` because
  `enrich_from_store()` should default to verified decisions.
- set `decision_ids` from `decision_id` values when present.
- set `computation_version`.

Default `read_decisions_from_store()` should:

- call `graph_store.get_verified_decisions(domain)` if callable.
- return only dictionary rows.
- return an empty list with warning if unavailable or failing.

### GraphEnricher

`GraphEnricher` may be a concrete base with callable hooks passed to the
constructor, or a thin alias/subclass of `BaseGraphEnricher`. The implementation
should prefer a clear abstract base plus a simple concrete wrapper only if tests
need a non-subclass ergonomic path.

### Main Methods

```python
def enrich(
    self,
    decisions: list[dict[str, Any]],
    *,
    dry_run: bool = False,
    graph_store: Any | None = None,
) -> GraphEnrichmentReport:
    ...
```

Behavior:

- Group decisions by `group_key(decision)`.
- Skip `None`/empty group keys with warnings.
- Skip groups below `min_decisions`.
- Call `compute_metrics(entity_id, decisions)`.
- Preserve explicit `ProvenancedValue` metrics. Raw metric values may appear in
  compute-only reports, but must carry per-entity
  `raw_metric_without_provenance=<metric>` warnings and must not be written as
  learned/verified/measured facts.
- If no `graph_store` is provided, return compute-only results with
  `persisted=False`.
- If `dry_run=True`, call `write_entity_enrichment(..., dry_run=True)` when
  available so protected-field validation can run; if unsupported, compute-only
  dry-run is acceptable with an honest warning.
- If `dry_run=False` and `graph_store` is provided, call
  `write_entity_enrichment()`.
- Catch `NotImplementedError` and return honest non-persisted result warnings.
- Do not catch programming errors from `compute_metrics()` unless tests define
  a safe error-reporting contract.

```python
def enrich_from_store(
    self,
    graph_store: Any,
    domain: str | None = None,
    *,
    dry_run: bool = False,
) -> GraphEnrichmentReport:
    ...
```

Behavior:

- Use `domain or self.domain`.
- Read decisions through public GraphStore read methods.
- Delegate to `enrich(..., graph_store=graph_store, dry_run=dry_run)`.
- Do not write decisions or outcomes.

### Idempotency

Default idempotency key should be deterministic, for example:

```text
{domain}:{entity_type}:{entity_id}:{namespace}:{computation_version}:{hash(decision_ids)}
```

Use stdlib hashing over sorted decision IDs/source-set content. Do not include
wall-clock timestamps in idempotency keys.

## Output Model Design

Implement frozen dataclasses or simple dataclasses with `to_dict()` helpers.

### GraphEnrichmentResult

Fields:

- `entity_id: str`
- `entity_type: str`
- `namespace: str`
- `sample_count: int`
- `metrics: dict[str, ProvenancedValue]`
- `persisted: bool`
- `receipt: EntityEnrichmentReceipt | None`
- `warnings: list[str]`

### GraphEnrichmentReport

Fields:

- `entities_enriched: int`
- `entities_skipped: int`
- `total_decisions_used: int`
- `dry_run: bool`
- `timestamp: str`
- `results: list[GraphEnrichmentResult]`
- `warnings: list[str]`
- `skipped_decisions: int`

`entities_enriched` should count entities with computed metrics, not only
persisted rows. Per-entity `persisted` and receipt fields identify write status.

## Persistence Strategy

Rules:

- If `graph_store` is provided and `dry_run=False`, use only
  `graph_store.write_entity_enrichment()`.
- If `dry_run=True`, call `write_entity_enrichment(..., dry_run=True)` when the
  method exists; otherwise return computed results with `persisted=False` and a
  warning.
- If no `graph_store` is provided, compute report only.
- If write is unsupported, return an honest per-entity warning and
  `persisted=False`; do not raise unless subclass computation itself failed.
- Do not use raw sqlite3.
- Do not use raw Cypher.
- Do not mutate node properties directly.
- Do not call legacy `write_enrichment`, `upsert_enrichment_node`, or
  `run_query`; the older DataOps service uses those paths and should remain
  reference-only for now (`apps/dataops/backend/app/services/graph_enrichment.py:38`,
  `apps/dataops/backend/app/services/graph_enrichment.py:44`,
  `apps/dataops/backend/app/services/graph_enrichment.py:50`).

## Provenance Strategy

P44 should rely on P39A provenance types rather than inventing a parallel model.

Metric rules:

- Metrics should be `ProvenancedValue` whenever written.
- Verified metrics should use `ProvenancedValue.from_verified()` only when
  computed from verified outcomes. This produces `source="verified_outcomes"`,
  `provenance_tier="learned"`, `measured=True`, and `verified=True`
  (`copilot_sdk/graph/enrichment.py:69`, `tests/test_entity_enrichment.py:41`).
- Fixture/context metrics should use `ProvenancedValue.from_fixture()` or an
  equivalent context value with `measured=False`, `verified=False`, and
  `factor_eligible=False` (`copilot_sdk/graph/enrichment.py:93`,
  `tests/test_entity_enrichment.py:51`).
- Missing/unmeasurable metrics should use `ProvenancedValue.unavailable()`
  (`copilot_sdk/graph/enrichment.py:114`, `tests/test_entity_enrichment.py:61`).
- `factor_eligible` may be carried in values but P44 must not consume it for
  scorer feedback, DK coverage gates, automation, or factor mutation.
- P44 must not implement factor feedback.

## File Plan

Allowed implementation files:

- `copilot-sdk/copilot_sdk/di/enrichment.py`
- `copilot-sdk/copilot_sdk/di/__init__.py`
- `copilot-sdk/tests/test_di_enrichment.py`
- `copilot-sdk/docs/implementation_plans/p44_di_graph_enrichment_plan.md`

Forbidden implementation files:

- `copilot-sdk/copilot_sdk/graph/*`
- `copilot-sdk/copilot_sdk/scoring/*`
- `copilot-sdk/copilot_sdk/di/models.py`
- `copilot-sdk/copilot_sdk/di/profiler.py`
- `copilot-sdk/copilot_sdk/di/nl_query.py`
- `copilot-sdk/copilot_sdk/di/query_patterns.py`
- `copilot-sdk/copilot_sdk/di/combination_discovery.py`
- `s2p-copilot/*`
- package files

## Test Plan

Create `tests/test_di_enrichment.py`.

Required tests:

1. `test_base_class_requires_group_key_and_compute_metrics`
2. `test_basic_grouping_by_entity`
3. `test_min_decisions_skip`
4. `test_none_group_key_skip`
5. `test_dry_run_no_persistence`
6. `test_compute_only_without_graph_store`
7. `test_persist_mode_calls_write_entity_enrichment`
8. `test_unsupported_write_returns_honest_warning`
9. `test_idempotent_results_ignoring_timestamp`
10. `test_build_source_set_records_decision_ids_and_counts`
11. `test_provenanced_value_metrics_roundtrip_through_fake_graphstore`
12. `test_verified_metric_provenance_boundary`
13. `test_context_metric_provenance_boundary`
14. `test_unavailable_metric_provenance_boundary`
15. `test_protected_metric_names_report_receipt_rejections`
16. `test_enrich_from_store_uses_get_verified_decisions`
17. `test_enrich_from_store_missing_read_method_safe`
18. `test_no_raw_db_or_scorer_dependency`
19. `test_di_exports_preserved`
20. `test_factor_eligible_carried_not_consumed`

Fake stores:

- A write-capable fake implementing `write_entity_enrichment()` and storing
  arguments for assertions.
- An unsupported fake whose write raises `NotImplementedError`.
- A read fake implementing `get_verified_decisions(domain)`.

Use P39A `InMemoryGraphStore` for at least one roundtrip-style test if useful,
but keep the DI tests independent from SQLite/AGE.

## Validation Plan

Run from `copilot-sdk`:

```powershell
python -m pytest tests/test_di_enrichment.py -q --timeout=120
python -m pytest tests/test_entity_enrichment.py -q --timeout=120
python -m pytest tests/ -k "di or enrichment or entity_enrichment" -q --timeout=120
python -m pytest tests/ -q --timeout=120
```

Baseline validation run during discovery:

```powershell
python -m pytest tests/ -k "di or enrichment or entity_enrichment" -q --timeout=120
```

Result:

- `241 passed, 6 skipped, 1207 deselected, 2912 warnings`

Full SDK baseline:

```powershell
python -m pytest tests/ -q --timeout=120
```

Result:

- `1392 passed, 62 skipped, 2912 warnings`

## Risks / No-Go Conditions

No-go if implementation discovers that:

- P39A GraphStore enrichment API is absent or incompatible.
- Provenance types cannot be imported safely from `copilot_sdk.graph.enrichment`.
- Implementation requires GraphStore protocol changes.
- Implementation requires raw DB access, raw Cypher, or legacy DataOps
  `run_query` enrichment paths.
- Implementation would mutate scorer, factors, conservation, outcomes, DK, or
  P39 factor-feedback surfaces.

Known limitations:

- P44 is infrastructure only. It does not provide domain metrics by itself.
- AGE entity enrichment persistence is not available unless a later adapter
  implements P39A write support.
- SDK-level reports are display/provenance infrastructure, not scoring evidence
  unless a future reviewed factor-feedback design explicitly consumes them.

## Recommended Next Prompt Summary

Implement P44 with:

- `copilot_sdk/di/enrichment.py` containing `BaseGraphEnricher`,
  `GraphEnricher`, `GraphEnrichmentResult`, and `GraphEnrichmentReport`.
- Additive exports in `copilot_sdk/di/__init__.py`.
- Tests in `tests/test_di_enrichment.py`.
- No GraphStore, scorer, conservation, DI profiler, DI NL-query,
  query-pattern, combination-discovery, S2P, or package changes.

## Implementation Addendum - 2026-06-15

Implemented files:

- Created `copilot_sdk/di/enrichment.py`.
- Created `tests/test_di_enrichment.py`.
- Updated `copilot_sdk/di/__init__.py` with additive exports.

Actual API:

- `GraphEnrichmentResult`
- `GraphEnrichmentReport`
- `BaseGraphEnricher`
- `GraphEnricher`

`BaseGraphEnricher` constructor:

```python
BaseGraphEnricher(
    *,
    domain: str,
    entity_type: str,
    namespace: str = "default",
    min_decisions: int = 5,
    computation_version: str = "",
)
```

Required hooks:

- `group_key(decision)`
- `compute_metrics(entity_id, decisions)`

Optional/default hooks:

- `build_source_set(entity_id, decisions)`
- `normalize_metric(metric_name, value, decisions)`
- `should_skip_entity(entity_id, decisions)`

Main methods:

- `enrich(decisions, *, graph_store=None, dry_run=False)`
- `enrich_from_store(graph_store, *, dry_run=False)`

P39A reuse:

- Reuses `ProvenancedValue`, `EnrichmentSourceSet`, and
  `EntityEnrichmentReceipt` from `copilot_sdk.graph.enrichment`.
- Persists only through `graph_store.write_entity_enrichment()`.
- Does not redefine GraphStore enrichment models.

Persistence behavior:

- Compute-only mode works without a graph store and marks results
  `persisted=False`.
- Persist mode calls `write_entity_enrichment()` and only reports
  `persisted=True` when the receipt confirms persistence.
- Unsupported writes return non-persisted per-entity warnings.
- Protected metric names are delegated to the P39A receipt behavior.

Dry-run behavior:

- Dry-run calls `write_entity_enrichment(..., dry_run=True)` when available so
  GraphStore validation/protected-field rejection can run.
- Dry-run never reports durable persistence.

Provenance behavior:

- Existing `ProvenancedValue` metrics are preserved.
- Raw metric values are preserved as raw values with explicit
  `raw_metric_without_provenance=<metric>` warnings; learned/verified/measured
  provenance requires a subclass to return or explicitly normalize to a
  `ProvenancedValue`.
- Fixture/context and unavailable metrics can be supplied by subclass hooks and
  retain their P39A provenance constraints.
- `factor_eligible` is carried by `ProvenancedValue` but is not consumed by P44.

Tests added:

- Basic grouping, deterministic ordering, empty input, and `None` group-key
  skips.
- `min_decisions` skips.
- Compute-only, dry-run, persist, unsupported-store behavior.
- Idempotent results ignoring timestamps.
- Source-set decision IDs/counts.
- Provenanced metric normalization and verified/context/unavailable boundaries.
- Confidence helper behavior.
- Abstract hook enforcement.
- DI export preservation.
- No GraphStore protocol/scorer import dependency.
- No raw SQL/Cypher dependency.
- Existing P39A compatibility via `InMemoryGraphStore`.
- `enrich_from_store()` verified-decision read behavior.
- Protected metric receipt rejection.
- Callable-hook `GraphEnricher`.

Validation:

```powershell
python -m pytest tests/test_di_enrichment.py -q --timeout=120
```

Result:

- `26 passed, 52 warnings`

```powershell
python -m pytest tests/test_entity_enrichment.py -q --timeout=120
```

Result:

- `41 passed, 82 warnings`

```powershell
python -m pytest tests/ -k "di or enrichment or entity_enrichment" -q --timeout=120
```

Result:

- `267 passed, 6 skipped, 1207 deselected, 2964 warnings`

```powershell
python -m pytest tests/ -q --timeout=120
```

Result:

- `1418 passed, 62 skipped, 2964 warnings`

Scope control:

- No GraphStore files changed.
- No scorer files changed.
- No conservation files changed.
- No DI models/profiler/NL/query-pattern/combination-discovery files changed.
- No S2P files changed.
- No package files changed.

Known limitations:

- P44 provides framework infrastructure only; domain-specific DataOps/S2P
  subclasses may adopt it later.
- No scheduler/background runner is included.
- No factor feedback, DK coverage gate, or scorer integration is included.
- AGE persistence remains unsupported unless a later adapter implements P39A
  write support.

## Fixer Addendum - 2026-06-15

P2 fixed:

- Generic direct `enrich(decisions)` no longer auto-promotes raw metric values to
  `ProvenancedValue.from_verified(...)`.
- Raw metrics remain raw values in `GraphEnrichmentResult.metrics`.
- Raw metrics add per-entity warnings such as
  `raw_metric_without_provenance=accuracy`.
- Only explicit subclass provenance can claim learned/verified/measured status:
  subclasses may return `ProvenancedValue.from_verified(...)` directly or
  override `normalize_metric(...)` to do so.

Skipped count semantics:

- `entities_skipped` now counts skipped entity groups only.
- Skipped decision rows from `None`/empty group keys are reported separately in
  `skipped_decisions`.
- Existing warnings still include `decisions_skipped_without_group=N`.

P39A/source-set behavior:

- Default direct caller-provided decisions are represented as unverified in the
  default `build_source_set()`.
- `enrich_from_store()` marks default source sets as verified because it reads
  through `get_verified_decisions()`.
- Subclasses can still override `build_source_set()` when they have stronger
  domain-specific provenance knowledge.

Tests updated:

- Added `test_raw_metrics_direct_enrich_are_not_auto_verified`.
- Added `test_explicit_verified_provenanced_value_passthrough`.
- Added `test_normalize_metric_override_can_claim_verified_when_explicit`.
- Added `test_entities_skipped_counts_entity_groups_not_decision_rows`.
- Updated previous raw-metric expectations so they no longer endorse generic
  verified provenance promotion.

Validation after fixer:

```powershell
python -m pytest tests/test_di_enrichment.py -q --timeout=120
```

Result:

- `29 passed, 58 warnings`

```powershell
python -m pytest tests/test_entity_enrichment.py -q --timeout=120
```

Result:

- `41 passed, 82 warnings`

```powershell
python -m pytest tests/ -k "di or enrichment or entity_enrichment" -q --timeout=120
```

Result:

- `287 passed, 6 skipped, 1207 deselected, 3004 warnings`

```powershell
python -m pytest tests/ -q --timeout=120
```

Result:

- `1438 passed, 62 skipped, 3004 warnings`

Scope control:

- No GraphStore files changed.
- No scorer files changed.
- No conservation files changed.
- No S2P files changed.
- No package files changed.
- No DI models/profiler/NL/query-pattern/combination-discovery files changed.
