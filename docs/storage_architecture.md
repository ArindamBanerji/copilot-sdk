# Storage Architecture: Unified Judgment Memory
**Canonical location:** `copilot-sdk/docs/storage_architecture.md`
**Date:** May 22, 2026 · **Authority:** MAP v5.114
**Updated by:** Codex design prompt (sections 7-12 added by analysis)

---

## §1 Principle

The platform has ONE storage concept per copilot: a **data directory**.
GraphStore and DecisionStore share the same SQLite file within that
directory. WAL mode for concurrent access. demo.py owns the
directory lifecycle.

```
~/.ci-platform/{copilot}/store.db
  ├── GraphStore tables (nodes, edges)            ← graph data
  ├── DecisionStore tables (decisions, centroids)  ← judgment data
  └── decisions_archive                            ← bounded retention
```

---

## §2 Current State (Debt)

```
GraphStore ──── InMemory/SQLite/AGE ──── graph data (nodes, edges)
DecisionStore ── own SQLite :memory: ── decisions, centroids
ReceiptStore ─── Python list ────────── receipts (S2P only)
TradeStore ───── Python list ────────── trades (Trading only)
Evolution ────── fixture JSON ───────── rules
```

Five storage mechanisms. Only AGE persists. The rest are ephemeral.

---

## §3 Target State

```
GraphStore ──── SQLite file (dev) / AGE (prod)
   └─── graph tables (nodes, edges)
   └─── judgment tables (decisions, centroids)
   └─── evidence tables (receipts, chain)         ← Phase 3
   └─── domain tables (trades, orders, alerts)    ← Phase 3
```

---

## §4 Migration Path

| Phase | What | Scope | Status |
|---|---|---|---|
| **Phase 1** | File-backed SQLite. Auto-seed. Bounded retention. demo.py control. | SDK copilots | **ACTIVE** |
| **Phase 2** | DecisionStore writes through GraphStore (decisions as nodes). | SDK + scoring | Planned |
| **Phase 3** | ReceiptStore, TradeStore, Evolution persist through GraphStore. | All copilots | Planned |
| **Phase 4** | AGE backend for any copilot needing graph traversal. | Per-copilot | Planned |

---

## §5 Phase 1 Design

### Data Directory Per Copilot

```
~/.ci-platform/
├── trading/
│   └── store.db        ← shared: GraphStore + DecisionStore tables
├── purchasing/
│   └── store.db
├── dataops/
│   └── store.db
└── s2p/
    └── store.db
```

### Configuration Flow

```
demo.py
  └── sets CI_DATA_DIR = ~/.ci-platform/trading/
  └── sets CI_STORE_PATH = ~/.ci-platform/trading/store.db
        └── backend reads CI_STORE_PATH
              ├── DecisionStore(db_path=CI_STORE_PATH)
              └── GraphStore(db_path=CI_STORE_PATH)  ← same file
```

### Lifecycle

| Event | Behavior |
|---|---|
| First start | Directory created. DB created. WAL enabled. Auto-seed from fixtures. |
| Restart | DB has data. Resume. Skip seed. |
| Every 100 decisions | Archive beyond 2×q_window (800). |
| `demo.py --reset` | Stop copilot. Delete directory. Next start re-seeds. |
| `demo.py --status` | Read decision counts from DB without starting. |

### SOC Exception

SOC uses AGE (PostgreSQL in WSL2). Not file-backed. Persistence
managed by AGE. Correct for SOC's graph traversal needs.

### S2P

Separate repo. Same pattern. `CI_STORE_PATH` → `~/.ci-platform/s2p/store.db`.
Implemented in a follow-on prompt for s2p-copilot.

---

## §6 Rules

1. One `store.db` file per copilot. No shared cross-copilot DB.
2. WAL mode for file-backed DBs. `:memory:` for tests.
3. Auto-seed on empty (0 decisions → load fixtures).
4. Bounded retention: archive beyond 800 active decisions.
5. demo.py is the control plane for data lifecycle.
6. Tests always use `:memory:`. Persistence tests use `tmp_path`.
7. `CI_STORE_PATH` not set → default `:memory:` (backward compat).

---

## 7. Current DecisionStore Schema

Source read: `copilot_sdk/scoring/storage.py`, including `DecisionStore.__init__`, `DecisionStore._create_tables`, `DecisionStore.save_decision`, `DecisionStore.save_outcome`, `DecisionStore.save_centroids`, `DecisionStore.load_latest_centroids`, `DecisionStore.get_decision`, `DecisionStore.get_verified_decisions`, `DecisionStore.get_centroid_checkpoints`, `DecisionStore.get_all_decisions`, `DecisionStore.count_verified`, `DecisionStore.count_correct`, `DecisionStore.count_categories_with_n`, and `DecisionStore._count_decisions`.

`DecisionStore.__init__(self, db_path: str | Path)` requires a `db_path` argument. The class has no default database path; app defaults are supplied by caller code such as `apps/trading/backend/app/main.py::create_app`, `apps/purchasing/backend/app/main.py::create_app`, `apps/dataops/backend/app/main.py::create_app`, and `copilot_sdk/scoring/scorer.py::CompoundingScorer.from_preset`. The constructor stores `self.db_path = str(db_path)`, opens `sqlite3.connect(self.db_path)`, sets `row_factory = sqlite3.Row`, and calls `_create_tables()`. No explicit in-memory/file branch is present inside `DecisionStore`.

`DecisionStore._create_tables()` creates the current live tables with this SQL:

```sql
CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    category TEXT NOT NULL,
    category_index INTEGER NOT NULL,
    factors_json TEXT NOT NULL,
    factor_vector_json TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    recommended_index INTEGER NOT NULL,
    confidence REAL NOT NULL,
    probabilities_json TEXT NOT NULL,
    created_at REAL NOT NULL
);
```

```sql
CREATE TABLE IF NOT EXISTS outcomes (
    decision_id TEXT PRIMARY KEY REFERENCES decisions(decision_id),
    actual_action TEXT NOT NULL,
    actual_index INTEGER NOT NULL,
    is_correct INTEGER NOT NULL,
    verified_at REAL NOT NULL,
    context_json TEXT
);
```

```sql
CREATE TABLE IF NOT EXISTS centroid_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT,
    category TEXT,
    centroids_json TEXT NOT NULL,
    decisions_count INTEGER NOT NULL,
    iks REAL NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at REAL NOT NULL
);
```

Migration helpers in the same file add backward-compatible columns: `DecisionStore._ensure_outcome_columns()` adds `outcomes.context_json`; `DecisionStore._ensure_centroid_columns()` adds `centroid_checkpoints.decision_id`, `category`, `metadata_json`, `decision_time_start`, `decision_time_end`, and `checkpoint_time`. `_ensure_centroid_columns()` also creates `idx_cc_checkpoint_time`, `idx_cc_decision_time`, and `idx_cc_category`.

| Method | Table | SQL Operation | Notes |
|---|---|---|---|
| `DecisionStore._create_tables` | `decisions` | `CREATE TABLE IF NOT EXISTS` | Core decision records. |
| `DecisionStore._create_tables` | `outcomes` | `CREATE TABLE IF NOT EXISTS` | One verified outcome per decision. |
| `DecisionStore._create_tables` | `centroid_checkpoints` | `CREATE TABLE IF NOT EXISTS` | Centroid snapshots. |
| `DecisionStore._ensure_outcome_columns` | `outcomes` | `PRAGMA table_info`, `ALTER TABLE ADD COLUMN` | Adds `context_json` if absent. |
| `DecisionStore._ensure_centroid_columns` | `centroid_checkpoints` | `PRAGMA table_info`, `ALTER TABLE ADD COLUMN`, `CREATE INDEX IF NOT EXISTS` | Adds newer centroid metadata/time fields and indexes. |
| `DecisionStore.save_decision` | `decisions` | `INSERT OR REPLACE` | Writes serialized factors, factor vector, probabilities, and scalar recommendation fields. |
| `DecisionStore.save_outcome` | `outcomes` | `INSERT OR REPLACE` | Writes actual action, correctness, verification time, and optional context. |
| `DecisionStore.save_centroids` | `centroid_checkpoints` | `INSERT` | Writes centroid JSON, count, IKS, metadata, and optional checkpoint window fields. |
| `DecisionStore.load_latest_centroids` | `centroid_checkpoints` | `SELECT centroids_json ... ORDER BY id DESC LIMIT 1` | Returns the latest checkpoint only; there is no domain filter. |
| `DecisionStore.get_decision` | `decisions` | `SELECT * WHERE decision_id = ?` | Returns `_decision_from_row(row)` or `None`. |
| `DecisionStore.get_verified_decisions` | `decisions`, `outcomes` | `INNER JOIN` | Returns joined decision/outcome dictionaries ordered by decision creation time. |
| `DecisionStore.get_centroid_checkpoints` | `centroid_checkpoints` | `SELECT *` with dynamic `WHERE` | Filters by category, checkpoint time, and decision time. |
| `DecisionStore.get_all_decisions` | `decisions` | `SELECT * ORDER BY created_at ASC, decision_id ASC` | Returns `_decision_from_row(row)` for every row. |
| `DecisionStore.count_verified` | `outcomes` | `SELECT COUNT(*) AS n FROM outcomes` | Counts all verified rows. |
| `DecisionStore.count_correct` | `outcomes` | `SELECT COUNT(*) AS n FROM outcomes WHERE is_correct = 1` | Counts correct rows. |
| `DecisionStore.count_categories_with_n` | `decisions`, `outcomes` | `INNER JOIN`, `GROUP BY`, `HAVING count >= ?` | Counts verified rows by category. |
| `DecisionStore._count_decisions` | `decisions` | `SELECT COUNT(*) AS n FROM decisions` | Private total decision count helper. |

`DecisionStore.save_decision()` consumes `decision_id`, `domain`, `category`, `category_index`, `factors`, `factor_vector`, `recommended_action`, `recommended_index`, `confidence`, `probabilities`, and optional `created_at`. It writes exactly `decision_id`, `domain`, `category`, `category_index`, `factors_json`, `factor_vector_json`, `recommended_action`, `recommended_index`, `confidence`, `probabilities_json`, and `created_at`.

`DecisionStore.count_verified()` executes `SELECT COUNT(*) AS n FROM outcomes`. `DecisionStore.count_correct()` executes `SELECT COUNT(*) AS n FROM outcomes WHERE is_correct = 1`. `DecisionStore._count_decisions()` executes `SELECT COUNT(*) AS n FROM decisions`.

`DecisionStore.get_recent_decisions()` was not found after reading `copilot_sdk/scoring/storage.py` fully. The closest current APIs are `DecisionStore.get_all_decisions()`, returning `decision_id`, `domain`, `category`, `category_index`, `factors`, `factor_vector`, `recommended_action`, `recommended_index`, `confidence`, `probabilities`, and `created_at`, and `copilot_sdk/graph/sqlite_store.py::SQLiteGraphStore.get_decisions(limit)`, which slices `DecisionStore.get_all_decisions()`.

WAL support is absent: no `PRAGMA journal_mode=WAL` exists in `copilot_sdk/scoring/storage.py`. Archive and retention logic is absent: no archive table, retention threshold, or archive/delete hook exists in `DecisionStore`. Table names are inline SQL string literals, not constants.

---

## 8. Current GraphStore Usage in SDK Copilots

Sources read: `apps/trading/backend/app/main.py`, `apps/purchasing/backend/app/main.py`, `apps/dataops/backend/app/main.py`, `copilot_sdk/scoring/scorer.py`, `copilot_sdk/backend/scoring_router.py`, `copilot_sdk/backend/scorer_proxy.py`, and `copilot_sdk/graph/sqlite_store.py`.

`SQLiteGraphStore` is used by all three SDK copilot backends. It delegates decision, outcome, verified-decision, count, and centroid operations to `DecisionStore` in `copilot_sdk/graph/sqlite_store.py`, and it adds graph-adjacent persistence for `evolution_events` and `decision_entity_edges`. `InMemoryGraphStore` was not found in the Trading, Purchasing, or DataOps `create_app()` paths.

| Copilot | DecisionStore db_path | GraphStore type | Startup hook? | app.state fields |
|---|---|---|---|---|
| Trading | `apps/trading/backend/app/main.py::create_app(db_path: str \| Path \| None = None)` sets `scoring_db = str(db_path or DEFAULT_DB_PATH)`, where `DEFAULT_DB_PATH` is `apps/trading/backend/data/trading.db`. | `SQLiteGraphStore(str(db_path), domain="trading")` from `_graph_store(db_path)`. | Not found. | None populated by `create_app()`. |
| Purchasing | `apps/purchasing/backend/app/main.py::create_app(db_path: str \| Path \| None = None)` sets `scoring_db = str(db_path or DEFAULT_DB_PATH)`, where `DEFAULT_DB_PATH` is `apps/purchasing/backend/data/purchasing.db`. | `SQLiteGraphStore(str(db_path), domain="purchasing")` from `_graph_store(db_path)`. | Not found. | None populated by `create_app()`. |
| DataOps | `apps/dataops/backend/app/main.py::create_app(db_path: str \| Path \| None = None)` sets `scoring_db = str(db_path or DEFAULT_DB_PATH)`, where `DEFAULT_DB_PATH` is `apps/dataops/backend/data/dataops.db`. | `SQLiteGraphStore(str(db_path), domain="dataops")` from `_graph_store(db_path)`. | Not found. | None populated by `create_app()`. |

`copilot_sdk/backend/scorer_proxy.py::FreshScorerProxy` stores the configured database path as `_db_path`, exposes `store = graph_store_factory(db_path)`, and opens `CompoundingScorer.from_preset(self._preset_name, db_path=self._db_path)` on each scoring call. `copilot_sdk/scoring/scorer.py::CompoundingScorer.from_preset(domain, db_path=None, graph_store=None, ...)` creates `DecisionStore(db_path)` and, when no graph store is passed, creates `SQLiteGraphStore(db_path, domain=preset.name)`. If `db_path` is `None`, it falls back to `copilot_sdk/scoring/data/{domain}.db`; the three app backends pass their own `scoring_db`, so they do not use that SDK default path.

Auto-seed logic would be added inside each app `create_app()` after `scoring_db` is resolved and before returning the `FastAPI` app. There is no existing startup hook to extend, so a new startup event would be the current insertion point.

---

## 9. Seed Data Inventory

Source read: `scripts/preseed_all_copilots.py`.

`scripts/preseed_all_copilots.py` seeds by calling running backend APIs with `urllib`, not by writing directly to `DecisionStore` or `SQLiteGraphStore`. It defines `PRESEED_DECISIONS_PER_COPILOT = 200`, `PRESEED_OVERRIDE_COUNT = 50`, expands fixture entries to the target count, posts `/api/score`, posts `/api/learn`, and posts a metadata endpoint when configured.

| Copilot | Source fixture used by preseed | Source entries | Target decisions | Key fields used |
|---|---|---:|---:|---|
| Trading | `apps/trading/backend/data/trading_seed_v2.json` | 40 | 200 | `trade_id`, `ticker`, `direction`, `category`, `thesis_type`, `timeframe`, `research_checklist`, `research_depth`, `conviction`, `technical_signal`, `position_size`, `time_horizon`, `market_regime`, `shares`, `entry_price`, `portfolio_value`, `stop_loss`, `target`, `rr_ratio`, `exit_price`, `pnl_pct`, `pnl_dollars`, `hold_days`, `outcome`, `is_correct`, `day_of_week`, `date`, `action_taken`, `vix_at_entry` |
| Purchasing | `apps/purchasing/backend/data/purchasing_seed_v2.json` | 20 | 200 | `order_id`, `item`, `display_name`, `category`, `quantity_lbs`, `day_of_week`, `date`, `is_event_day`, `event_type`, factor source fields, `action_taken`, `is_correct`, waste/stockout/cost fields |
| DataOps | `copilot_sdk/scoring/presets/dataops_seed.json` | 20 | 200 | `event_id`, `dataset`, `category`, `action_taken`, `is_correct`, `factors` |

Files found under `apps/trading/backend/data/`: `analytics_cache.json`, `market_snapshot.json`, `portfolio_summary.json`, `ticker_cache.json`, `trade_metadata.json`, `trading_seed_v2.json`.

Files found under `apps/purchasing/backend/data/`: `analytics_cache.json`, `evolution_fixtures.json`, `order_metadata.json`, `purchasing_orders.json`, `purchasing_seed_v2.json`, `purchasing_suppliers.json`, `waste_history.json`, `weather_cache.json`.

Files found under `apps/dataops/backend/data/`: `ae_impact.json`, `alert_metadata.json`, `celonis_knowledge_models.json`, `celonis_kpis.json`, `celonis_process_data.json`, `conservation_history.json`, `evolution_fixtures.json`, `incident.json`, `process_signals.json`, `process_timeline.json`, `sap_purchase_orders.json`, `sap_supplier_invoices.json`, `sap_suppliers.json`, `schema_changes.json`, `transfer_status.json`, `transformations.json`.

| Copilot | Fixture File | Entries | Key Fields | Used by preseed? |
|---|---|---:|---|---|
| Trading | `apps/trading/backend/data/trading_seed_v2.json` | 40 | `trade_id`, `ticker`, `direction`, `category`, factor fields, pricing fields, `outcome`, `is_correct`, `action_taken` | Yes |
| Trading | `apps/trading/backend/data/trade_metadata.json` | 113 keyed records | `decision_id`, `trade_id`, `category`, factor fields, `score_action`, `score_confidence`, `scored_factors`, outcome/pricing fields | No |
| Purchasing | `apps/purchasing/backend/data/purchasing_seed_v2.json` | 20 | `order_id`, `item`, `category`, factor source fields, `action_taken`, `is_correct`, cost/stockout fields | Yes |
| Purchasing | `apps/purchasing/backend/data/purchasing_orders.json` | 500 | `order_id`, `category`, `supplier_id`, `supplier_name`, `factors`, `outcome`, `status`, `verification_score`, `verified` | No |
| Purchasing | `apps/purchasing/backend/data/order_metadata.json` | 285 keyed records | `decision_id`, `category`, `action`, `confirmed_action`, factor/cost fields, `reward`, `created_at` | No |
| DataOps | `copilot_sdk/scoring/presets/dataops_seed.json` | 20 | `event_id`, `dataset`, `category`, `action_taken`, `is_correct`, `factors` | Yes |
| DataOps | `apps/dataops/backend/data/alert_metadata.json` | 315 keyed records | `decision_id`, `alert_id`, `category`, `action_taken`, `factors`, `ae_suggested`, `followed_ae`, `system_name` | No |

No app-local file under `apps/dataops/backend/data/` is used as the DataOps source fixture by `scripts/preseed_all_copilots.py`; the script points to `copilot_sdk/scoring/presets/dataops_seed.json`.

---

## 10. Table Collision Analysis

Sources read: `copilot_sdk/scoring/storage.py`, `copilot_sdk/graph/sqlite_store.py`, `apps/trading/backend/app/main.py`, `apps/purchasing/backend/app/main.py`, `apps/dataops/backend/app/main.py`, and `scripts/preseed_all_copilots.py`. A source search for `sqlite3`, `CREATE TABLE`, `DecisionStore(`, and `SQLiteGraphStore(` found production SQLite table creation in `DecisionStore` and `SQLiteGraphStore`; other direct table creation was in tests.

| Table Name | Used By | Risk if Shared File |
|---|---|---|
| `decisions` | `DecisionStore`; `SQLiteGraphStore.write_decision` delegates to `DecisionStore.save_decision` | Potential conflict. The table has `domain`, but `decision_id` is the primary key across the whole file. |
| `outcomes` | `DecisionStore`; `SQLiteGraphStore.write_outcome` delegates to `DecisionStore.save_outcome` | Potential conflict. The table is keyed only by `decision_id` and has no `domain`. |
| `centroid_checkpoints` | `DecisionStore`; `SQLiteGraphStore.save_centroids` delegates to `DecisionStore.save_centroids` | High conflict. The table has `category` but no `domain`, and `load_latest_centroids()` reads the latest checkpoint without domain filtering. |
| `evolution_events` | `SQLiteGraphStore.save_evolution_event` | High conflict. The table has event/rule/variant fields but no `domain`. |
| `decision_entity_edges` | `SQLiteGraphStore.link_decision_to_entity` and `SQLiteGraphStore.get_decision_links` | Potential conflict. The table has `decision_id`, `entity_id`, and `edge_type`, but no `domain`. |

The current defaults avoid collision by using separate files: `apps/trading/backend/data/trading.db`, `apps/purchasing/backend/data/purchasing.db`, and `apps/dataops/backend/data/dataops.db`. The persistence implementation should preserve one SQLite file per copilot unless centroid, evolution, and edge tables are made domain-scoped.

---

## 11. Implementation Plan

This is a design plan only. No implementation code is included here.

### 11a. DecisionStore changes

File: `copilot_sdk/scoring/storage.py`.

Modify or add:

- `DecisionStore.__init__`
- `DecisionStore._create_tables`
- `DecisionStore.save_decision`
- `DecisionStore._count_decisions`
- new helper `DecisionStore._enable_wal`
- new helper `DecisionStore._archive_old_decisions`

WAL plan:

- In `DecisionStore.__init__`, after `sqlite3.connect(self.db_path)` and before `_create_tables()`, run `PRAGMA journal_mode=WAL` for file-backed stores.
- Skip WAL for `":memory:"` or any future explicit in-memory path.
- Keep WAL connection-local initialization simple; SQLite persists the journal mode for the database file, but every new `DecisionStore` connection can safely assert it.

Archive table proposal:

```sql
CREATE TABLE IF NOT EXISTS decisions_archive (
    archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    category TEXT NOT NULL,
    category_index INTEGER NOT NULL,
    factors_json TEXT NOT NULL,
    factor_vector_json TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    recommended_index INTEGER NOT NULL,
    confidence REAL NOT NULL,
    probabilities_json TEXT NOT NULL,
    created_at REAL NOT NULL,
    actual_action TEXT,
    actual_index INTEGER,
    is_correct INTEGER,
    verified_at REAL,
    context_json TEXT,
    archived_at REAL NOT NULL,
    archive_reason TEXT NOT NULL
);
```

Archive hook:

- Add archive table creation inside `DecisionStore._create_tables()`.
- Initialize `self._decision_count = self._count_decisions()` after `_create_tables()` in `DecisionStore.__init__`.
- In `DecisionStore.save_decision()`, after the current insert succeeds, update `_decision_count` and call `_archive_old_decisions()` when the active-row threshold is exceeded.
- `_archive_old_decisions()` should copy oldest live decisions left-joined to outcomes into `decisions_archive`, then delete matching `outcomes` and `decisions` rows explicitly.
- Do not archive `centroid_checkpoints` in the first pass; their retention semantics differ from decision rows.

Backward compatibility:

- Existing database files open through current `CREATE TABLE IF NOT EXISTS` and `_ensure_*` migrations.
- Existing callers passing explicit `db_path` keep their behavior.
- Archive table creation is additive.
- Legacy migration tests that construct older `decisions`, `outcomes`, and `centroid_checkpoints` schemas should remain valid.

### 11b. Per-copilot `main.py` changes

Do not point all copilots at one SQLite file unless table schemas are made domain-scoped first. Prefer per-copilot files under a `CI_STORE_PATH` directory, or treat a file-valued `CI_STORE_PATH` as a single-app override.

| Copilot | Current `create_app` line | Proposed path behavior | Auto-seed source | Startup placement |
|---|---|---|---|---|
| Trading | `scoring_db = str(db_path or DEFAULT_DB_PATH)` in `apps/trading/backend/app/main.py::create_app` | explicit `db_path` wins; directory `CI_STORE_PATH` maps to `trading.db`; unset uses current default | `apps/trading/backend/data/trading_seed_v2.json` | New startup event inside `create_app()` after `scoring_db` is resolved |
| Purchasing | `scoring_db = str(db_path or DEFAULT_DB_PATH)` in `apps/purchasing/backend/app/main.py::create_app` | explicit `db_path` wins; directory `CI_STORE_PATH` maps to `purchasing.db`; unset uses current default | `apps/purchasing/backend/data/purchasing_seed_v2.json` | New startup event inside `create_app()` after `scoring_db` is resolved |
| DataOps | `scoring_db = str(db_path or DEFAULT_DB_PATH)` in `apps/dataops/backend/app/main.py::create_app` | explicit `db_path` wins; directory `CI_STORE_PATH` maps to `dataops.db`; unset uses current default | `copilot_sdk/scoring/presets/dataops_seed.json` | New startup event inside `create_app()` after `scoring_db` is resolved |

Auto-seed behavior:

- Check the target store before seeding; skip when decisions already exist.
- Seed by using the same scoring/learning semantics as the API through the configured scorer/proxy and `scoring_db`; do not import `scripts/preseed_all_copilots.py` because that script is HTTP-oriented.
- Load seed JSON inside the startup function to limit import-time file I/O.

### 11c. Test plan

| Test Name | File | Assertion |
|---|---|---|
| `test_decision_store_reopens_existing_count` | `tests/scoring/test_storage.py` | Reopened file-backed stores initialize count from existing `decisions`. |
| `test_decision_store_enables_wal_for_file_db` | `tests/scoring/test_storage.py` | File-backed store reports `wal` from `PRAGMA journal_mode`. |
| `test_decision_store_skips_wal_for_memory_db` | `tests/scoring/test_storage.py` | In-memory store still opens cleanly. |
| `test_decision_archive_table_created` | `tests/scoring/test_storage.py` | `decisions_archive` exists after initialization. |
| `test_decision_archive_copies_decision_and_outcome` | `tests/scoring/test_storage.py` | Archived row includes decision fields and joined outcome fields. |
| `test_decision_archive_removes_live_rows` | `tests/scoring/test_storage.py` | Archived decisions and outcomes are removed from active tables. |
| `test_archive_backward_compatible_with_legacy_schema` | `tests/scoring/test_storage.py` | Legacy schema migration still works with archive support. |
| `test_trading_uses_ci_store_path_directory` | `apps/trading/backend/tests/test_trading_backend.py` | Directory `CI_STORE_PATH` resolves to `trading.db`. |
| `test_purchasing_uses_ci_store_path_directory` | `apps/purchasing/backend/tests/test_purchasing_backend.py` | Directory `CI_STORE_PATH` resolves to `purchasing.db`. |
| `test_dataops_uses_ci_store_path_directory` | `apps/dataops/backend/tests/test_dataops_backend.py` | Directory `CI_STORE_PATH` resolves to `dataops.db`. |
| `test_trading_auto_seed_empty_store` | `apps/trading/backend/tests/test_trading_backend.py` | Empty Trading store seeds from `trading_seed_v2.json`. |
| `test_purchasing_auto_seed_empty_store` | `apps/purchasing/backend/tests/test_purchasing_backend.py` | Empty Purchasing store seeds from `purchasing_seed_v2.json`. |
| `test_dataops_auto_seed_empty_store` | `apps/dataops/backend/tests/test_dataops_backend.py` | Empty DataOps store seeds from `dataops_seed.json`. |
| `test_auto_seed_skips_non_empty_store` | each app backend test file | Startup does not duplicate existing decisions. |
| `test_no_ci_store_path_uses_current_default` | each app backend test file | Current default path behavior is unchanged when `CI_STORE_PATH` is unset. |
| `test_shared_file_collision_guard_documented_or_prevented` | `tests/scoring/test_storage.py` or app backend tests | Shared-file use is prevented or proven safe before enabling it. |

### 11d. Risk assessment

- WAL can break tests that rely on `":memory:"` unless that path is guarded.
- Explicit `db_path` arguments in existing tests must continue to override `CI_STORE_PATH`.
- A single shared SQLite file is unsafe today because `centroid_checkpoints`, `evolution_events`, and `decision_entity_edges` are not domain-scoped.
- `DecisionStore.load_latest_centroids()` can load another domain's latest centroid checkpoint if multiple domains share a file.
- `scripts/preseed_all_copilots.py` should not be imported into app startup because it calls running HTTP APIs.
- SQLite WAL improves read/write behavior but still has one-writer constraints; add retry or `busy_timeout` only if concurrent write tests show a need.
- Archive deletion should explicitly delete `outcomes` before `decisions` because current storage code does not enable `PRAGMA foreign_keys=ON`.

---

## 12. Verification Commands

Baseline commands run during this analysis:

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest tests/ -q --timeout=120
```

Observed result: `654 passed, 1308 warnings in 69.63s`.

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest apps/trading/backend/tests/ -q --timeout=120
```

Observed result: `261 passed, 522 warnings in 10.17s`.

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120
```

Observed result: `93 passed, 186 warnings in 6.69s`.

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest apps/dataops/backend/tests/ -q --timeout=120
```


Observed result: `156 passed, 312 warnings in 13.74s`.

Planned automated commands after implementation:

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest tests/scoring/test_storage.py -q --timeout=120
python -m pytest tests/ -q --timeout=120
python -m pytest apps/trading/backend/tests/ -q --timeout=120
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120
python -m pytest apps/dataops/backend/tests/ -q --timeout=120
```

Expected counts for new planned tests are to be recorded after implementation. Existing observed baselines are listed above.

Manual smoke commands:

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
Remove-Item Env:\CI_STORE_PATH -ErrorAction SilentlyContinue
python demo.py
```

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
$env:CI_STORE_PATH = "C:\tmp\ci-store-sdk-persist"
New-Item -ItemType Directory -Force $env:CI_STORE_PATH | Out-Null
python -m pytest apps/trading/backend/tests/ -q --timeout=120
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120
python -m pytest apps/dataops/backend/tests/ -q --timeout=120
Remove-Item Env:\CI_STORE_PATH -ErrorAction SilentlyContinue
```

Inspect a SQLite file:

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -c "import sqlite3; p=r'C:\tmp\ci-store-sdk-persist\trading.db'; con=sqlite3.connect(p); print(con.execute('PRAGMA journal_mode').fetchone()[0]); print(con.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\").fetchall()); print(con.execute('SELECT COUNT(*) FROM decisions').fetchone()[0]); con.close()"
```

Validate this document:

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -c "from pathlib import Path; text=Path('docs/storage_architecture.md').read_text(encoding='utf-8'); [(_ for _ in ()).throw(AssertionError(f'Missing {section}')) for section in ['## 7','## 8','## 9','## 10','## 11','## 12'] if section not in text]; start=text.find('## 7'); assert ('TO'+'DO') not in text[start:]; assert ('FI'+'LL') not in text[start:]; print('storage_architecture.md sections 7-12 present and no placeholder sentinels')"
```

## §13 — Fixed State Specification

### §13.1 DecisionStore Is Deleted

`copilot_sdk/scoring/storage.py` (the DecisionStore class) is
absorbed into `copilot_sdk/graph/sqlite_store.py` (SQLiteGraphStore).
All SQL from DecisionStore moves into SQLiteGraphStore. DecisionStore
stops existing as a class.

After the fix:
```
grep -r "DecisionStore" copilot_sdk/ apps/ --include="*.py" | grep -v test | grep -v __pycache__
# Expected: ZERO matches
```

### §13.2 GraphStore Protocol (Complete)

Every method takes `domain` as first parameter (where applicable).
Every query filters by domain.

```python
class GraphStore(Protocol):
    # Decisions
    def write_decision(self, domain, category, action, confidence, factors, ...) -> str: ...
    def write_outcome(self, decision_id, actual_action, is_correct, ...) -> None: ...
    def get_decision(self, decision_id) -> dict | None: ...
    def get_decisions(self, domain, category=None, limit=400) -> list[dict]: ...
    def get_all_decisions(self, domain) -> list[dict]: ...
    def get_verified_decisions(self, domain) -> list[dict]: ...

    # Counts
    def count_verified(self, domain) -> int: ...
    def count_correct(self, domain) -> int: ...
    def count_decisions(self, domain) -> int: ...

    # Centroids
    def save_centroids(self, domain, category, centroids, ...) -> None: ...
    def load_latest_centroids(self, domain) -> dict | None: ...
    def get_centroid_checkpoints(self, domain, ...) -> list[dict]: ...

    # Evolution
    def save_evolution_event(self, domain, ...) -> None: ...
    def get_evolution_events(self, domain, ...) -> list[dict]: ...

    # Lifecycle
    def archive_old_decisions(self, domain, keep_recent=800) -> int: ...
    def count_archived(self, domain) -> int: ...
    def close(self) -> None: ...
```

### §13.3 All Tables Domain-Scoped

Every table has `domain TEXT NOT NULL` with an index. Every INSERT
writes domain. Every SELECT filters by domain. See §2 of fixed
state spec for exact CREATE TABLE statements.

### §13.4 Scorer Uses GraphStore Only

```python
class CompoundingScorer:
    def __init__(self, ..., graph_store: GraphStore):
        self._graph_store = graph_store   # ONLY storage reference
        # NO self._store

    def score(self, context):
        self._graph_store.write_decision(domain=self._domain, ...)

    def learn(self, decision_id, actual_action, ...):
        self._graph_store.get_decision(decision_id)
        self._graph_store.write_outcome(decision_id, ...)
        self._graph_store.save_centroids(domain=self._domain, ...)

    @classmethod
    def from_preset(cls, domain, db_path=None, graph_store=None):
        gs = graph_store or SQLiteGraphStore(db_path, domain=domain)
        return cls(..., graph_store=gs)  # NO DecisionStore
```

### §13.5 App Backends Use CI_DATA_DIR

```python
def create_app(db_path=None):
    data_dir = os.environ.get("CI_DATA_DIR")
    if data_dir:
        scoring_db = str(Path(data_dir) / "trading.db")
    else:
        scoring_db = str(db_path or DEFAULT_DB_PATH)

    graph_store = SQLiteGraphStore(scoring_db, domain="trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=graph_store)
    # ONE store. ONE connection. ONE file.
```

---

## §14 — Implementation Sequence

### §14.1 Three Prompts, Sequenced

Each prompt depends on the prior. Each is independently testable.
Each is preceded by a design verification prompt.

```
Prompt 0-A: ABSORB verification (design, no code)
  → Codex maps every DecisionStore reference
  → Codex maps GraphStore protocol gaps
  → Codex maps InMemoryGraphStore gaps
  → Produces exact file list and method inventory for Prompt 1

Prompt 1: ABSORB + DOMAIN-SCOPE (implementation)
  → Delete DecisionStore class
  → Move SQL into SQLiteGraphStore
  → Domain-scope all tables
  → Update GraphStore protocol
  → Update InMemoryGraphStore
  → WAL mode
  → Migration for existing DBs

Prompt 0-B: SCORER-PROMOTE verification (design, no code)
  → Codex maps every self._store reference in scorer
  → Codex maps from_preset() flow
  → Codex maps test files that mock DecisionStore
  → Produces exact change list for Prompt 2

Prompt 2: SCORER-PROMOTE (implementation)
  → Remove self._store from CompoundingScorer
  → All scorer writes through self._graph_store
  → Update from_preset()
  → Update all affected tests

Prompt 3: PERSIST + AUTO-SEED (implementation)
  → CI_DATA_DIR env var in backends
  → Auto-seed from fixtures on empty
  → Bounded retention (archive)
  → demo.py already updated (v4)
```

### §14.2 Verification After Each Prompt

After Prompt 1:
```bash
grep -r "class DecisionStore" copilot_sdk/
# Expected: ZERO (class deleted)
python -m pytest tests/ -q --timeout=120
python -m pytest apps/*/backend/tests/ -q --timeout=120
```

After Prompt 2:
```bash
grep -r "self._store" copilot_sdk/scoring/scorer.py
# Expected: ZERO
grep -r "DecisionStore" copilot_sdk/ apps/ --include="*.py" | grep -v test | grep -v __pycache__
# Expected: ZERO
```

After Prompt 3:
```bash
python demo.py --reset
python demo.py --sdk --no-browser
# [SEED] messages
python demo.py --status
# decision counts > 0
```

---

## §15 — ABSORB Analysis

This section analyzes the exact current scope of absorbing `DecisionStore` into `SQLiteGraphStore`, using §13 as authority. Pre-append check: §13 exists at `docs/storage_architecture.md:459`, and §13.2 defines the fixed target `GraphStore` protocol at `docs/storage_architecture.md:474`. A pre-append search for `§15` / `## 15` in `docs/storage_architecture.md` returned no matches, so this section was appended instead of replacing existing content.

### §15.1 DecisionStore reference census

Searches run:

- `rg -n "DecisionStore" copilot_sdk apps scripts tests -g "*.py"`
- `rg -n "from.*storage.*import|import.*storage" copilot_sdk apps tests -g "*.py"`

No `DecisionStore` references were found under `scripts/` in the first search. Direct storage imports were found in production SDK code and tests; no app production direct storage import was found outside a Trading data-import comment.

| File | Line | Usage Type | Classification | Notes |
|---|---:|---|---|---|
| `copilot_sdk/scoring/storage.py` | 37 | class definition | MUST_CHANGE | `DecisionStore` class itself; §13.1 requires deletion/absorption. |
| `copilot_sdk/scoring/scorer.py` | 21 | import | MUST_CHANGE | Imports `DecisionStore` directly. |
| `copilot_sdk/scoring/scorer.py` | 92 | type hint / constructor dependency | MUST_CHANGE | `CompoundingScorer.__init__` accepts `store: DecisionStore`. |
| `copilot_sdk/scoring/scorer.py` | 149 | instantiation | MUST_CHANGE | `CompoundingScorer.from_preset` constructs `DecisionStore(db_path)`. |
| `copilot_sdk/scoring/scorer.py` | 794 | property type hint | MUST_CHANGE | `store` property exposes `DecisionStore`. |
| `copilot_sdk/graph/sqlite_store.py` | 1 | module docstring | MUST_CHANGE | Describes adapter as backed by `DecisionStore`. |
| `copilot_sdk/graph/sqlite_store.py` | 11 | import | MUST_CHANGE | Imports `DecisionStore`. |
| `copilot_sdk/graph/sqlite_store.py` | 15 | class docstring | MUST_CHANGE | Describes open-call-close adapter over `DecisionStore`. |
| `copilot_sdk/graph/sqlite_store.py` | 40 | instantiation | MUST_CHANGE | `write_decision` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 71 | instantiation | MUST_CHANGE | `write_outcome` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 85 | instantiation | MUST_CHANGE | `get_decision` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 99 | instantiation | MUST_CHANGE | `get_decisions` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 111 | instantiation | MUST_CHANGE | `get_verified_decisions` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 121 | instantiation | MUST_CHANGE | `count_verified` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 128 | instantiation | MUST_CHANGE | `count_correct` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 149 | instantiation | MUST_CHANGE | `save_centroids` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 174 | instantiation | MUST_CHANGE | `get_centroid_checkpoints` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 194 | instantiation | MUST_CHANGE | `save_evolution_event` opens `DecisionStore(self.db_path)` for its connection. |
| `copilot_sdk/graph/sqlite_store.py` | 231 | instantiation | MUST_CHANGE | `link_decision_to_entity` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 247 | instantiation | MUST_CHANGE | `get_decision_links` opens `DecisionStore(self.db_path)`. |
| `copilot_sdk/graph/sqlite_store.py` | 275 | type hint | MUST_CHANGE | `_ensure_edges_table(self, store: DecisionStore)` depends on the class. |
| `apps/trading/backend/app/routers/data_import.py` | 18 | comment | MUST_CHANGE | Comment says production should replace demo list with SQLite/DecisionStore; after §13 this should name GraphStore instead. |
| `tests/test_consolidation.py` | 20 | import | TEST_ONLY | Test imports `DecisionStore`. |
| `tests/test_consolidation.py` | 46 | instantiation | TEST_ONLY | Test constructs `DecisionStore(tmp_path / "consolidation.sqlite")`. |
| `tests/test_bitemporal_scorer.py` | 23 | import | TEST_ONLY | Test imports `DecisionStore`. |
| `tests/test_bitemporal_scorer.py` | 62 | instantiation | TEST_ONLY | Test passes a `DecisionStore` into `CompoundingScorer`. |
| `tests/test_learn_context.py` | 11 | import | TEST_ONLY | Test imports `DecisionStore`. |
| `tests/test_learn_context.py` | 53 | instantiation | TEST_ONLY | Test constructs `DecisionStore(tmp_path / "context.sqlite")`. |
| `tests/test_learn_context.py` | 70 | instantiation | TEST_ONLY | Test constructs `DecisionStore(tmp_path / "default-sqlite.sqlite")`. |
| `tests/test_learn_context.py` | 108 | instantiation | TEST_ONLY | Test constructs `DecisionStore(tmp_path / "store.sqlite")`. |
| `tests/test_learn_context.py` | 190 | instantiation | TEST_ONLY | Test constructs `DecisionStore(db_path)` after creating legacy tables. |
| `tests/test_judgment_conflict.py` | 26 | import | TEST_ONLY | Test imports `DecisionStore`. |
| `tests/test_judgment_conflict.py` | 52 | instantiation | TEST_ONLY | Test constructs `DecisionStore(tmp_path / "conflict.sqlite")`. |
| `tests/test_archetype_generator.py` | 17 | import | TEST_ONLY | Test imports `DecisionStore`. |
| `tests/test_archetype_generator.py` | 158 | instantiation | TEST_ONLY | Test constructs `DecisionStore(tmp_path / "generated.sqlite")`. |
| `tests/test_graph_entity_links.py` | 12 | import | TEST_ONLY | Test imports `DecisionStore`. |
| `tests/test_graph_entity_links.py` | 118 | instantiation | TEST_ONLY | Test constructs `DecisionStore(tmp_path / "links.sqlite")`. |
| `tests/scoring/test_storage.py` | 8 | import | TEST_ONLY | Storage tests import `DecisionStore`. |
| `tests/scoring/test_storage.py` | 249 | instantiation | TEST_ONLY | Migration test constructs `DecisionStore(db_path)`. |
| `tests/scoring/test_storage.py` | 272 | instantiation | TEST_ONLY | Test constructs `DecisionStore(db_path)`. |
| `tests/scoring/test_storage.py` | 329 | instantiation | TEST_ONLY | Test constructs `DecisionStore(temp_db)`. |
| `tests/scoring/test_storage.py` | 333 | instantiation | TEST_ONLY | Test reopens `DecisionStore(temp_db)`. |
| `tests/scoring/test_scorer.py` | 619 | assertion string | TEST_ONLY | Test asserts legacy `DecisionStore` data path is not used. |
| `tests/graph/test_sqlite_store.py` | 9 | import | TEST_ONLY | Graph tests import `DecisionStore`. |
| `tests/graph/test_sqlite_store.py` | 173 | instantiation | TEST_ONLY | Migration test constructs `DecisionStore(db_path)`. |
| `tests/graph/test_sqlite_store.py` | 187 | instantiation | TEST_ONLY | Test constructs first `DecisionStore(db_path)`. |
| `tests/graph/test_sqlite_store.py` | 190 | instantiation | TEST_ONLY | Test constructs second `DecisionStore(db_path)`. |
| `tests/graph/test_sqlite_store.py` | 318 | instantiation | TEST_ONLY | Test constructs raw `DecisionStore(db_path)`. |
| `tests/scoring/conftest.py` | 9 | import | TEST_ONLY | Test fixture imports `DecisionStore`. |
| `tests/scoring/conftest.py` | 52 | instantiation | TEST_ONLY | Fixture constructs `DecisionStore(temp_db)`. |
| `apps/trading/backend/tests/test_trading_backend.py` | 408 | import | TEST_ONLY | App backend test imports `DecisionStore`. |
| `apps/trading/backend/tests/test_trading_backend.py` | 411 | instantiation | TEST_ONLY | Test constructs `DecisionStore(db_path)`. |
| `apps/trading/backend/tests/test_trading_backend.py` | 429 | import | TEST_ONLY | App backend test imports `DecisionStore`. |
| `apps/trading/backend/tests/test_trading_backend.py` | 432 | instantiation | TEST_ONLY | Test constructs `DecisionStore(db_path)`. |
| `apps/trading/backend/tests/test_trading_backend.py` | 493 | import | TEST_ONLY | App backend test imports `DecisionStore`. |
| `apps/trading/backend/tests/test_trading_backend.py` | 499 | instantiation | TEST_ONLY | Test constructs `DecisionStore(db_path)`. |
| `apps/purchasing/backend/tests/test_purchasing_backend.py` | 551 | import | TEST_ONLY | App backend test imports `DecisionStore`. |
| `apps/purchasing/backend/tests/test_purchasing_backend.py` | 554 | instantiation | TEST_ONLY | Test constructs `DecisionStore(db_path)`. |
| `apps/purchasing/backend/tests/test_purchasing_backend.py` | 572 | import | TEST_ONLY | App backend test imports `DecisionStore`. |
| `apps/purchasing/backend/tests/test_purchasing_backend.py` | 575 | instantiation | TEST_ONLY | Test constructs `DecisionStore(db_path)`. |
| `apps/purchasing/backend/tests/test_purchasing_backend.py` | 667 | import | TEST_ONLY | App backend test imports `DecisionStore`. |
| `apps/purchasing/backend/tests/test_purchasing_backend.py` | 673 | instantiation | TEST_ONLY | Test constructs `DecisionStore(db_path)`. |

### §15.2 GraphStore protocol gap analysis

Current protocol source: `copilot_sdk/graph/protocol.py:9`. Target protocol source: §13.2 at `docs/storage_architecture.md:474`.

| Method | Current Protocol | Target Protocol | Gap? |
|---|---|---|---|
| `write_decision` | `copilot_sdk/graph/protocol.py:12` takes `entity_id, category, action, confidence, factors, metadata` | `docs/storage_architecture.md:482` requires `domain, category, action, confidence, factors, ...` | Signature mismatch: current lacks first-class `domain` and has `entity_id` as first argument. |
| `write_outcome` | `copilot_sdk/graph/protocol.py:23` takes `decision_id, actual_action, is_correct, metadata` | `docs/storage_architecture.md:483` uses `decision_id, actual_action, is_correct, ...` | Mostly aligned; no explicit domain in target line. |
| `get_decision` | `copilot_sdk/graph/protocol.py:32` takes `decision_id` | `docs/storage_architecture.md:484` takes `decision_id` | Aligned by signature. |
| `get_decisions` | `copilot_sdk/graph/protocol.py:35` takes `category=None, limit=400` | `docs/storage_architecture.md:485` requires `domain, category=None, limit=400` | Missing `domain`. |
| `get_all_decisions` | `copilot_sdk/graph/protocol.py:51` takes no domain | `docs/storage_architecture.md:486` requires `domain` | Missing `domain`. |
| `get_verified_decisions` | `copilot_sdk/graph/protocol.py:42` takes no domain | `docs/storage_architecture.md:487` requires `domain` | Missing `domain`. |
| `count_verified` | `copilot_sdk/graph/protocol.py:45` takes no domain | `docs/storage_architecture.md:490` requires `domain` | Missing `domain`. |
| `count_correct` | `copilot_sdk/graph/protocol.py:48` takes no domain | `docs/storage_architecture.md:491` requires `domain` | Missing `domain`. |
| `count_decisions` | Not found in `copilot_sdk/graph/protocol.py:9-89` | `docs/storage_architecture.md:492` requires `count_decisions(domain)` | Missing method. |
| `save_centroids` | `copilot_sdk/graph/protocol.py:54` takes `decision_id, category, centroids, metadata, ...` | `docs/storage_architecture.md:495` requires `domain, category, centroids, ...` | Signature mismatch; missing domain and target removes leading `decision_id` from required position. |
| `load_latest_centroids` | Not found in `copilot_sdk/graph/protocol.py:9-89` | `docs/storage_architecture.md:496` requires `load_latest_centroids(domain)` | Missing method. |
| `get_centroid_checkpoints` | `copilot_sdk/graph/protocol.py:67` takes filters, no domain | `docs/storage_architecture.md:497` requires `domain, ...` | Missing `domain`. |
| `save_evolution_event` | `copilot_sdk/graph/protocol.py:79` takes `event_type, rule_name, variant_id, metadata` | `docs/storage_architecture.md:500` requires `domain, ...` | Missing `domain`. |
| `get_evolution_events` | Not found in `copilot_sdk/graph/protocol.py:9-89` | `docs/storage_architecture.md:501` requires `get_evolution_events(domain, ...)` | Missing method. |
| `archive_old_decisions` | Not found in `copilot_sdk/graph/protocol.py:9-89` | `docs/storage_architecture.md:504` requires `archive_old_decisions(domain, keep_recent=800)` | Missing method. |
| `count_archived` | Not found in `copilot_sdk/graph/protocol.py:9-89` | `docs/storage_architecture.md:505` requires `count_archived(domain)` | Missing method. |
| `close` | `copilot_sdk/graph/protocol.py:88` | `docs/storage_architecture.md:506` | Aligned. |

### §15.3 SQLiteGraphStore delegation map

Source read fully: `copilot_sdk/graph/sqlite_store.py`.

Constructor signature: `SQLiteGraphStore.__init__(self, db_path: str | Path, domain: str = "graph")` at `copilot_sdk/graph/sqlite_store.py:17`. It stores `self.db_path` and `self.domain` at `copilot_sdk/graph/sqlite_store.py:18-19`. It does not keep its own `sqlite3` connection; instead, most methods open `DecisionStore(self.db_path)` per call and close it. It creates tables directly only through SQL executed on a `DecisionStore.connection`.

| Method | Delegates to DecisionStore? | Own SQL? | Notes |
|---|---|---|---|
| `__init__` | No | No | Stores path/domain only at `copilot_sdk/graph/sqlite_store.py:17-19`. |
| `write_decision` | Yes | No | Opens `DecisionStore` and calls `store.save_decision` at `copilot_sdk/graph/sqlite_store.py:40-58`. |
| `write_outcome` | Yes | No | Opens `DecisionStore` and calls `store.save_outcome` at `copilot_sdk/graph/sqlite_store.py:71-80`. |
| `get_decision` | Yes | No | Opens `DecisionStore` and calls `store.get_decision` at `copilot_sdk/graph/sqlite_store.py:85-89`. |
| `get_decisions` | Yes | No | Opens `DecisionStore` and filters `store.get_all_decisions()` at `copilot_sdk/graph/sqlite_store.py:99-106`. |
| `get_verified_decisions` | Yes | No | Opens `DecisionStore` and calls `store.get_verified_decisions` at `copilot_sdk/graph/sqlite_store.py:111-116`. |
| `count_verified` | Yes | No | Opens `DecisionStore` and calls `store.count_verified` at `copilot_sdk/graph/sqlite_store.py:120-125`. |
| `count_correct` | Yes | No | Opens `DecisionStore` and calls `store.count_correct` at `copilot_sdk/graph/sqlite_store.py:127-132`. |
| `get_all_decisions` | Indirect | No | Calls `self.get_decisions(...)` at `copilot_sdk/graph/sqlite_store.py:134-135`. |
| `save_centroids` | Yes | No | Opens `DecisionStore` and calls `store.save_centroids` at `copilot_sdk/graph/sqlite_store.py:149-160`. |
| `get_centroid_checkpoints` | Yes | No | Opens `DecisionStore` and calls `store.get_centroid_checkpoints` at `copilot_sdk/graph/sqlite_store.py:174-183`. |
| `save_evolution_event` | Yes, for connection lifecycle | Yes | Opens `DecisionStore`, creates/inserts `evolution_events` with raw SQL at `copilot_sdk/graph/sqlite_store.py:194-221`. |
| `link_decision_to_entity` | Yes, for connection lifecycle | Yes | Opens `DecisionStore`, calls `_ensure_edges_table`, inserts into `decision_entity_edges` at `copilot_sdk/graph/sqlite_store.py:231-242`. |
| `get_decision_links` | Yes, for connection lifecycle | Yes | Opens `DecisionStore`, ensures table, selects from `decision_entity_edges` at `copilot_sdk/graph/sqlite_store.py:247-268`. |
| `close` | No | No | No-op at `copilot_sdk/graph/sqlite_store.py:272-273`. |
| `_ensure_edges_table` | No | Yes | Creates `decision_entity_edges` at `copilot_sdk/graph/sqlite_store.py:275-287`. |
| `_normalize_decision` | No | No | Normalizes metadata/entity fields at `copilot_sdk/graph/sqlite_store.py:289-299`. |

Tables created directly by `SQLiteGraphStore`, not via `DecisionStore`: `evolution_events` at `copilot_sdk/graph/sqlite_store.py:198` and `decision_entity_edges` at `copilot_sdk/graph/sqlite_store.py:278`.

Current architecture: `SQLiteGraphStore` is an adapter over `DecisionStore`, not the owner of the core SQLite schema. Absorption implication: all `DecisionStore` DDL and methods must move into `SQLiteGraphStore`, and all per-call `DecisionStore(self.db_path)` creation must be replaced by internal connection handling or a consolidated helper owned by `SQLiteGraphStore`.

### §15.4 InMemoryGraphStore gap analysis

Source read fully: `copilot_sdk/graph/memory_store.py`. The requested filename `copilot_sdk/graph/in_memory_store.py` was not found; the equivalent implementation is `copilot_sdk/graph/memory_store.py`, with class `InMemoryGraphStore` at `copilot_sdk/graph/memory_store.py:16`.

| Method | Implemented? | Has domain param? | Notes |
|---|---|---|---|
| `write_decision` | Yes at `copilot_sdk/graph/memory_store.py:28` | No | Same current protocol shape as `entity_id, category, action, confidence, factors, metadata`. |
| `write_outcome` | Yes at `copilot_sdk/graph/memory_store.py:58` | No | Target line does not require domain. |
| `get_decision` | Yes at `copilot_sdk/graph/memory_store.py:75` | No | Target line does not require domain. |
| `get_decisions` | Yes at `copilot_sdk/graph/memory_store.py:79` | No | Needs domain for §13.2 target. |
| `get_all_decisions` | Yes at `copilot_sdk/graph/memory_store.py:113` | No | Needs domain for §13.2 target. |
| `get_verified_decisions` | Yes at `copilot_sdk/graph/memory_store.py:91` | No | Needs domain for §13.2 target. |
| `count_verified` | Yes at `copilot_sdk/graph/memory_store.py:107` | No | Needs domain for §13.2 target. |
| `count_correct` | Yes at `copilot_sdk/graph/memory_store.py:110` | No | Needs domain for §13.2 target. |
| `count_decisions` | No | No | Missing target method from `docs/storage_architecture.md:492`. |
| `save_centroids` | Yes at `copilot_sdk/graph/memory_store.py:116` | No | Signature mismatch; target requires domain. |
| `load_latest_centroids` | No | No | Missing target method from `docs/storage_architecture.md:496`. |
| `get_centroid_checkpoints` | Yes at `copilot_sdk/graph/memory_store.py:140` | No | Needs domain for §13.2 target. |
| `save_evolution_event` | Yes at `copilot_sdk/graph/memory_store.py:167` | No | Needs domain for §13.2 target. |
| `get_evolution_events` | No | No | Missing target method from `docs/storage_architecture.md:501`. |
| `archive_old_decisions` | No | No | Missing target method from `docs/storage_architecture.md:504`. |
| `count_archived` | No | No | Missing target method from `docs/storage_architecture.md:505`. |
| `close` | Yes at `copilot_sdk/graph/memory_store.py:215` | No | Aligned. |

Additional implemented methods not in the current protocol but used by graph tests: `link_decision_to_entity` at `copilot_sdk/graph/memory_store.py:184`, `get_decision_links` at `copilot_sdk/graph/memory_store.py:199`, and `reset` at `copilot_sdk/graph/memory_store.py:207`.

### §15.5 Scorer storage bypass map

Source read fully: `copilot_sdk/scoring/scorer.py`.

Storage constructor evidence: `CompoundingScorer.__init__` accepts `store: DecisionStore` and optional `graph_store: GraphStore | None` at `copilot_sdk/scoring/scorer.py:89-95`, assigns `self._store = store` at `copilot_sdk/scoring/scorer.py:102`, creates fallback `SQLiteGraphStore(store.db_path, domain=preset.name)` at `copilot_sdk/scoring/scorer.py:104-107`, and stores `self._graph_store = graph_store` at `copilot_sdk/scoring/scorer.py:108`. `CompoundingScorer.from_preset` constructs `DecisionStore(db_path)` at `copilot_sdk/scoring/scorer.py:149`, loads centroids through `store.load_latest_centroids()` at `copilot_sdk/scoring/scorer.py:150`, and creates `SQLiteGraphStore(db_path, domain=preset.name)` at `copilot_sdk/scoring/scorer.py:153-156`.

| Method | `self._store` refs | `self._graph_store` refs | Notes |
|---|---|---|---|
| `__init__` | Sets `self._store` at `copilot_sdk/scoring/scorer.py:102` | Fallback creation and assignment at `copilot_sdk/scoring/scorer.py:104-108` | MUST_CHANGE: §13.4 requires no `self._store`. |
| `from_preset` | Creates local `store = DecisionStore(db_path)` at `copilot_sdk/scoring/scorer.py:149`; loads centroids at `copilot_sdk/scoring/scorer.py:150` | Creates `SQLiteGraphStore` when not provided at `copilot_sdk/scoring/scorer.py:153-156` | MUST_CHANGE: target must create/use GraphStore only. |
| `score` | None | Writes decision via `_graph_store.write_decision` at `copilot_sdk/scoring/scorer.py:213-220` | Already graph-first but target signature needs domain. |
| `learn` | None | Reads decision at `copilot_sdk/scoring/scorer.py:242`, writes outcome at `copilot_sdk/scoring/scorer.py:298`, optionally links entity at `copilot_sdk/scoring/scorer.py:305-307`, saves centroids through helper at `copilot_sdk/scoring/scorer.py:332-338` | Already graph-first but target signatures need domain. |
| `fingerprint` | None | Uses `_graph_store.get_verified_decisions()` at `copilot_sdk/scoring/scorer.py:369-373` | Needs domain-aware call after protocol update. |
| `trajectory` | None | Uses `_graph_store.get_centroid_checkpoints()` and `_graph_store.get_verified_decisions()` at `copilot_sdk/scoring/scorer.py:400-418` | Needs domain-aware calls after protocol update. |
| `get_phase` | None | Uses `_graph_store.count_verified()` and `count_correct()` at `copilot_sdk/scoring/scorer.py:421-429` | Needs domain-aware calls after protocol update. |
| `get_alpha` | None | Uses `_graph_store.count_verified()` and `count_correct()` at `copilot_sdk/scoring/scorer.py:433-440` | Needs domain-aware calls after protocol update. |
| `warm_start` | None | Optional `_graph_store.save_centroids` call at `copilot_sdk/scoring/scorer.py:490-503` | Needs domain-aware `save_centroids`. |
| `export` | None | Uses `_graph_store.get_all_decisions()` at `copilot_sdk/scoring/scorer.py:515-531` | Needs domain-aware call. |
| `load` | None directly | Calls `from_preset` at `copilot_sdk/scoring/scorer.py:533-537` | Inherits `from_preset` DecisionStore bypass risk. |
| `_compute_iks` | None | Uses `count_verified`, `count_correct`, and `get_verified_decisions` at `copilot_sdk/scoring/scorer.py:540-573` | Needs domain-aware calls. |
| `_conservation_pause` | None | Calls `_conservation_stats(self._graph_store)` at `copilot_sdk/scoring/scorer.py:575-595` | Helper must handle domain-aware GraphStore. |
| `_save_centroids_checkpoint` | None | Calls `_graph_store.save_centroids` at `copilot_sdk/scoring/scorer.py:663-689` | Needs domain-aware `save_centroids`. |
| `_setup_evolution` | None | Passes `_graph_store` to `InMemoryEvolutionLedger` at `copilot_sdk/scoring/scorer.py:733` | Ledger behavior may need target protocol adaptation. |
| `_run_evolution` | None | Uses `_graph_store.get_verified_decisions()` at `copilot_sdk/scoring/scorer.py:745-760` | Needs domain-aware call. |
| `_evolution_conservation_state` | None | Calls `_conservation_stats(self._graph_store)` at `copilot_sdk/scoring/scorer.py:763-786` | Helper must handle domain-aware GraphStore. |
| `graph_store` property | None | Returns `_graph_store` at `copilot_sdk/scoring/scorer.py:788-791` | Keep. |
| `store` property | Returns `_store` at `copilot_sdk/scoring/scorer.py:793-795` | None | MUST_CHANGE: §13.4 says no `self._store`. |

### §15.6 Router storage references

Sources read: `copilot_sdk/backend/scoring_router.py`, `copilot_sdk/backend/conservation_router.py`, `copilot_sdk/backend/evolution_router.py`, `copilot_sdk/backend/scorer_proxy.py`, and app `main.py` files via `rg -n "DecisionStore|_store|graph_store|GraphStore" apps -g "main.py"`.

| File | Storage Access Pattern | DecisionStore Direct? | GraphStore Direct? | Notes |
|---|---|---|---|---|
| `copilot_sdk/backend/scoring_router.py` | Through scorer, then `_scorer_data_store` checks `graph_store`, `_graph_store`, `store`, `_store` at `copilot_sdk/backend/scoring_router.py:213-218` | No direct import | Indirect via scorer/store attributes | `history()` calls `get_decisions` or `get_all_decisions` on resolved store at `copilot_sdk/backend/scoring_router.py:131-141`; this must prefer GraphStore-only after absorption. |
| `copilot_sdk/backend/conservation_router.py` | Through `state_provider`; `_state_counts` resolves direct count methods or `graph_store`, `_graph_store`, `store`, `_store` at `copilot_sdk/backend/conservation_router.py:100-138` | No direct import | Indirect via provider/state | Needs domain-aware count methods after protocol update. |
| `copilot_sdk/backend/evolution_router.py` | `create_evolution_router` accepts `graph_store_factory` and wraps it in `InMemoryEvolutionLedger` at `copilot_sdk/backend/evolution_router.py:18-38` | No | Yes, via factory | Legacy mode can also use `ledger_provider` at `copilot_sdk/backend/evolution_router.py:24-31`. |
| `copilot_sdk/backend/scorer_proxy.py` | Stores graph store facade as `self.store` and creates fresh scorer through `CompoundingScorer.from_preset(..., db_path=self._db_path)` at `copilot_sdk/backend/scorer_proxy.py:22-27` | No direct import | Indirect via graph store factory | `_close_scorer_store` closes scorer `_store` at `copilot_sdk/backend/scorer_proxy.py:76-81`; must change when `_store` is removed. |
| `apps/trading/backend/app/main.py` | Creates `SQLiteGraphStore` in `_graph_store`, passes it to routers/factories | No | Yes | Evidence: import at `apps/trading/backend/app/main.py:31`, `_graph_store` at `apps/trading/backend/app/main.py:54-57`, router uses at `apps/trading/backend/app/main.py:71-97`. |
| `apps/purchasing/backend/app/main.py` | Creates `SQLiteGraphStore` in `_graph_store`, passes it to routers/factories | No | Yes | Evidence: import at `apps/purchasing/backend/app/main.py:32`, `_graph_store` at `apps/purchasing/backend/app/main.py:54-57`, router uses at `apps/purchasing/backend/app/main.py:123-146`. |
| `apps/dataops/backend/app/main.py` | Creates `SQLiteGraphStore` in `_graph_store`, passes it to routers/factories | No | Yes | Evidence: import at `apps/dataops/backend/app/main.py:35`, `_graph_store` at `apps/dataops/backend/app/main.py:57-60`, router uses at `apps/dataops/backend/app/main.py:86-110`. |

### §15.7 Test impact assessment

Reference counts from read-only scan:

- `tests/`: 28 `DecisionStore` string references across 10 files.
- `apps/*/backend/tests/`: 12 `DecisionStore` string references across 2 files.

| Test File | References | Classification | Effort |
|---|---:|---|---|
| `tests/test_archetype_generator.py` | 2 | IMPORT_CHANGE_ONLY | low |
| `tests/test_bitemporal_scorer.py` | 2 | LOGIC_CHANGE | medium |
| `tests/test_consolidation.py` | 2 | LOGIC_CHANGE | medium |
| `tests/test_graph_entity_links.py` | 2 | LOGIC_CHANGE | medium |
| `tests/test_judgment_conflict.py` | 2 | LOGIC_CHANGE | medium |
| `tests/test_learn_context.py` | 5 | LOGIC_CHANGE | high |
| `tests/graph/test_sqlite_store.py` | 5 | LOGIC_CHANGE | high |
| `tests/scoring/conftest.py` | 2 | FIXTURE_CHANGE | medium |
| `tests/scoring/test_scorer.py` | 1 | IMPORT_CHANGE_ONLY | low |
| `tests/scoring/test_storage.py` | 5 | LOGIC_CHANGE | high |
| `apps/trading/backend/tests/test_trading_backend.py` | 6 | LOGIC_CHANGE | medium |
| `apps/purchasing/backend/tests/test_purchasing_backend.py` | 6 | LOGIC_CHANGE | medium |

Evidence examples: direct test imports occur at `tests/scoring/test_storage.py:8`, `tests/graph/test_sqlite_store.py:9`, `tests/scoring/conftest.py:9`, `apps/trading/backend/tests/test_trading_backend.py:408`, and `apps/purchasing/backend/tests/test_purchasing_backend.py:551`. Schema migration and raw-table tests are high impact because they instantiate `DecisionStore` against handcrafted tables, e.g. `tests/test_learn_context.py:190`, `tests/graph/test_sqlite_store.py:173`, and `tests/scoring/test_storage.py:249`.

### §15.8 Migration risk

Expected app database paths are grounded in app mains: Trading default `apps/trading/backend/data/trading.db` at `apps/trading/backend/app/main.py:35-36`, Purchasing default `apps/purchasing/backend/data/purchasing.db` at `apps/purchasing/backend/app/main.py:35-36`, and DataOps default `apps/dataops/backend/data/dataops.db` at `apps/dataops/backend/app/main.py:38-39`.

Read-only SQLite inspection found these existing files:

- `apps/dataops/backend/data/dataops.db`
- `apps/purchasing/backend/data/purchasing.db`
- `apps/trading/backend/data/trading.db`

| DB File | Table | Columns | Domain Column? | Migration Needed? | Risk Notes |
|---|---|---|---|---|---|
| `apps/dataops/backend/data/dataops.db` | `decisions` | `decision_id`, `domain`, `category`, `category_index`, `factors_json`, `factor_vector_json`, `recommended_action`, `recommended_index`, `confidence`, `probabilities_json`, `created_at` | Yes | Yes | Must preserve rows while moving ownership from `DecisionStore` to `SQLiteGraphStore`. |
| `apps/dataops/backend/data/dataops.db` | `outcomes` | `decision_id`, `actual_action`, `actual_index`, `is_correct`, `verified_at`, `context_json` | No | Yes | §13.3 requires every table to have `domain TEXT NOT NULL`. |
| `apps/dataops/backend/data/dataops.db` | `centroid_checkpoints` | `id`, `centroids_json`, `decisions_count`, `iks`, `created_at`, `decision_id`, `category`, `metadata_json` | No | Yes | Missing domain and also lacks newer time-window columns present in other DBs. |
| `apps/purchasing/backend/data/purchasing.db` | `decisions` | `decision_id`, `domain`, `category`, `category_index`, `factors_json`, `factor_vector_json`, `recommended_action`, `recommended_index`, `confidence`, `probabilities_json`, `created_at` | Yes | Yes | Table owner changes; add indexes required by §13.3 if missing. |
| `apps/purchasing/backend/data/purchasing.db` | `outcomes` | `decision_id`, `actual_action`, `actual_index`, `is_correct`, `verified_at`, `context_json` | No | Yes | Needs domain column and migration from joined decision domain. |
| `apps/purchasing/backend/data/purchasing.db` | `centroid_checkpoints` | `id`, `centroids_json`, `decisions_count`, `iks`, `created_at`, `decision_id`, `category`, `metadata_json`, `decision_time_start`, `decision_time_end`, `checkpoint_time` | No | Yes | Needs domain column and domain-filtered latest-centroid semantics. |
| `apps/trading/backend/data/trading.db` | `decisions` | `decision_id`, `domain`, `category`, `category_index`, `factors_json`, `factor_vector_json`, `recommended_action`, `recommended_index`, `confidence`, `probabilities_json`, `created_at` | Yes | Yes | Table owner changes; add indexes required by §13.3 if missing. |
| `apps/trading/backend/data/trading.db` | `outcomes` | `decision_id`, `actual_action`, `actual_index`, `is_correct`, `verified_at`, `context_json` | No | Yes | Needs domain column and migration from joined decision domain. |
| `apps/trading/backend/data/trading.db` | `centroid_checkpoints` | `id`, `centroids_json`, `decisions_count`, `iks`, `created_at`, `decision_id`, `category`, `metadata_json`, `decision_time_start`, `decision_time_end`, `checkpoint_time` | No | Yes | Needs domain column and domain-filtered latest-centroid semantics. |
| all three DBs | `sqlite_sequence` | `name`, `seq` | No | No | SQLite internal AUTOINCREMENT table; not a domain data table. |

Migration risk summary:

- Existing DB files use `DecisionStore` table shapes, while §13.3 requires every table to be domain-scoped at `docs/storage_architecture.md:509-513`.
- `outcomes` and `centroid_checkpoints` need domain backfill.
- `dataops.db` has an older `centroid_checkpoints` shape without `decision_time_start`, `decision_time_end`, and `checkpoint_time`; this is compatible with current `DecisionStore._ensure_centroid_columns()` at `copilot_sdk/scoring/storage.py:96-132`, but absorption must preserve that migration.
- `load_latest_centroids` currently has no domain filter at `copilot_sdk/scoring/storage.py:236-245`; any migration must make latest-centroid reads domain-scoped.

### §15.9 Baseline test counts

| Command | Result | Count / Notes |
|---|---|---|
| `python -m pytest tests/ -q --timeout=120` | PASS | `654 passed, 1308 warnings in 67.81s` |
| `python -m pytest apps/trading/backend/tests/ -q --timeout=120` | PASS | `261 passed, 522 warnings in 7.28s` |
| `python -m pytest apps/purchasing/backend/tests/ -q --timeout=120` | PASS | `93 passed, 186 warnings in 4.50s` |
| `python -m pytest apps/dataops/backend/tests/ -q --timeout=120` | PASS | `156 passed, 312 warnings in 9.70s` |
