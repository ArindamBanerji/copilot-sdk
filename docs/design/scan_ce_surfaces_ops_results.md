# Verification Scan C+E — Surfaces, DI Timeline, Operations, and Consumers

**Date:** 2026-08-06  
**Type:** Read-only verification. No source, test, graph, or database writes.

Status labels: **CONFIRMED** = directly supported by source/runtime evidence; **CONTRADICTED** = source conflicts with the claim; **GAP** = not established by the available scan.

## SCAN C — SURFACES

### D1 — Shared route

**CONFIRMED.** The shared router defines `GET /api/self/centroid-history` with `limit` and time/category filters (`copilot-sdk/copilot_sdk/backend/self_computation_router.py:19-51`). DataOps mounts it at `main.py:749`. The frontend calls it at `copilot-sdk/apps/dataops/frontend/src/api.ts:410-414`.

### D2 — Shared response shape

**CONTRADICTED as a cross-surface claim; CONFIRMED for the shared DataOps panel’s envelope.** The shared Pydantic model supplies only `checkpoints` and `total` (`copilot-sdk/copilot_sdk/backend/models.py:177-179`), and the route returns those fields (`self_computation_router.py:49-51`). The panel can consume the returned checkpoint dictionaries because it reads checkpoint fields dynamically. However, the custom DataOps route returns a different shape (`snapshots`, `factor_names`, `total_decisions`) and cannot satisfy the shared `checkpoints` contract (`apps/dataops/backend/app/context_router.py:1037-1068`). The model also does not statically define the checkpoint fields the panel consumes.

### V7 — DI-TIMELINE field contract

`CentroidTimelinePanel` is wired to `fetchCentroidHistory(50)` and reads `data.checkpoints` (`copilot-sdk/apps/dataops/frontend/src/components/CentroidTimelinePanel.tsx:13-14,26-49`; API call `apps/dataops/frontend/src/api.ts:410-414`). The exact field comparison is:

| Field | TimelinePanel consumes | Shared `/api/self/centroid-history` | Custom `/api/context/centroid-history` | Gap? |
|---|---|---|---|---|
| Envelope `checkpoints` | Yes, required by `buildTimeline()` (`CentroidTimelinePanel.tsx:48,126`) | Yes, required model field (`copilot_sdk/backend/models.py:177-179`) | No; custom has `snapshots` (`context_router.py:1064-1068`) | **YES** for custom route |
| Envelope `total` | Yes, display fallback (`CentroidTimelinePanel.tsx:87`) | Yes (`models.py:177-179`) | No; custom uses `total_decisions` | **YES** for custom route |
| `checkpointTime` / `checkpoint_time` | Yes, preferred X-axis label (`CentroidTimelinePanel.tsx:130-135`) | Present only as an untyped dictionary field from GraphStore; TS aliases are declared at `apps/dataops/frontend/src/types.ts:663-667` | No | **YES** for custom route |
| `createdAt` / `created_at` | Yes, fallback X-axis label (`CentroidTimelinePanel.tsx:131-135`) | Present only as an untyped dictionary field; aliases at `types.ts:663-667` | No | **YES** for custom route |
| `centroids` | Yes; iterates values and computes keys/drift (`CentroidTimelinePanel.tsx:140-150`) | Available inside checkpoint dictionaries from GraphStore; not declared by `CentroidHistoryResponse` itself | Custom has `centroids_sample`, nested under snapshots, not `centroids` | **YES** for custom route |
| `iks` / `metadata.iks` / `metadata.IKS` | Yes (`CentroidTimelinePanel.tsx:137`) | Available in checkpoint dictionaries; not typed in the shared response envelope | No direct IKS field; custom has no `iks` | **YES** for custom route |
| `metadata.phase` | Yes, phase labels/markers (`CentroidTimelinePanel.tsx:138,153-155`) | Available only if present in checkpoint metadata | No direct metadata object; custom has `note` | **YES** for custom route |
| `decisionId`, `category`, `action` | Not used by this panel; declared as optional TS fields (`types.ts:657-662`) | May be present in checkpoint dictionaries | Not present as checkpoint fields | No for this panel; yes for consumers requiring identity |
| `snapshots`, `factor_names`, `total_decisions` | No | No | Yes (`context_router.py:1048-1067`) | **YES** if the panel is pointed at custom route |

The DataOps frontend has two distinct API functions: `getCentroidHistory()` targets the custom route and types `CentroidHistoryResponse`, while `fetchCentroidHistory()` targets the shared route and types `SelfCentroidHistoryResponse` (`apps/dataops/frontend/src/api.ts:401-414`; `apps/dataops/frontend/src/types.ts:650-672`). The timeline panel uses the latter.

### V8 — DataOps timeout root cause

**GAP — root cause not proven.** The observed DataOps `/api/self/centroid-history` timeout cannot be attributed to the 219 checkpoint rows from source or the current database snapshot.

Evidence:

1. The shared route has a bounded `limit` parameter, default 50 and maximum 500 (`copilot-sdk/copilot_sdk/backend/self_computation_router.py:29-38`), and passes that limit to `get_centroid_checkpoints()` (`:49`).
2. SQLite checkpoint enumeration also applies `LIMIT ?` for bounded requests (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:2671-2701`).
3. The DataOps snapshot contains 219 rows, but a request with the panel’s `limit=50` does not load all 219 rows through the shared route. Therefore, **219 rows as a volume-only explanation is CONTRADICTED** by the bounded query path.
4. At this scan time, all five local OpenAPI probes refused connections, including DataOps :8030. This establishes no live service state, not an internal timeout cause.
5. DataOps selects its GraphStore during application construction (`copilot-sdk/apps/dataops/backend/app/main.py:579-589`) and mounts the shared router on that selected store (`:749`). The source does not expose a timeout-specific exception, timing log, or route-level fallback around this call.

The remaining possible classes—service startup/readiness, selected backend connectivity, database lock, or an external AGE/SQLite issue—were not distinguishable from the available read-only evidence.

### S2P read/write mismatch

**CONFIRMED — two different S2P surfaces use different state.**

- Normal S2P learning persists L5 state with `store.update_centroid()` (`s2p-copilot/backend/app/routers/s2p.py:656-709`; learn route invocation `:2187-2203` and outcome route `:2311-2319`).
- `S2PCentroidExplorerService.get_centroid_drift()` reads `graph_store.get_centroid_checkpoints()` (`s2p-copilot/backend/app/services/centroid_explorer.py:145-189`). It does not read L5 rows.
- S2P’s explorer import endpoint is a separate legacy checkpoint writer: `_checkpoint_imported_centroids()` calls `graph_store.save_centroids(..., "import", ...)` (`s2p-copilot/backend/app/routers/s2p_explorer.py:200-228`).
- S2P current-centroid/cell surfaces read the scorer’s in-memory centroids (`s2p-copilot/backend/app/routers/s2p_explorer.py:52-75`), so those can reflect learning while the drift endpoint remains empty/stale unless checkpoint rows were also written.

Therefore, the CentroidExplorer drift history shows checkpoint/import history, not the ordinary L5 `update_centroid()` history. The mismatch is not absolute because the import route can create legacy checkpoint rows.

### `SNAPSHOT_AFTER` traversal

**CONTRADICTED if the claim is that a production/history reader traverses the edge.** The AGE writer creates and deduplicates the edge:

| Classification | File:line | Evidence |
|---|---|---|
| WRITE / dedup check | `ci-platform/ci_platform/graph/age_graph_store.py:1103-1120` | `OPTIONAL MATCH (d)-[snapshot:SNAPSHOT_AFTER]->(c)` followed by `CREATE (d)-[:SNAPSHOT_AFTER]->(c)` when absent |
| WRITE caller | `ci-platform/ci_platform/graph/age_graph_store.py:1421-1426` | V2 checkpoint write calls `_link_checkpoint_edges()` |
| Cleanup match/delete | `ci-platform/ci_platform/graph/age_graph_store.py:3095-3101` | Domain reset matches and deletes the edge |

No other `SNAPSHOT_AFTER` reference was found in `ci-platform/ci_platform`, `copilot-sdk/copilot_sdk`, `gen-ai-roi-demo-v4-v50/backend/app`, or `s2p-copilot/backend/app`. The `3097` match is reset cleanup, not a history/consumer traversal. Thus an AGE write exists, but no reader that returns a traversed Decision→Checkpoint lineage was confirmed.

### SOC L5 writer

**CONFIRMED — it writes L5 state, not a shared centroid checkpoint.** `persist_soc_centroid()` obtains a learning store and calls `store.update_centroid()` with domain, category, action, vector, delta, and causing decision (`gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:396-437`). It does not call `save_centroids()` or `write_centroid_checkpoint()`, and it does not create `SNAPSHOT_AFTER`. The SOC route invokes it after guarded scorer update (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2088-2095,2188-2241`).

## SCAN E — OPERATIONS AND CONSUMERS

### V10 — Consumer inventory

The updated keyword scan found **41 Python files with any centroid/judgment keyword** across the requested roots. A narrower persistence/state scan found **30 Python files**, of which **24 are non-test implementation files and 6 are tests**. The principal implementation consumers are categorized below; the GraphStore adapter is included separately because the supplied E1 roots omit `ci-platform`.

#### Checkpoint readers

- Shared SDK: `copilot-sdk/copilot_sdk/scoring/scorer.py:266-268,1359`; `backend/self_computation_router.py:29-51`; `backend/transfer_router.py:181-203`; `backend/diagnostics_models.py:225,422-423`.
- Store implementations: `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2626-2701`; `memory_store.py:1370-1419`; `dual_write_store.py:376-410`; AGE adapter `ci-platform/ci_platform/graph/age_graph_store.py:2661-2678,2834-2853`.
- Copilot consumers: Trading `apps/trading/backend/app/routers/analytics.py:257` and `state/trading_registry.py:64-67`; Purchasing `apps/purchasing/backend/app/routers/evidence.py:186-194` and `backend/cli.py:418-431`; S2P `s2p-copilot/backend/app/services/centroid_explorer.py:145-189` and `routers/s2p_performance.py:171-176`.

#### Checkpoint writers

- Shared scorer legacy warm-start writer: `copilot-sdk/copilot_sdk/scoring/scorer.py:1514-1527`.
- Shared scorer V2 writer: `scorer.py:1767-1840`.
- SQLite/AGE/InMemory implementations: `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1556-1634,2591-2624`; `ci-platform/ci_platform/graph/age_graph_store.py:1356-1426,2620-2659`; `copilot-sdk/copilot_sdk/graph/memory_store.py:777-815,1346-1368`.
- Outbox replay: `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:299-324`.
- S2P import checkpoint: `s2p-copilot/backend/app/routers/s2p_explorer.py:200-228`.
- Transfer warm-start metadata reader: `copilot-sdk/copilot_sdk/backend/transfer_router.py:181-203`; the corresponding writer is the scorer path at `scorer.py:1514-1527`.

#### L5 readers and state stores

- SQLite L5 state is stored in `l5_centroids` by `update_centroid()` (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:2279-2315`); InMemory keeps `_l5_centroids` (`memory_store.py:1182-1205`); AGE uses `L5Centroid` and `SHAPED_BY` in `age_graph_store.py:2217-2255` and reads it at `:2256-2313`.
- Startup `load_latest_centroids()` is a separate checkpoint path, not an L5 read (`copilot-sdk/copilot_sdk/scoring/scorer.py:266-268`).

#### L5 writers

- SDK scoring route: `copilot-sdk/copilot_sdk/backend/scoring_router.py:479-557`.
- SOC: `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:396-437`; route use in `backend/app/routers/triage.py:2241-2269`.
- S2P: `s2p-copilot/backend/app/routers/s2p.py:656-709,2187-2203,2311-2319`.
- Shared adapters and outbox replay: `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2279-2315`; `memory_store.py:1182-1205`; `age_graph_store.py:2217-2255`; `persistence_outbox.py:299-324`.

#### Delta readers

- SOC framework evolution route reads `Decision.centroid_delta_norm` (`gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:107-153`); the field is part of the graph schema at `backend/app/graph_schema.py:98`.
- S2P framework route has the analogous centroid-delta surface (`s2p-copilot/backend/app/routers/framework_router.py:98-142`), while S2P L5 update stores `delta_norm` through `routers/s2p.py:695-705`.
- Shared scoring route exposes `centroid_delta`/`centroid_updated` fields (`copilot-sdk/copilot_sdk/backend/scoring_router.py:697-705`).

#### Frontend consumers

The scan found **32 frontend TypeScript/TSX files** with centroid keywords. Main rendering/API consumers are:

- DataOps: `apps/dataops/frontend/src/api.ts:401-414`; `components/CentroidTimelinePanel.tsx:26-155`; `components/CentroidTimeline.tsx`; `components/CentroidTimelineChart.tsx`; `screens/CurveScreen.tsx`; `screens/InsightScreen.tsx`; types `types.ts:650-672`.
- Trading: `apps/trading/frontend/src/api.ts:864`; `components/CentroidTimeline.tsx`; `components/CentroidTimelineChart.tsx`; `screens/PerformanceScreen.tsx`; `state/tradingKeys.ts:26`; types `types.ts:700-710`.
- Purchasing: `apps/purchasing/frontend/src/components/CentroidTimelineChart.tsx`; `screens/PerformanceScreen.tsx`; types `types.ts:338-348`.
- S2P: `apps/s2p/frontend/src/components/CentroidExplorer.tsx`; `CentroidExplorerPanel.tsx`; `FactorRadar.tsx`; `TrajectoryChart.tsx`; `screens/InsightScreen.tsx`; `screens/TriageScreen.tsx`.
- SOC: `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/CompoundingTab.tsx` and `RuntimeEvolutionTab.tsx` read centroid-evolution/drift API data; `frontend/src/lib/api.ts` contains the route calls.

### V10b — Store-selection and feature-flag insertion points

**CONFIRMED — per-copilot store selection seams exist; GAP for a pre-existing JM read/write flag.**

| Copilot | Store-selection evidence | Current selection |
|---|---|---|
| SOC | `gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:30-63` resolves `GraphConfig`, requires `GRAPH_BACKEND=age`, and creates the AGE client | Direct AGE client; no shared SDK `GraphStore` injection seam in SOC route |
| S2P | `s2p-copilot/backend/app/main.py:101-143` calls `create_graph_store()` with `graph_config.backend`, DSN, graph, and profile | Selected GraphStore passed into `CompoundingScorer.from_preset()` |
| Trading | `copilot-sdk/apps/trading/backend/app/main.py:323-356,439` defines `selected_graph_store_factory`, injects scorer/store, mounts self router | Factory-selected backend; shared scorer receives selected store |
| Purchasing | `copilot-sdk/apps/purchasing/backend/app/main.py:449-505,707` defines and propagates selected factory/store | Factory-selected backend; shared scorer and self router receive selected store |
| DataOps | `copilot-sdk/apps/dataops/backend/app/main.py:313-325,579-652,749` selects and injects one store | Factory-selected backend; shared scorer and self router receive selected store |
| Shared factory | `copilot-sdk/copilot_sdk/graph/factory.py:123-205` selects `sqlite`, `dual_write`, or AGE based on explicit/config/env backend | Common backend-construction seam |

`CompoundingScorer` accepts an injected `graph_store` and uses that store for startup/load and persistence (`copilot-sdk/copilot_sdk/scoring/scorer.py:130-141,214-268`). Therefore per-copilot store selection can be applied at app construction without changing the scorer’s method signatures. A `JM_READ_STORE`/`JM_WRITE_STORE` flag is not present in the scanned code; adding such a flag would require wiring at these app/factory seams and deciding how the scorer’s single `_graph_store` is split.

### V11 — Pool configuration

**CONFIRMED — configurable AGE pool exists; default pool activation is off unless enabled.**

- `AGEClient` reads `AGE_USE_POOL`; default is false. It reads `AGE_POOL_MIN_SIZE` default 1 and `AGE_POOL_MAX_SIZE` default 5 (`ci-platform/ci_platform/graph/age_client.py:113-140`).
- When pooled, it constructs `psycopg_pool.ConnectionPool` with min 1/max 5 defaults, `autocommit=True`, and `connect_timeout=10` (`age_client.py:179-200`).
- Session configuration loads AGE and sets `statement_timeout='120s'` (`age_client.py:170-176`).
- When pooling is disabled, the client uses fresh connections; if pool initialization fails, it falls back to a warm connection (`age_client.py:219-227,420-464`).
- `AGEGraphStore` constructs an AGEClient (`ci-platform/ci_platform/graph/age_graph_store.py:38-42`). SOC’s direct client is created through the shared factory (`gen-ai-roi-demo-v4-v50/backend/app/db/graph_client.py:53-63`).

**PgBouncer: GAP / not found.** No PgBouncer configuration file or source reference was found in the scanned repository. The AGE client connects directly through psycopg/psycopg_pool; no PgBouncer DSN or service configuration is present in the scanned paths.

**PostgreSQL `max_connections`: GAP in repository evidence.** No repository setting establishes the live PostgreSQL value. The commonly used default of 100 is an external deployment assumption, not confirmed by this scan.

### V11b — Connection math

**GAP — scenario calculation only, not observed load.** Under the supplied worst-case assumption:

```text
4 Playwright workers × 5 copilots × approximately 4 concurrent AGE connections/copilot
= approximately 80 AGE connections
```

The arithmetic is 80. It cannot be compared definitively with the live PostgreSQL ceiling because `max_connections` was not found in repository configuration, and current code defaults to a per-client pool maximum of 5 only when `AGE_USE_POOL` is enabled (`age_client.py:127-140,184-188`). In the current scanned architecture, SOC is AGE-backed while S2P/Trading/Purchasing/DataOps normally select SQLite; the all-AGE value is therefore a future topology scenario, not current observed load.

### V13 — InMemory conformance

**CONTRADICTED for full adapter parity.** Specific differences:

| Method | InMemory | AGE/SQLite comparison |
|---|---|---|
| `load_latest_centroids` | Returns the last legacy list row by domain; no `checkpoint_id IS NULL` predicate (`copilot-sdk/copilot_sdk/graph/memory_store.py:1370-1378`) | AGE/SQLite explicitly filter null IDs (`ci-platform/ci_platform/graph/age_graph_store.py:2661-2678`; `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2626-2638`) |
| `save_centroids` | Stores a Python legacy row without checkpoint ID, shape, or factor-name hash (`memory_store.py:1346-1368`) | SQLite has durable schema columns (`sqlite_store.py:441-458`); AGE creates a durable checkpoint node (`age_graph_store.py:2620-2659`) |
| `write_centroid_checkpoint` | Stores V2 payload in an in-memory dictionary with ID, shape, factor hash, and timestamp (`memory_store.py:777-815`) | SQLite inserts a durable V2 row (`sqlite_store.py:1556-1634`); AGE creates V2 node and can link `SNAPSHOT_AFTER` (`age_graph_store.py:1356-1426`) |
| `update_centroid` | Updates `_l5_centroids` dictionary only (`memory_store.py:1182-1205`) | SQLite upserts durable `l5_centroids` (`sqlite_store.py:2279-2315`); AGE upserts `L5Centroid` with `SHAPED_BY` (`age_graph_store.py:2217-2255`) |
| `get_centroid_checkpoints` | Includes V2 only when `include_v2=True` (`memory_store.py:1387-1419`) | AGE/SQLite also default to legacy-only, but AGE has graph lineage edge creation; neither adapter returns traversal lineage from this method |
| `SNAPSHOT_AFTER` | No graph edge or traversal exists | AGE writer creates it; SQLite has no edge equivalent in its checkpoint table |

## COUPLING ANALYSIS

### Where `load_latest_centroids` runs

The principal startup call is `CompoundingScorer.from_preset()` (`copilot-sdk/copilot_sdk/scoring/scorer.py:214-268`). It calls the injected store’s `load_latest_centroids(preset.name)` and falls back to the preset bootstrap tensor when no row is returned (`:266-268`). Store implementations also expose the method directly (`sqlite_store.py:2626-2638`; AGE `:2661-2678`; InMemory `:1370-1378`).

### Effect of changing one copilot’s store

The scorer is a shared class but its state is instance/domain scoped: the constructor records the injected `_graph_store` and domain (`scorer.py:130-141`), while each app constructs and injects its selected store (`S2P main.py:123-143`; Trading main.py:323-356; Purchasing main.py:449-505; DataOps main.py:579-652). A store change for one app therefore affects that app’s load, checkpoint history, L5 state, and persistence, but does not automatically alter another app’s scorer instance. Shared adapter/protocol behavior remains a coupling point.

### Can per-copilot flags isolate read/write?

**GAP for existing flags; source seam CONFIRMED.** Backend selection can be isolated at each app’s factory seam, but the scorer currently has one `_graph_store` used for both read and write (`scorer.py:138-141,266-268`; write path `:1802-1839`). A separate read/write store requires an explicit wrapper or scorer-level routing decision; no existing `JM_READ_STORE`/`JM_WRITE_STORE` implementation was found.

### Warm-start safety

**CONTRADICTED if treated as unused/vestigial.** The scorer actively writes a null-ID legacy row with category `"warm_start"` (`copilot-sdk/copilot_sdk/scoring/scorer.py:1514-1527`). The transfer router reads recent checkpoint metadata and selects rows whose metadata source is `warm_start` (`copilot-sdk/copilot_sdk/backend/transfer_router.py:181-203`). Removing that writer would change transfer/warm-start behavior, not only startup checkpoint behavior.

## Runtime surface probe

All five requested `/openapi.json` probes were unavailable at scan time: ports 8001, 8002, 8010, 8020, and 8030 refused connections. Consequently, source route registration—not live OpenAPI output—is the evidence for route inventory in this report.

## Cleanup

No scratch scripts were created. No source, test, graph, or database was modified. The only artifact written is this requested report.
