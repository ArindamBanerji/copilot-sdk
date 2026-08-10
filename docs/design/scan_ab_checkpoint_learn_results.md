# Verification Scan A+B — Checkpoint and Learn Paths

**Date:** 2026-08-06  
**Type:** Read-only verification. No source, test, graph, or database writes.

## Scope and status vocabulary

- **CONFIRMED** — source or read-only runtime evidence directly supports the item.
- **CONTRADICTED** — source evidence directly conflicts with the item.
- **GAP** — the implementation or requested runtime proof was not available from the scan.

The scan used the v2 GraphStore implementations, shared scorer, SOC/S2P routes, persistence outbox, and read-only SQLite database inspection. The live Trading/Purchasing/DataOps HTTP services were not running during the runtime probe.

## SCAN A — CHECKPOINT MODEL

### V1 — Restart / null-ID behavior

**GAP — restart equivalence was not executed.** The startup loader is clear: `CompoundingScorer.from_preset()` calls `load_latest_centroids()` and falls back to bootstrap only when it returns `None` (`copilot-sdk/copilot_sdk/scoring/scorer.py:266-268`). A learn→process-restart→load experiment was not run.

Read-only counts from repository SQLite database snapshots were:

| Database snapshot | Rows in `centroid_checkpoints` | `checkpoint_id IS NULL` | Non-null ID |
|---|---:|---:|---:|
| Trading `apps/trading/backend/data/trading.db` | 5 | 5 | 0 |
| Purchasing `apps/purchasing/backend/data/purchasing.db` | 5 | 5 | 0 |
| DataOps `apps/dataops/backend/data/dataops.db` | 219 | 219 | 0 |
| S2P `copilot-sdk/data/s2p.db` | 0 | 0 | 0 |

These counts show that the inspected Trading, Purchasing, and DataOps snapshots are populated by the null-ID legacy model; they do not prove the result of a fresh restart after a new learn. No live endpoint counts were available because ports 8010, 8020, and 8030 refused connections.

### V4 — Schema and write/load paths

**CONFIRMED for schema and path inventory; GAP for full cross-adapter conformance.**

#### SQLite

The table schema is (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:441-458`):

```sql
centroid_checkpoints (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  checkpoint_id TEXT UNIQUE,
  domain TEXT NOT NULL DEFAULT '',
  decision_id TEXT,
  category TEXT,
  action TEXT,
  centroids_json TEXT NOT NULL,
  decisions_count INTEGER NOT NULL,
  verified_count INTEGER NOT NULL DEFAULT 0,
  iks REAL NOT NULL,
  shape_json TEXT NOT NULL DEFAULT '[]',
  factor_names_hash TEXT NOT NULL DEFAULT '',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at REAL NOT NULL,
  decision_time_start TEXT,
  decision_time_end TEXT,
  checkpoint_time TEXT
)
```

V2 `write_centroid_checkpoint()` accepts the complete identity, centroid tensor, counts, IKS, shape, factor-name hash, and metadata (`sqlite_store.py:1556-1569`), then inserts the row with a non-null `checkpoint_id` (`:1614-1634`). Legacy `save_centroids()` inserts the older checkpoint representation (`:2591-2624`).

`load_latest_centroids()` reads only rows with null `checkpoint_id` (`sqlite_store.py:2626-2638`). Normal checkpoint enumeration also excludes V2 rows by default because `_checkpoint_where_clause()` adds `checkpoint_id IS NULL` when `include_v2=False` (`sqlite_store.py:3474-3487`).

#### AGE

The V2 AGE node written by `write_centroid_checkpoint()` contains `checkpoint_id`, `domain`, `category`, `action`, serialized centroids, decisions/verified counts, IKS, shape, factor-name hash, metadata, `schema_version='protocol_v2'`, and `created_at` (`ci-platform/ci_platform/graph/age_graph_store.py:1356-1420`).

The AGE V2 writer also links the triggering Decision with `SNAPSHOT_AFTER` and the reverse `DERIVED_FROM` relationship (`age_graph_store.py:1103-1125,1421-1426`). This is the only directly confirmed implementation of the JM snapshot-edge write in the scanned code.

AGE legacy `save_centroids()` creates a `CentroidCheckpoint` with `decision_id`, domain, category, centroids, metadata, and created time; it optionally creates `HAS_CENTROID_CHECKPOINT` from a Decision (`age_graph_store.py:2620-2659`). It does not create a V2 `checkpoint_id` or the JM `SNAPSHOT_AFTER` edge.

AGE `load_latest_centroids()` filters `c.checkpoint_id IS NULL` (`age_graph_store.py:2661-2678`). `get_centroid_checkpoints()` also excludes V2 by default and includes it only when `include_v2=True` (`age_graph_store.py:2834-2853`).

#### InMemory

The protocol V2 method has the same required signature (`copilot-sdk/copilot_sdk/graph/protocol.py:267-280`). InMemory stores V2 rows in `_protocol_centroid_checkpoints` with a non-null ID, shape, factor-name hash, metadata, and timestamp (`copilot-sdk/copilot_sdk/graph/memory_store.py:777-815`).

Its legacy `save_centroids()` stores a separate list without a `checkpoint_id`, shape, or factor-name hash (`memory_store.py:1346-1368`). Its `load_latest_centroids()` selects the latest legacy list row by domain and does not apply a null-ID predicate (`:1370-1378`). `get_centroid_checkpoints()` includes V2 rows only when `include_v2=True` (`:1387-1419`).

### CLAIM 1 — Two writer paths

**CONFIRMED.**

1. Legacy `save_centroids()` is called by the warm-start path (`copilot-sdk/copilot_sdk/scoring/scorer.py:1514-1527`). The scorer’s checkpoint helper can also invoke it when `write_legacy=True` (`scorer.py:1767-1817`).
2. V2 `write_centroid_checkpoint()` is the default branch of `_save_centroids_checkpoint()` for a Protocol V2 store (`scorer.py:1817-1840`). It writes a generated non-null checkpoint ID, shape, and factor-name hash (`:1822-1839`).

The two paths write different representations: legacy rows are null-ID-compatible; V2 rows are identified protocol checkpoints.

### CLAIM 2 — NULL filter hides V2 rows from startup loading

**CONFIRMED for AGE and SQLite.** SQLite’s loader has `WHERE domain = ? AND checkpoint_id IS NULL` (`sqlite_store.py:2626-2638`). AGE’s loader has the equivalent predicate (`age_graph_store.py:2661-2678`). The V2 writer supplies non-null IDs (`scorer.py:1826-1839`).

**Additional evidence:** default `get_centroid_checkpoints()` also excludes V2 in both adapters; V2 is opt-in through `include_v2=True` (`sqlite_store.py:3474-3487`; `age_graph_store.py:2834-2853`).

### CLAIM 3 — Both paths exist in the scorer, so restart behavior is unproven

**CONFIRMED for path availability; GAP for the restart conclusion.** Both legacy and V2 branches are present (`scorer.py:1767-1840`), and startup precedence is checkpoint result before bootstrap (`:266-268`). However, no controlled learn/restart/load experiment was run. The inspected SQLite snapshots show legacy rows for three domains, but that is not a proof for all future writes or runtime configuration.

### CLAIM 4 — S2P calibration uses null-ID `save_centroids()` as the reference write path

**CONTRADICTED by current S2P source.** The S2P route’s L5 persistence calls `store.update_centroid(...)` (`s2p-copilot/backend/app/routers/s2p.py:656-709`), and the `/learn` path invokes the shared scorer, then L5 centroid persistence (`s2p-copilot/backend/app/routers/s2p.py:2141-2185,2187-2203`). No S2P backend call to `save_centroids()` was found.

The shared scorer’s V2 checkpoint helper defaults to `write_legacy=False` and calls `write_centroid_checkpoint()` for Protocol V2 stores (`copilot-sdk/copilot_sdk/scoring/scorer.py:1779-1821,1826-1839`). Therefore, the current source does not establish null-ID `save_centroids()` as S2P’s calibration reference path.

### CLAIM 5 — SOC has no checkpoint writer

**CONFIRMED in the SOC backend for `CentroidCheckpoint` writers; qualified by a separate L5 writer.** The SOC verify/learn path imports and invokes `persist_soc_centroid()` (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2088-2095,2241-2269`). That function calls `store.update_centroid()` for the `L5Centroid` state (`gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:396-437`), not `save_centroids()` or `write_centroid_checkpoint()`.

The SOC centroid-evolution route reads `Decision.centroid_delta_norm` rather than `CentroidCheckpoint` rows (`gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:107-153`). No SOC backend call to either checkpoint writer was found.

## SCAN B — LEARN / TRANSACTION PATH

### V5 — Atomic SOC verify→learn→persist

**GAP / NOT CONFIRMED.** The SOC route serializes access to the in-memory scorer with `async with _acquire_scorer()` and calls `guarded_update()` (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2115-2171`). It then performs persistence artifacts, centroid persistence, DK tracking, and later response/state work as separate calls (`:2188-2241`).

The SOC centroid persistence function performs a separate `store.update_centroid()` call (`gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:425-437`). The scanned triage path contains no transaction boundary that encloses the scorer update, decision/outcome write, centroid write, and artifact writes as one database transaction. The lock is an application concurrency guard, not evidence of database atomicity. AGE has transaction-capable code elsewhere, but no proof was found that this complete SOC verify→learn sequence is passed through one transaction.

### Shared scorer learn sequence

The shared `CompoundingScorer.learn()` performs the in-memory scorer update (`copilot-sdk/copilot_sdk/scoring/scorer.py:690-713`), writes the outcome (`:722-728`), and later writes the centroid checkpoint (`:760-789`) plus other artifacts (`:810-821`). These are separate method calls; no transaction context spans them. SQLite’s `_run_write()` commits each individual operation (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:978-996`).

### S2P learn sequence

**GAP for database atomicity.** S2P places the route under `get_mutation_lock("s2p")` (`s2p-copilot/backend/app/routers/s2p.py:2156-2185`), then invokes the shared scorer and separately persists L5 centroid and conservation state (`:2187-2203`). The lock prevents concurrent route mutations but the source does not show one transaction spanning outcome, centroid, conservation, evidence, and DK writes.

### CLAIM 6 — Learning update path is not verified to be atomic

**CONFIRMED as an implementation gap at the orchestration level.** The SOC and shared scorer paths use locks/ordered calls, but the scanned paths do not wrap the full learning mutation and all dependent persistence in one transaction (`triage.py:2115-2241`; `scorer.py:690-821`). Individual SQLite writes are transactionally committed by `_run_write()`, which is weaker than a single cross-artifact transaction (`sqlite_store.py:978-996`).

This does not assert that every individual AGE or SQLite write is non-atomic; it asserts that the complete verify→learn→persist workflow is not shown to be atomic.

### V6 — §12b fail-closed and outbox

**GAP — partial implementation confirmed, full end-to-end fail-closed behavior not proven.**

- `PersistenceOutbox` exists at `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:36-66` and creates a SQLite `failed_artifacts` table (`:58-66`). Its default path is `~/.ci-platform/<domain>/outbox.db`, configurable by `CI_PERSISTENCE_OUTBOX_PATH` (`:41-56`).
- The scorer creates and drains the outbox at startup (`copilot-sdk/copilot_sdk/scoring/scorer.py:166-173`). Centroid-checkpoint failures are recorded for replay (`:1841-1856`), and replay dispatches `centroid_checkpoint` to `write_centroid_checkpoint()` (`persistence_outbox.py:299-324`).
- Outcome is explicitly not deferrable: `enqueue("outcome", ...)` raises `ValueError` (`persistence_outbox.py:193-202`). The source-level invariant test verifies no outcome replay/defer path (`copilot-sdk/tests/scoring/test_persistence_outbox.py:448-458`), and a direct enqueue test verifies the fail-closed exception (`:274-278`).
- No test named `test_learn_remains_fail_closed` was found. No end-to-end AGE-unavailable `/learn` or `/outcome` execution was run in this read-only scan.

Thus the outbox and outcome non-deferral are **CONFIRMED**, while the complete §12b learn/outcome runtime behavior remains a **GAP**.

## InMemory DIVERGENCE — V13

**CONFIRMED.** The following methods differ materially from AGE/SQLite:

1. `save_centroids()` stores legacy rows in a Python list with no `checkpoint_id`, no `shape`, and no `factor_names_hash` (`copilot-sdk/copilot_sdk/graph/memory_store.py:1346-1368`). AGE/SQLite legacy rows also omit or default some V2 fields, but their durable schemas include checkpoint columns/fields (`sqlite_store.py:441-458`; AGE V2 schema `age_graph_store.py:1375-1417`).
2. `load_latest_centroids()` selects the last legacy in-memory row for the domain without a null-ID predicate (`memory_store.py:1370-1378`). AGE/SQLite explicitly require `checkpoint_id IS NULL` (`age_graph_store.py:2661-2678`; `sqlite_store.py:2626-2638`).
3. InMemory V2 rows are kept in a separate `_protocol_centroid_checkpoints` dictionary and are included in history only with `include_v2=True` (`memory_store.py:777-815,1387-1419`). AGE/SQLite likewise default history to legacy rows, but AGE additionally supports JM edge creation for V2 (`age_graph_store.py:1103-1125,1421-1426`); InMemory has no graph traversal or `SNAPSHOT_AFTER` edge.
4. InMemory `update_centroid()` updates an in-memory `_l5_centroids` map (`memory_store.py:1182-1205`); it is not a durable checkpoint write and does not create lineage edges.

## ADDITIONAL FINDINGS

1. The V2 AGE adapter does implement JM lineage edges, but the current SDK SQLite adapter has no corresponding `SNAPSHOT_AFTER` relationship model. This makes “V2 exists” different from “V2 is JM-conformant” across backends (`age_graph_store.py:1103-1125`; SQLite schema `sqlite_store.py:441-458`).
2. Both AGE and SQLite default history readers exclude V2 rows, not only startup loaders. The `include_v2` switch is therefore an explicit namespace/precedence boundary (`sqlite_store.py:3474-3487`; `age_graph_store.py:2834-2853`).
3. `write_centroid_checkpoint()` computes and stores a factor-name hash in the V2 payload (`scorer.py:1822-1837`), but the startup `load_latest_centroids()` implementations shown here do not validate shape or factor-name hash before returning centroids (`sqlite_store.py:2626-2638`; `age_graph_store.py:2661-2678`).
4. The demo bundle restore is explicitly SQLite-only at write time and logs that AGE migration is required when `GRAPH_BACKEND` is `age` or `dual_write` (`copilot-sdk/copilot_sdk/demo/bundle.py:1,58-69,145-155`).
5. The legacy warm-start path writes `save_centroids()` with category `"warm_start"` (`copilot-sdk/copilot_sdk/scoring/scorer.py:1514-1527`), so null-ID rows are not only a historical compatibility artifact; there remains a live caller.
6. The inspected persistent snapshots show null-ID rows in Trading, Purchasing, and DataOps, while S2P’s inspected `s2p.db` has no checkpoint rows. This is evidence of current stored state, not a substitute for the requested restart experiment.

## Cleanup

No scratch scripts were created. No source, test, graph, or database was modified. SQLite inspection used read-only connections; no live service was available for a learn/restart test.
