# VLD Centroid Propagation Diagnosis — Checkpoint vs Bundle

Date: 2026-09-12
Repo: copilot-sdk
Scope: diagnosis only. No source files were modified.

## 1. Centroid loading path

The active scorer path is `CompoundingScorer.from_preset()` in `copilot_sdk/scoring/scorer.py`.

1. Preset selection happens at `copilot_sdk/scoring/scorer.py:271-276`. The domain name selects a preset class from `PRESET_REGISTRY` and instantiates it.
2. If no explicit graph store is supplied, `profile='test'` uses `InMemoryGraphStore` at `copilot_sdk/scoring/scorer.py:287-290`; `profile='development'` uses `SQLiteGraphStore(db_path, domain=preset.name)` at `copilot_sdk/scoring/scorer.py:291-299`. Production rejects missing or SQLite/in-memory stores at `copilot_sdk/scoring/scorer.py:282-319`.
3. The first centroid source checked is the graph store checkpoint state: `centroids = graph_store.load_latest_centroids(preset.name)` at `copilot_sdk/scoring/scorer.py:320`.
4. `from_preset()` then asks for one latest checkpoint at `copilot_sdk/scoring/scorer.py:321-325` and compares its `factor_names_hash` with the current preset hash at `copilot_sdk/scoring/scorer.py:326-337`. A schema-hash mismatch discards the checkpoint and falls back to bootstrap.
5. If the graph store returns no usable centroid tensor, bootstrap wins: `centroids = np.array(preset.bootstrap_centroids, ...)` at `copilot_sdk/scoring/scorer.py:338-339`.
6. The resulting tensor is passed into `ProfileScorer(mu=centroids, ...)` at `copilot_sdk/scoring/scorer.py:346-353`.
7. L5 restore is not part of `from_preset()` itself. Startup-equivalent L5 overlay calls `load_centroids_from_l5()`, implemented at `copilot_sdk/scoring/scorer.py:706-730`. It copies the active tensor, validates each row’s category/action/vector shape, then overwrites only those `(category, action)` cells present in L5.
8. The startup L5 path is `copilot_sdk/scoring/startup_restore.py:142-171`: `_restore_centroids()` calls `learning_store.get_centroids(domain)`, then `scorer.load_centroids_from_l5(...)`.
9. SQLite’s checkpoint loader is `copilot_sdk/graph/sqlite_store.py:2906-2923`. It selects all `centroid_checkpoints` rows for the domain and returns the row with maximum `(created_at, id)`. That row wins over the preset bootstrap.
10. SQLite’s L5 rows are read through `get_centroids()` at `copilot_sdk/graph/sqlite_store.py:2602-2618` from the separate `l5_centroids` table.

The export path follows the same precedence. `tests/vld_validation_report.py` backs up existing app SQLite databases read-only into an in-memory `SQLiteGraphStore` at `tests/vld_validation_report.py:199-206`, reads checkpoints at `tests/vld_validation_report.py:207-211`, constructs `CompoundingScorer.from_preset(..., graph_store=store, profile='test')` at `tests/vld_validation_report.py:214-215`, and applies startup-equivalent L5 restore at `tests/vld_validation_report.py:216`. `tests/extract_real_centroids.py:18-34` delegates to that collector and exports the resulting post-L5 tensor.

Measured shapes after each source:

| Domain | Source | Shape | Per-category max action spread |
| --- | --- | --- | --- |
| Purchasing | preset bootstrap via `from_preset(profile='test')` | `(5, 4, 7)` | `[0.275437, 0.420332, 0.275757, 0.365821, 0.263886]` |
| Purchasing | empty SQLite development store | `(5, 4, 7)` | `[0.275437, 0.420332, 0.275757, 0.365821, 0.263886]` |
| Purchasing | current SQLite latest checkpoint | `(5, 4, 7)` | `[0.0, 0.0, 0.0, 0.0, 0.0]` |
| Purchasing | exported `real_centroids_v1.json` | `(5, 4, 7)` | all categories `0.000000` |
| Trading | preset bootstrap via `from_preset(profile='test')` | `(5, 4, 10)` | `[0.316681, 0.355658, 0.374777, 0.304165, 0.337872]` |
| Trading | empty SQLite development store | `(5, 4, 10)` | `[0.316681, 0.355658, 0.374777, 0.304165, 0.337872]` |
| Trading | current SQLite latest checkpoint | `(5, 4, 10)` | `[0.0, 0.0, 0.0, 0.0, 0.0]` |
| Trading | exported `real_centroids_v1.json` after L5 | `(5, 4, 10)` | `trend_following=0.526551`, `mean_reversion=0.030000`, `event_driven=0.025000`, `income_strategy=0.000000`, `scalp_intraday=0.000000` |

The source that wins for the exported runtime snapshot is therefore: latest SQLite checkpoint first, then L5 overlay if rows exist, otherwise preset bootstrap. The bundle does not participate in export unless it has already written a winning checkpoint row into the app SQLite database.

## 2. Demo bundle consumption

`scripts/regenerate_demo_bundles.py` writes JSON bundles under `demo/`. The generator builds a bundle at `scripts/regenerate_demo_bundles.py:199-215`; `centroid_checkpoints` are produced by `build_checkpoints()` at `scripts/regenerate_demo_bundles.py:403-430`.

The generator now builds differentiated action centroids. `build_centroids()` groups vectors by `(category, action)` at `scripts/regenerate_demo_bundles.py:348-360`, uses per-cell means when available at `scripts/regenerate_demo_bundles.py:375-381`, falls back to `*_bootstrap.json` per-action priors at `scripts/regenerate_demo_bundles.py:382-383`, and asserts action uniqueness at `scripts/regenerate_demo_bundles.py:390-397`.

Bundle JSONs are consumed by app startup, not by `from_preset()` directly:

- Trading imports `restore_bundle_if_empty` at `apps/trading/backend/app/main.py:91`, defaults `demo_bundle_path` to `REPO_ROOT / "demo" / f"{DOMAIN}_demo_bundle.json"` at `apps/trading/backend/app/main.py:387-392`, and calls `_restore_demo_bundle(...)` at `apps/trading/backend/app/main.py:489`.
- Purchasing imports it at `apps/purchasing/backend/app/main.py:100`, defaults the bundle path at `apps/purchasing/backend/app/main.py:516-521`, and calls `_restore_demo_bundle(...)` at `apps/purchasing/backend/app/main.py:592`.
- DataOps follows the same pattern at `apps/dataops/backend/app/main.py:75`, `apps/dataops/backend/app/main.py:648-653`, and `apps/dataops/backend/app/main.py:770`.

The restore helper is `copilot_sdk/demo/bundle.py`. It reads the bundle at `copilot_sdk/demo/bundle.py:20-40`, verifies the domain at `copilot_sdk/demo/bundle.py:43-47`, gets the SQLite primary store at `copilot_sdk/demo/bundle.py:49`, and then applies a cold-store guard: it counts existing decisions at `copilot_sdk/demo/bundle.py:50-56` and returns `False` without writing anything if `count_decisions(domain) >= min_decisions_to_skip`.

If restore proceeds, it inserts decisions at `copilot_sdk/demo/bundle.py:76-87`, outcomes at `copilot_sdk/demo/bundle.py:88-111`, and checkpoint rows into `centroid_checkpoints` at `copilot_sdk/demo/bundle.py:112-123`. It stores checkpoint centroids via `_checkpoint_values()` at `copilot_sdk/demo/bundle.py:287-305`, which writes `checkpoint.get("centroids")` into `centroids_json`.

`preseed_all_copilots.py` did not show direct `restore_bundle`, `demo_bundle`, or centroid-checkpoint writes in the targeted search. Its role is API/data preseed, not applying `demo/*_demo_bundle.json` into the checkpoint tables.

The propagation gap is the cold-store guard. The regenerated bundle has good centroids, but the existing app databases are not cold:

| Domain | Existing decisions | Existing checkpoints | Bundle `min_decisions_to_skip` | Restore result |
| --- | ---: | ---: | ---: | --- |
| Trading | 800 | 5 | 180 | skipped |
| Purchasing | 801 | 5 | 180 | skipped |

Because restore skips, regenerated bundle JSON never overwrites or supersedes the stale checkpoint rows.

## 3. Checkpoint analysis

Trading database: `apps/trading/backend/data/trading.db`.

- Tables include `centroid_checkpoints`, `l5_centroids`, `l5_dk_weights`, and `l5_conservation_state`.
- `centroid_checkpoints`: 5 rows.
- Latest checkpoint row: `(id=5, created_at=1700720000.0, checkpoint_time='2023-11-23T06:28:20Z', decision_id=None, category=None, action=None)`.
- Both first and latest checkpoint tensors have shape `(5, 4, 10)` and per-category action spread `[0.0, 0.0, 0.0, 0.0, 0.0]`; the stored checkpoints are fully collapsed within every category.
- `l5_centroids`: 6 rows, covering a sparse subset including `trend_following/strong_execution`, `trend_following/partial_execution`, `event_driven/strong_execution`, `mean_reversion/strong_execution`, `income_strategy/strong_execution`, and `scalp_intraday/strong_execution`.
- Export hashes differ (`pre_restore_hash=2e5b...`, `post_restore_hash=c672...`) and `l5_rows_applied=6/6`, so L5 is overlaying part of the collapsed checkpoint. The partial overlay explains why only some Trading categories/actions regain spread in `real_centroids_v1.json`.

Purchasing database: `apps/purchasing/backend/data/purchasing.db`.

- Tables include `centroid_checkpoints`, `l5_centroids`, `l5_dk_weights`, and `l5_conservation_state`.
- `centroid_checkpoints`: 5 rows.
- Latest checkpoint row: `(id=5, created_at=1700720000.0, checkpoint_time='2023-11-23T06:28:20Z', decision_id=None, category=None, action=None)`.
- Both first and latest checkpoint tensors have shape `(5, 4, 7)` and per-category action spread `[0.0, 0.0, 0.0, 0.0, 0.0]`; the stored checkpoints are fully collapsed within every category.
- `l5_centroids`: 0 rows.
- Export hashes are identical (`pre_restore_hash=78ac...`, `post_restore_hash=78ac...`) and `l5_rows_applied=0/0`, so nothing repairs the collapsed checkpoint. This explains why Purchasing remains fully collapsed in `real_centroids_v1.json`.

The checkpoint rows are the collapsed source. They win because `load_latest_centroids()` has no action-spread quality gate; it only validates that the row parses as a numeric tensor with `ndim > 0`.

## 4. Bootstrap prior analysis

The preset bootstrap files are separate from the demo bundles.

- `copilot_sdk/scoring/presets/trading.py:111-125` loads `copilot_sdk/scoring/presets/trading_bootstrap.json`. The file has shape `(5, 4, 10)` and differentiated action centroids.
- `copilot_sdk/scoring/presets/purchasing.py:93-109` loads `copilot_sdk/scoring/presets/purchasing_bootstrap.json`. The file has shape `(5, 4, 7)` and differentiated action centroids.
- Both presets have legacy migration branches (`trading.py:121-122`, `purchasing.py:103-104`), but the current JSON files already match the current expected shapes.

Measured preset/bootstrap spread:

| Domain | Bootstrap file | Shape | Per-category max action spread |
| --- | --- | --- | --- |
| Trading | `copilot_sdk/scoring/presets/trading_bootstrap.json` | `(5, 4, 10)` | `[0.316681, 0.355658, 0.374777, 0.304165, 0.337872]` |
| Purchasing | `copilot_sdk/scoring/presets/purchasing_bootstrap.json` | `(5, 4, 7)` | `[0.275437, 0.420332, 0.275757, 0.365821, 0.263886]` |

`from_preset(profile='test')` with no app database uses `InMemoryGraphStore`, finds no checkpoint, and returns those differentiated bootstrap tensors. Passing an empty `db_path` while still using `profile='test'` also returns bootstrap because `profile='test'` ignores the SQLite path and uses in-memory storage. Using `profile='development'` with an empty SQLite DB also returns the differentiated bootstrap, because the empty store has no checkpoint rows.

The regenerated demo bundles are also differentiated:

| Domain | Bundle checkpoint shape | Per-category max action spread |
| --- | --- | --- |
| Trading | `(5, 4, 10)` | `[0.6, 0.3557, 0.64, 0.4525, 0.6018]` |
| Purchasing | `(5, 4, 7)` | `[0.5562, 0.4495, 0.5049, 0.6018, 0.65]` |

Therefore the collapse is not in the preset bootstrap and not in the regenerated bundle. It persists only in the already-populated SQLite checkpoint rows.

## 5. Root cause

Purchasing is fully collapsed in the export because the export reads `apps/purchasing/backend/data/purchasing.db`, that database has five fully collapsed `centroid_checkpoints` rows, and there are no `l5_centroids` rows to overlay. The scorer source order is checkpoint first, bootstrap second. Since a checkpoint exists and has the right factor hash/shape, it wins over the differentiated preset. Since the database already has 801 decisions and the bundle skip threshold is 180, app startup does not restore the regenerated bundle into the database.

Trading is partially collapsed in the export for the same checkpoint reason, with one additional repair step. Its `centroid_checkpoints` rows are also fully collapsed. Unlike Purchasing, Trading has six L5 centroid rows. The export applies those rows after checkpoint load, so categories touched by L5 regain some action spread while untouched categories remain collapsed. This is why Trading is partially collapsed rather than fully collapsed.

The answer to the source-precedence question is:

1. Existing SQLite checkpoint wins if present and schema-compatible.
2. L5 overlay wins only for specific `(category, action)` cells present in `l5_centroids`.
3. Preset bootstrap wins only when no usable checkpoint is returned or the checkpoint is rejected by factor-name hash mismatch.
4. Demo bundle wins only indirectly, when startup restore writes bundle checkpoint rows into SQLite. It is skipped for warm stores once `count_decisions(domain) >= min_decisions_to_skip`.

Regenerating `demo/*_demo_bundle.json` alone does not change runtime/export state because neither `from_preset()` nor `extract_real_centroids.py` reads bundle JSON directly, and app startup refuses to restore the bundle into these non-cold databases.

## 6. Recommended fix

Recommended fix: **D) Add a centroid-checkpoint refresh path for demo bundles, with a collapse quality gate.**

The minimal runtime/export fix is to remove or supersede stale collapsed checkpoint rows so the scorer can either fall back to the already differentiated bootstrap priors or load a newly written differentiated bundle checkpoint. However, simply deleting `centroid_checkpoints` rows does not actually propagate regenerated bundle geometry, because the bundle restore guard is based on decision count and would still skip with 800/801 existing decisions. It would fix collapse by falling back to preset bootstrap, but it would not make bundle regeneration the source of truth.

A durable fix should add an explicit centroid refresh operation separate from full bundle restore:

1. Read `demo/{domain}_demo_bundle.json`.
2. Extract the latest `centroid_checkpoints[*].centroids` tensor.
3. Validate shape equals the preset tensor shape and factor names match the domain preset.
4. Compute per-category action spread; if any category has max action spread `<= 0.01`, reject the bundle checkpoint.
5. Inspect the latest SQLite checkpoint. If it is collapsed or older than the regenerated bundle checkpoint, write a new V2 checkpoint row with the bundle tensor and a fresh `created_at`/`checkpoint_time`, or delete only the stale collapsed checkpoint rows before writing the new row.
6. Leave decisions, outcomes, RL state, L5 state, and evidence fixtures untouched.
7. Let the existing scorer path continue unchanged: `from_preset()` loads the latest SQLite checkpoint, then startup/export L5 overlay applies on top.

Suggested files for an implementation follow-up:

- Add a script such as `scripts/refresh_demo_centroid_checkpoints.py`, or extend `copilot_sdk/demo/bundle.py` with a centroid-only refresh function. This is not a scorer change.
- Add tests that create a warm SQLite store with collapsed checkpoints and `count_decisions >= min_decisions_to_skip`, run the refresh, and assert that `load_latest_centroids()` returns a differentiated tensor.
- Keep `CompoundingScorer.from_preset()` unchanged. Its current precedence is correct for learned runtime state; the problem is stale bad checkpoint data without a quality gate.

Blast radius:

- No production scoring logic needs to change.
- No preset bootstrap update is needed for Trading or Purchasing; both are already differentiated.
- No export-path workaround should be used as the primary fix. Making `extract_real_centroids.py` read bundle JSON would mask the real runtime state and diverge from app startup behavior.
- Database mutation is required only in an authorized follow-up migration/refresh step. This diagnosis did not modify database files.
