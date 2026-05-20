# GS-BITEMPORAL Architecture Plan

## 1. Executive Summary

Current state: centroid checkpoints are persisted through the SDK `GraphStore` protocol with `decision_id`, `category`, `centroids`, and optional `metadata` only. The protocol signature is `save_centroids(decision_id, category, centroids, metadata=None)` and checkpoint reads are `get_centroid_checkpoints(limit=50)` (`copilot_sdk/graph/protocol.py:54-64`). SQLite currently stores checkpoint rows with `created_at` as a wall-clock float (`copilot_sdk/scoring/storage.py:67-76`, `copilot_sdk/scoring/storage.py:172-198`). InMemory stores `created_at` as a UTC ISO string (`copilot_sdk/graph/memory_store.py:112-127`). ci-platform's AGE adapter stores checkpoint nodes with `created_at` as UTC ISO text (`ci_platform/graph/age_graph_store.py:206-236`).

Target state: add additive bi-temporal metadata to centroid checkpoints:

- `decision_time_start`: earliest decision timestamp that contributed to the checkpoint.
- `decision_time_end`: latest decision timestamp that contributed to the checkpoint.
- `checkpoint_time`: UTC ISO timestamp when the checkpoint was computed/persisted.

Classification: `PLAN_READY`.

This is plan-only. No source, test, schema, or ci-platform files were changed. SDK implementation should happen first. ci-platform AGE changes are documented here but deferred to a separate implementation prompt because ci-platform is a separate repo and is read-only for this task.

## 2. Current Architecture

### GraphStore Protocol

The active graph protocol is `copilot_sdk/graph/protocol.py`; there is no `copilot_sdk/graph/graph_store.py` file in the SDK checkout. `GraphStore` is a runtime-checkable `Protocol` (`copilot_sdk/graph/protocol.py:8-10`). It requires `save_centroids(decision_id, category, centroids, metadata=None)` (`copilot_sdk/graph/protocol.py:54-60`) and `get_centroid_checkpoints(limit=50)` (`copilot_sdk/graph/protocol.py:63-64`). Protocol tests assert the protocol is runtime-checkable and that `save_centroids` and `get_centroid_checkpoints` exist (`tests/graph/test_protocol.py:6-8`, `tests/graph/test_protocol.py:31-36`).

### SQLiteGraphStore and DecisionStore

`SQLiteGraphStore.save_centroids()` has the same protocol-facing signature and delegates to `DecisionStore.save_centroids()` with `decision_id`, `category`, and metadata (`copilot_sdk/graph/sqlite_store.py:137-155`). `SQLiteGraphStore.get_centroid_checkpoints()` delegates to `DecisionStore.get_centroid_checkpoints()` (`copilot_sdk/graph/sqlite_store.py:157-162`).

The SQLite checkpoint schema currently has columns `id`, `decision_id`, `category`, `centroids_json`, `decisions_count`, `iks`, `metadata_json`, and `created_at` (`copilot_sdk/scoring/storage.py:67-76`). The current migration helper `_ensure_centroid_columns()` adds missing checkpoint columns idempotently with `ALTER TABLE` (`copilot_sdk/scoring/storage.py:91-103`), which is the pattern to extend for bi-temporal fields.

`DecisionStore.save_centroids()` stores `created_at` as `time.time()` and persists JSON-encoded centroids and metadata (`copilot_sdk/scoring/storage.py:172-198`). `DecisionStore.get_centroid_checkpoints()` returns checkpoints in ascending created order, limiting by newest rows then reversing when a limit is supplied (`copilot_sdk/scoring/storage.py:237-254`). Its return dict includes `id`, `decision_id`, `category`, `centroids`, `decisions_count`, `iks`, `metadata`, and `created_at` (`copilot_sdk/scoring/storage.py:255-265`).

Existing SQLite tests assert save/read shape, order, limit, and JSON round-trip (`tests/graph/test_sqlite_store.py:75-129`). `DecisionStore` tests assert latest checkpoint loading, checkpoint metadata, and limit behavior (`tests/scoring/test_storage.py:78-122`).

### InMemoryGraphStore

`InMemoryGraphStore` keeps checkpoint state in an instance-local `_centroid_checkpoints` list (`copilot_sdk/graph/memory_store.py:15-22`). `save_centroids()` stores a checkpoint dict with `decision_id`, `category`, `centroids`, `metadata`, and `created_at` (`copilot_sdk/graph/memory_store.py:112-127`). `get_centroid_checkpoints(limit=50)` returns a deep copy of the last `limit` checkpoints (`copilot_sdk/graph/memory_store.py:129-133`). Tests assert shape, `created_at`, limit, reset, and copy safety (`tests/graph/test_memory_store.py:87-141`).

### AGEGraphStore in ci-platform

ci-platform has a GraphStore-compatible AGE adapter (`ci_platform/graph/age_graph_store.py:1-17`). It imports `AGEClient` (`ci_platform/graph/age_graph_store.py:13`) and constructs a client in `__init__` (`ci_platform/graph/age_graph_store.py:19-20`). Its `save_centroids()` signature matches the SDK protocol today (`ci_platform/graph/age_graph_store.py:206-212`). It serializes centroid and metadata JSON, sets `created_at` to `datetime.now(timezone.utc).isoformat()`, and creates a `CentroidCheckpoint` node linked to a `Decision` when possible (`ci_platform/graph/age_graph_store.py:213-236`). It reads checkpoints with `MATCH (c:CentroidCheckpoint)`, orders by `c.created_at DESC`, limits, and reverses to chronological order (`ci_platform/graph/age_graph_store.py:362-373`).

AGE query constraints are explicit in `AGEClient`: Cypher datetime functions are not supported and Python datetime/timedelta should be used (`ci_platform/graph/age_client.py:8-12`); `MERGE` is unsupported and code should use match-then-create patterns (`ci_platform/graph/age_client.py:13`, `ci_platform/graph/age_client.py:53-69`). This means AGE bi-temporal implementation should store Python-generated ISO strings as properties and avoid Cypher datetime functions.

### CompoundingScorer Save Paths

`CompoundingScorer.__init__` already supports consolidation and stores instance-local `_batch_decision_count` and checkpoint identity fields (`copilot_sdk/scoring/scorer.py:98-119`). `score()` writes decision metadata including `created_at: time.time()` (`copilot_sdk/scoring/scorer.py:200-209`) and writes decisions through the graph store (`copilot_sdk/scoring/scorer.py:210-217`). `learn()` has `consolidate: bool = False` and writes outcome metadata with `verified_at: time.time()` (`copilot_sdk/scoring/scorer.py:230-300`).

Checkpoint persistence happens after successful centroid update and outcome write. With consolidation enabled, `learn()` increments `_batch_decision_count` and either saves on `consolidate=True` or buffers persistence; with consolidation disabled it saves every successful learn (`copilot_sdk/scoring/scorer.py:305-327`). `flush_centroids()` saves the buffered checkpoint and resets `_batch_decision_count` (`copilot_sdk/scoring/scorer.py:368-383`). `_save_centroids_checkpoint()` constructs metadata and calls `self._graph_store.save_centroids(decision_id, category, self._scorer.centroids, metadata=metadata)` (`copilot_sdk/scoring/scorer.py:634-656`). Warm-start also saves centroids through the graph store with metadata (`copilot_sdk/scoring/scorer.py:461-475`).

GS-CONSOLIDATE tests prove default behavior saves every successful learn, consolidation buffers persistence, `consolidate=True` saves metadata, `flush_centroids()` saves and resets count, and outcome writes still run while buffered (`tests/test_consolidation.py:68-92`, `tests/test_consolidation.py:109-143`, `tests/test_consolidation.py:178-192`).

### Checkpoint Consumers

`CompoundingScorer.trajectory()` calls `self._graph_store.get_centroid_checkpoints()` and returns the checkpoint list (`copilot_sdk/scoring/scorer.py:385-390`). The SDK self-computation backend exposes `/api/self/centroid-history` with only `limit`; it calls `get_centroid_checkpoints(limit=limit)` and returns JSON-safe checkpoints (`copilot_sdk/backend/self_computation_router.py:19-23`). The transfer router finds latest checkpoints with `get_centroid_checkpoints(limit=10)` and reads `created_at` or `timestamp` for status output (`copilot_sdk/backend/transfer_router.py:36-58`). A DataOps app endpoint named `/centroid-history` computes local decision-derived snapshots rather than GraphStore checkpoints (`apps/dataops/backend/app/context_router.py:972-1003`) and should not be part of the initial SDK implementation.

### Timestamp Availability

Decision timestamps are available today as `created_at`. `CompoundingScorer.score()` puts `created_at: time.time()` into graph decision metadata (`copilot_sdk/scoring/scorer.py:200-209`). `SQLiteGraphStore.write_decision()` passes metadata `created_at` to `DecisionStore.save_decision()` (`copilot_sdk/graph/sqlite_store.py:21-61`). `InMemoryGraphStore.write_decision()` stores `created_at` from metadata or `time.time()` (`copilot_sdk/graph/memory_store.py:24-52`). `DecisionStore.save_decision()` stores `created_at` as a float epoch timestamp (`copilot_sdk/scoring/storage.py:105-142`). `SQLiteGraphStore._normalize_decision()` preserves decision metadata in returned decision dicts (`copilot_sdk/graph/sqlite_store.py:266-276`), and `CompoundingScorer._decision_field()` can read fields from top-level, metadata, and nested factors metadata (`copilot_sdk/scoring/scorer.py:795-806`).

## 3. Bi-Temporal Model

Represent bi-temporal checkpoint metadata as additive explicit fields:

- `decision_time_start: str | None`
- `decision_time_end: str | None`
- `checkpoint_time: str | None`

The plan chooses explicit fields rather than a tuple because current storage implementations expose flat dict rows (`copilot_sdk/scoring/storage.py:255-265`, `copilot_sdk/graph/memory_store.py:120-126`) and SQLite migrations add columns independently (`copilot_sdk/scoring/storage.py:91-103`). Explicit fields also translate directly to AGE node properties (`ci_platform/graph/age_graph_store.py:218-225`).

Semantics:

- `decision_time_start` and `decision_time_end` describe the decision-time span of decisions that contributed to the checkpoint.
- `checkpoint_time` describes when the checkpoint was computed/persisted.
- All three values should be normalized UTC ISO 8601 strings ending in `Z`, or `None`.
- Existing `created_at` fields remain for compatibility and are not redefined.
- When existing callers do not provide new bi-temporal arguments, call signatures and persistence frequency remain unchanged. New checkpoint rows should still receive a generated `checkpoint_time` at save time; legacy rows created before the migration may return `None` for additive bi-temporal fields.
- Do not use host wall-clock for `decision_time_start` or `decision_time_end` unless no decision timestamp exists and the implementation explicitly documents the fallback. Prefer decision metadata, then stored decision `created_at`, then `None`.
- `checkpoint_time` is generated at checkpoint persistence time using Python UTC time because it is a persistence/computation timestamp, and AGE cannot rely on Cypher datetime functions (`ci_platform/graph/age_client.py:8-12`).

## 4. Protocol Change

Use a backward-compatible keyword-only extension:

```python
def save_centroids(
    self,
    decision_id: str,
    category: str,
    centroids: Any,
    metadata: dict[str, Any] | None = None,
    *,
    decision_time_start: str | None = None,
    decision_time_end: str | None = None,
    checkpoint_time: str | None = None,
) -> None: ...
```

The first four parameters stay unchanged, preserving current callers such as `CompoundingScorer._save_centroids_checkpoint()` (`copilot_sdk/scoring/scorer.py:651-655`), warm-start (`copilot_sdk/scoring/scorer.py:461-475`), and graph store tests (`tests/graph/test_sqlite_store.py:78-83`, `tests/graph/test_memory_store.py:90-95`). New parameters are keyword-only to prevent accidental positional protocol drift.

Extend reads with keyword-only optional filters:

```python
def get_centroid_checkpoints(
    self,
    limit: int = 50,
    *,
    checkpoint_time_start: str | None = None,
    checkpoint_time_end: str | None = None,
    decision_time_start: str | None = None,
    decision_time_end: str | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]: ...
```

Filter semantics:

- No filters returns current behavior.
- `checkpoint_time_start/end` include checkpoints whose `checkpoint_time` falls inside the inclusive range.
- `decision_time_start/end` include checkpoints whose decision span is contained in the inclusive query window: checkpoint `decision_time_start >= query_start` when start is supplied, and checkpoint `decision_time_end <= query_end` when end is supplied.
- Temporal filters exclude old checkpoints with `NULL`/missing time fields, avoiding false matches for unknown time.
- `category` is additive and optional; it aligns with existing checkpoint category fields in all stores (`copilot_sdk/scoring/storage.py:67-76`, `copilot_sdk/graph/memory_store.py:121-124`, `ci_platform/graph/age_graph_store.py:220-224`).

`DecisionStore.save_centroids()` should receive analogous keyword-only fields after existing keyword-only `metadata` because its current signature already uses keyword-only `decision_id`, `category`, and `metadata` (`copilot_sdk/scoring/storage.py:172-179`).

## 5. SQLiteGraphStore Design

SQLite changes:

- Add nullable `TEXT` columns to `centroid_checkpoints`:
  - `decision_time_start`
  - `decision_time_end`
  - `checkpoint_time`
- Preserve `created_at REAL NOT NULL` for existing ordering and compatibility (`copilot_sdk/scoring/storage.py:67-76`, `copilot_sdk/scoring/storage.py:195-196`).
- Extend `_ensure_centroid_columns()` using the existing idempotent `PRAGMA table_info` plus `ALTER TABLE ADD COLUMN` pattern (`copilot_sdk/scoring/storage.py:91-103`).
- Add `CREATE INDEX IF NOT EXISTS` indexes:
  - `idx_centroid_checkpoints_checkpoint_time(checkpoint_time)`
  - `idx_centroid_checkpoints_decision_time(decision_time_start, decision_time_end)`
  - `idx_centroid_checkpoints_category(category)` if category filtering is implemented.

Serialization:

- Store new bi-temporal values as UTC ISO strings in `TEXT`.
- If `checkpoint_time` is not supplied, generate it at save time with a UTC helper.
- If decision-time fields are omitted, store `NULL`.

Query behavior:

- `DecisionStore.get_centroid_checkpoints()` should keep no-filter ordering and limit semantics because tests assert chronological results and newest-limited results (`tests/scoring/test_storage.py:109-122`, `tests/graph/test_sqlite_store.py:94-118`).
- Apply filters before limit.
- Continue returning additive dict keys `decision_time_start`, `decision_time_end`, and `checkpoint_time` along with current keys (`copilot_sdk/scoring/storage.py:255-265`).
- Existing tests that compare exact fields should be updated only if they assert complete dict equality. Current checkpoint tests assert selected fields (`tests/graph/test_sqlite_store.py:85-91`, `tests/scoring/test_storage.py:101-106`), so additive keys should be safe.

Migration tests:

- Open an existing DB created with the old schema and verify the idempotent migration adds nullable columns.
- Verify old rows with null bi-temporal fields still read without filters.
- Verify filtered temporal queries exclude rows with null temporal fields.

## 6. InMemoryGraphStore Design

Extend `InMemoryGraphStore.save_centroids()` with the same keyword-only optional fields. Store additive keys on each checkpoint dict:

- `decision_time_start`
- `decision_time_end`
- `checkpoint_time`

Keep current fields unchanged (`decision_id`, `category`, `centroids`, `metadata`, `created_at`) because tests assert these keys and copy behavior (`tests/graph/test_memory_store.py:97-103`, `tests/graph/test_memory_store.py:132-141`). If `checkpoint_time` is omitted, generate UTC ISO at save time; `created_at` remains for compatibility.

Extend `get_centroid_checkpoints()` with the same optional filters as SQLite. Filtering should operate on a copied or local list before slicing so the stored checkpoints remain immutable to callers. Existing no-filter limit behavior must remain: last N chronological checkpoints (`copilot_sdk/graph/memory_store.py:129-133`, `tests/graph/test_memory_store.py:106-116`).

## 7. AGEGraphStore / ci-platform Design

ci-platform implementation is deferred to a separate prompt. It must not be implemented from the SDK prompt because this task permits only SDK-local documentation changes and ci-platform is a separate read-only reference repo.

Required ci-platform changes when prompted:

- Extend `AGEGraphStore.save_centroids()` with the same keyword-only optional fields after `metadata` (`ci_platform/graph/age_graph_store.py:206-212`).
- Add `decision_time_start`, `decision_time_end`, and `checkpoint_time` properties to `CentroidCheckpoint` nodes alongside current `decision_id`, `category`, `centroids`, `metadata`, and `created_at` properties (`ci_platform/graph/age_graph_store.py:218-225`).
- If `checkpoint_time` is omitted, generate it in Python UTC. AGEClient explicitly documents that Cypher datetime functions are not supported (`ci_platform/graph/age_client.py:8-12`).
- Extend `get_centroid_checkpoints()` with optional filters while preserving current no-filter ordering and limit behavior (`ci_platform/graph/age_graph_store.py:362-373`).
- Avoid `MERGE`; AGEClient rejects `MERGE` and requires match-then-create patterns (`ci_platform/graph/age_client.py:13`, `ci_platform/graph/age_client.py:53-69`).
- Keep query construction consistent with existing AGEGraphStore style: use `_S()` for string literals (`ci_platform/graph/age_graph_store.py:43-44`) and `_safe_limit()` for limits (`ci_platform/graph/age_graph_store.py:46-52`).

## 8. CompoundingScorer Integration

Decision timestamp extraction:

1. Prefer explicit decision-time metadata keys if present: `decision_time`, `event_time`, or `timestamp`.
2. Fall back to decision `created_at`, which `score()` writes to decision metadata (`copilot_sdk/scoring/scorer.py:200-209`) and both SDK stores persist (`copilot_sdk/graph/sqlite_store.py:21-61`, `copilot_sdk/graph/memory_store.py:24-52`).
3. Normalize float epoch, int epoch, and ISO strings to UTC ISO `Z`.
4. If no timestamp can be found, pass `None` rather than substituting wall-clock decision time silently.

Non-consolidated behavior:

- Each successful `learn()` checkpoint uses `decision_time_start == decision_time_end == current decision timestamp`.
- `checkpoint_time` is generated at `_save_centroids_checkpoint()` time.
- Default persistence frequency stays unchanged: consolidation disabled saves every successful learn (`copilot_sdk/scoring/scorer.py:322-327`, `tests/test_consolidation.py:68-80`).

GS-CONSOLIDATE behavior:

- Add instance-local `_batch_decision_time_start` and `_batch_decision_time_end`.
- Each successful `learn()` updates the in-memory batch range even when checkpoint persistence is buffered.
- `consolidate=True` passes the accumulated range into `_save_centroids_checkpoint()` and resets the range after saving.
- `flush_centroids()` passes the accumulated range, then resets range and count together.
- `flush_centroids()` with no buffered decisions still returns `0` and does not save (`copilot_sdk/scoring/scorer.py:368-383`, `tests/test_consolidation.py:147-152`).

Warm-start behavior:

- Warm-start checkpoint saves have no decision range unless the warm-start source metadata includes one. They should pass `decision_time_start=None` and `decision_time_end=None`, with `checkpoint_time` generated at persistence (`copilot_sdk/scoring/scorer.py:461-475`).

Do not change centroid update math, conflict detection, conservation, or learning gates. `learn()` currently performs conflict detection, conservation pause, centroid update, outcome write, and checkpoint logic in that order (`copilot_sdk/scoring/scorer.py:251-327`); bi-temporal metadata belongs only to the checkpoint persistence boundary.

## 9. Self-Computation / Endpoint Updates

SDK self-computation endpoint:

- Extend `/api/self/centroid-history` to accept optional query params:
  - `checkpoint_time_start`
  - `checkpoint_time_end`
  - `decision_time_start`
  - `decision_time_end`
  - `category`
- Preserve current no-filter behavior: `limit` only, returns checkpoint list and total (`copilot_sdk/backend/self_computation_router.py:19-23`).
- Pass filters through to `get_centroid_checkpoints()`.

Transfer router:

- Keep current behavior initially. It reads recent checkpoints with `limit=10` and surfaces `created_at` or `timestamp` (`copilot_sdk/backend/transfer_router.py:36-58`).
- A later compatibility polish may prefer `checkpoint_time` for status timestamps while preserving fallback to `created_at`.

Apps:

- No frontend changes in the initial implementation.
- The DataOps `/api/context/centroid-history` endpoint is app-local and decision-derived (`apps/dataops/backend/app/context_router.py:972-1003`), not the SDK checkpoint history path, so it should not be changed in the SDK bi-temporal implementation.

## 10. What Does NOT Change

- Conservation law and conservation router behavior do not change. The conservation router computes status from decision/outcome counts and graph-store count methods, not centroid checkpoints (`copilot_sdk/backend/conservation_router.py:45-60`, `copilot_sdk/backend/conservation_router.py:100-144`).
- GS-CONFLICT detection does not change.
- Fingerprint and centroid update math do not change.
- Existing `save_centroids()` callers still work because new parameters are optional and keyword-only.
- Existing `get_centroid_checkpoints(limit=...)` callers still work because filters are optional.
- No new datastore is introduced.
- No frontend changes are part of the initial SDK implementation.
- SDK does not import or modify ci-platform.

## 11. Test Plan

Protocol and compatibility:

- `test_graph_store_protocol_accepts_bitemporal_keywords`
- `test_existing_save_centroids_callers_still_work`
- `test_get_centroid_checkpoints_without_filters_returns_all_current_shape`

SQLite:

- `test_sqlite_save_without_bitemporal_params_works`
- `test_sqlite_save_without_checkpoint_time_generates_utc_iso_checkpoint_time`
- `test_sqlite_save_with_bitemporal_params_stores_fields`
- `test_sqlite_existing_db_migrates_bitemporal_columns`
- `test_sqlite_checkpoint_time_filters`
- `test_sqlite_decision_time_filters`
- `test_sqlite_temporal_filters_exclude_unknown_null_rows`
- `test_sqlite_category_filter`
- `test_sqlite_no_filter_limit_order_unchanged`

InMemory:

- `test_memory_save_without_bitemporal_params_works`
- `test_memory_save_without_checkpoint_time_generates_utc_iso_checkpoint_time`
- `test_memory_save_with_bitemporal_params_stores_fields`
- `test_memory_checkpoint_time_filters_match_sqlite_semantics`
- `test_memory_decision_time_filters_match_sqlite_semantics`
- `test_memory_no_filter_limit_order_unchanged`

CompoundingScorer:

- `test_scorer_learn_checkpoint_has_per_decision_time_range`
- `test_scorer_uses_decision_metadata_timestamp_when_present`
- `test_scorer_missing_decision_timestamp_keeps_decision_range_none`
- `test_consolidation_flush_passes_batch_decision_time_range`
- `test_consolidate_true_passes_batch_decision_time_range`
- `test_warm_start_checkpoint_has_checkpoint_time_and_null_decision_range`
- `test_conservation_router_has_no_bitemporal_dependency`

Endpoint:

- `test_self_centroid_history_accepts_checkpoint_time_filters`
- `test_self_centroid_history_accepts_decision_time_filters`
- `test_self_centroid_history_without_filters_unchanged`

ci-platform:

- AGE tests are deferred to a separate ci-platform implementation prompt. They should cover AGE property persistence, filtered reads, no-filter backward compatibility, and AGE query constraints.

## 12. Implementation Sequence

1. SDK Prompt 1: protocol + InMemoryGraphStore + compatibility tests.
2. SDK Prompt 2: DecisionStore/SQLiteGraphStore schema migration + filters + SQLite tests.
3. SDK Prompt 3: CompoundingScorer timestamp extraction, consolidation batch range integration, and scorer tests.
4. SDK Prompt 4: self-computation endpoint filters and backend tests.
5. ci-platform Prompt 5: AGEGraphStore bi-temporal fields and filters, using AGE-safe query patterns.
6. GPT-5.5 holistic review.

This split keeps protocol/implementation/storage/scorer/API changes reviewable and avoids cross-repo edits in a single prompt.

## 13. Risks and Mitigations

- Protocol break across structural implementations: use optional keyword-only parameters and update all SDK implementations in the same SDK prompt.
- SQLite migration risk: extend the existing idempotent `_ensure_centroid_columns()` pattern (`copilot_sdk/scoring/storage.py:91-103`) and add old-DB migration tests.
- Timestamp format inconsistency: normalize new fields to UTC ISO `Z`; leave existing `created_at` compatibility fields unchanged.
- Host wall-clock misuse for decision range: only use wall-clock for `checkpoint_time`; decision range comes from decision metadata or remains `None`.
- Query filter ambiguity: document inclusive contained-range semantics and test SQLite/InMemory parity.
- AGE query compatibility: defer implementation and use Python timestamps, `_S()` literals, `_safe_limit()`, and match-then-create patterns (`ci_platform/graph/age_client.py:8-13`, `ci_platform/graph/age_graph_store.py:43-52`).
- GS-CONSOLIDATE batch range off-by-one: update range on each successful learn after decision lookup and reset only after save; add flush and consolidate tests.
- Return-shape breakage: fields are additive; no existing consumer should require exact checkpoint dict equality based on current tests (`tests/graph/test_sqlite_store.py:85-91`, `tests/graph/test_memory_store.py:97-103`).
- Performance/indexing: add checkpoint and decision-time indexes for SQLite; AGE filtering performance can be evaluated separately.
- Old databases with null fields: no-filter reads include old rows; temporal filters exclude unknown/null rows.

## 14. Reading Log

- `CLAUDE.md:1-58` - repository grounding contract and no-git instruction.
- `copilot_sdk/graph/protocol.py:1-76` - GraphStore protocol and checkpoint signatures.
- `copilot_sdk/graph/sqlite_store.py:1-276` - SQLiteGraphStore decision, outcome, centroid, and normalization methods.
- `copilot_sdk/graph/memory_store.py:1-190` - InMemoryGraphStore checkpoint storage and reads.
- `copilot_sdk/scoring/storage.py:1-330` - DecisionStore schema, migrations, checkpoint persistence, and checkpoint reads.
- `copilot_sdk/scoring/scorer.py:1-820` - CompoundingScorer score, learn, consolidation, flush, warm-start, and checkpoint save paths.
- `copilot_sdk/scoring/config.py:1-51` - DomainShape and preset protocol.
- `copilot_sdk/backend/conservation_router.py:1-181` - conservation status/count path.
- `copilot_sdk/backend/self_computation_router.py:1-180` - checkpoint history endpoint consumer.
- `copilot_sdk/backend/transfer_router.py:1-105` - checkpoint status consumer.
- `apps/dataops/backend/app/context_router.py:540-566,972-1003` - app-local centroid-history endpoint.
- `tests/graph/test_protocol.py:1-40` - protocol method tests.
- `tests/graph/test_sqlite_store.py:75-129` - SQLite checkpoint tests.
- `tests/graph/test_memory_store.py:87-141` - memory checkpoint tests.
- `tests/scoring/test_storage.py:78-122` - DecisionStore checkpoint tests.
- `tests/test_consolidation.py:1-220` - GS-CONSOLIDATE behavior tests.
- `ci_platform/graph/age_graph_store.py:1-454` - AGEGraphStore checkpoint implementation and read path.
- `ci_platform/graph/age_client.py:1-180` - AGE dialect constraints and query safety.

## Prompt Verification Pass

- All SDK `save_centroids()` implementations were identified: protocol, SQLiteGraphStore/DecisionStore, and InMemoryGraphStore.
- The ci-platform AGE implementation was inspected and deferred to a separate ci-platform prompt.
- `get_centroid_checkpoints()` consumers were identified in scorer trajectory, self-computation router, transfer router, tests, and app-local DataOps history.
- The protocol change is backward-compatible through optional keyword-only parameters.
- SQLite migration strategy is idempotent and follows the existing column-add migration pattern.
- InMemory and SQLite filter semantics are specified to match.
- GS-CONSOLIDATE interaction is documented with batch decision-time range state.
- Conservation is explicitly out of scope and remains decision/outcome count based.
- No source, test, app, config, or ci-platform files were changed.
