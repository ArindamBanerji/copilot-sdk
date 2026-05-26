# Bootstrap Shape Diagnostic — Trading + Purchasing
**Generated:** 2026-05-25 · **Repo:** copilot-sdk

## Executive Summary
- Current status: Trading and Purchasing bootstrap JSON files still store legacy centroid arrays on disk, but the current preset loaders contain explicit in-memory migration paths for those known legacy shapes. Trading JSON is `(5,3,6)` while the preset is `(5,4,7)`. Purchasing JSON is `(5,4,6)` while the preset is `(5,4,7)`. DataOps JSON matches `(6,5,6)`.
- P1 risk: App-local DB checkpoint files are stale. `apps/trading/backend/data/trading.db` latest checkpoint is `(5,3,6)` and `apps/purchasing/backend/data/purchasing.db` latest checkpoint is `(5,4,6)`. `CompoundingScorer.from_preset()` loads DB centroids before bootstrap at `copilot_sdk/scoring/scorer.py:147-149`, so stale DB checkpoints can override the migrated bootstrap and trigger shape errors before the preset fallback/migration is used.
- Recommended next step: Regenerate Trading and Purchasing bootstrap JSONs to canonical `(5,4,7)`, fix or bypass the current calibration scripts if used, and delete/regenerate stale app-local Trading DB per Standing Rule #46. Purchasing also needs stale centroid checkpoint remediation, most simply by deleting/regenerating `apps/purchasing/backend/data/purchasing.db` or clearing its centroid checkpoints during a controlled local reset.

## Shape Status Table
| Bootstrap File | Expected Shape | Actual Shape | Metadata Names Present | File Size | Status |
|---|---:|---:|---|---:|---|
| `copilot_sdk/scoring/presets/trading_bootstrap.json` | `(5,4,7)` | `(5,3,6)` | No `category_names`, `action_names`, or `factor_names`; metadata has `shape: [5, 3, 6]` | 3193 | FAIL on-disk shape; loader migrates known legacy shape |
| `copilot_sdk/scoring/presets/purchasing_bootstrap.json` | `(5,4,7)` | `(5,4,6)` | No `category_names`, `action_names`, or `factor_names`; metadata has `shape: [5, 4, 6]` | 4152 | FAIL on-disk shape; loader migrates known legacy shape |
| `copilot_sdk/scoring/presets/dataops_bootstrap.json` | `(6,5,6)` | `(6,5,6)` | No `category_names`, `action_names`, or `factor_names`; metadata has `shape: [6, 5, 6]` | 5805 | PASS |

## Preset Shape Definitions
### Trading
- Preset registry includes `"trading": TradingPreset` at `copilot_sdk/scoring/presets/__init__.py:8-12`.
- Shape is defined in `copilot_sdk/scoring/presets/trading.py:24-46` as 5 categories, 4 actions, and 7 factors.
- Categories: `trend_following`, `mean_reversion`, `event_driven`, `income_strategy`, `scalp_intraday` at `trading.py:29-35`.
- Actions: `strong_execution`, `partial_execution`, `poor_execution`, `skip_recommended` at `trading.py:36`.
- Factors: `signal_alignment`, `market_regime`, `position_sizing`, `timing_quality`, `risk_reward_actual`, `emotional_indicator`, `signal_confidence` at `trading.py:37-45`.
- `penalty_ratio` is `3.0` at `trading.py:48-51`.
- Bootstrap loader: `bootstrap_centroids` delegates to `_load_bootstrap()` at `trading.py:80-82`.
- `_load_bootstrap()` reads `trading_bootstrap.json`, computes `expected_shape = preset.shape.tensor_shape`, and reads `data["centroids"]` at `trading.py:85-90`.
- Known legacy migration: if centroids are `(5,3,6)` and expected is `(5,4,7)`, it returns `_migrate_legacy_centroids()` at `trading.py:91-92`.
- Other shape mismatch behavior: raises `ValueError` at `trading.py:93-94`, then the broad `except Exception` returns neutral `np.full(expected_shape, 0.5)` at `trading.py:96-97`.
- Warning/log behavior: no warning or logging is emitted in `_load_bootstrap()`; migration and fallback are silent.
- Migration details: `_migrate_legacy_centroids()` creates `(5,4,7)` full neutral base at `trading.py:100-102`, copies old values to first 3 actions and 6 factors, fills the 7th `signal_confidence` for existing actions from `_LEGACY_ACTION_CONFIDENCE = (0.65, 0.55, 0.50)` at `trading.py:14` and `trading.py:103-104`, and initializes `skip_recommended` with `_NEUTRAL_SKIP_CENTROID` from `trading.py:15` and `trading.py:105-107`.

### Purchasing
- Preset registry includes `"purchasing": PurchasingPreset` at `copilot_sdk/scoring/presets/__init__.py:8-12`.
- Shape is defined in `copilot_sdk/scoring/presets/purchasing.py:20-49` as 5 categories, 4 actions, and 7 factors.
- Categories: `protein`, `produce`, `dairy`, `dry_goods`, `beverages` at `purchasing.py:25-31`.
- Actions: `order_as_planned`, `order_more`, `order_less`, `skip` at `purchasing.py:32-37`.
- Factors: `expected_demand`, `day_of_week`, `weather_forecast`, `event_flag`, `historical_waste`, `supplier_lead_time`, `price_memory_index` at `purchasing.py:38-48`.
- `penalty_ratio` is `3.0` at `purchasing.py:51-53`.
- `price_memory_index` guidance is embedded in comments at `purchasing.py:45-46`: historical price tracking per supplier x category; high means within learned norms, low means anomalous spike or hidden discount.
- Bootstrap loader: `bootstrap_centroids` delegates to `_load_bootstrap()` at `purchasing.py:76-78`.
- Known legacy migration: if centroids are `(5,4,6)` and expected is `(5,4,7)`, it returns `_migrate_legacy_centroids()` at `purchasing.py:87-88`.
- Other shape mismatch behavior: raises `ValueError` at `purchasing.py:89-92`, then the broad `except Exception` returns neutral `np.full(expected_shape, 0.5)` at `purchasing.py:94-95`.
- Warning/log behavior: no warning or logging is emitted in `_load_bootstrap()`; migration and fallback are silent.
- Migration details: `_migrate_legacy_centroids()` creates `(5,4,7)` full neutral base, copies old 6 factors, and initializes the 7th `price_memory_index` to `0.5` at `purchasing.py:98-102`.

### DataOps
- Preset registry includes `"dataops": DataOpsPreset` at `copilot_sdk/scoring/presets/__init__.py:8-12`.
- Shape is defined in `copilot_sdk/scoring/presets/dataops.py:20-48` as 6 categories, 5 actions, and 6 factors.
- Categories: `schema_change`, `volume_anomaly`, `quality_anomaly`, `freshness_violation`, `pipeline_failure`, `transform_drift` at `dataops.py:25-32`.
- Actions: `auto_approve`, `investigate`, `escalate_to_owner`, `pause_downstream`, `refer_to_specialist` at `dataops.py:33-39`.
- Factors: `impact_scope`, `source_reliability`, `recurrence_frequency`, `downstream_urgency`, `data_freshness`, `business_criticality` at `dataops.py:40-47`.
- `penalty_ratio` is `10.0` at `dataops.py:50-52`.
- Loader reads `dataops_bootstrap.json` at `dataops.py:80-85`, validates exact shape at `dataops.py:86-87`, returns centroids at `dataops.py:88`, and silently falls back to neutral `np.full(expected_shape, 0.5)` at `dataops.py:89-90`.
- Current DataOps bootstrap JSON shape matches the preset, so no DataOps bootstrap action is required.

## Bootstrap Loading Order
- Function path: `CompoundingScorer.from_preset(domain, db_path=None, graph_store=None, ...)` in `copilot_sdk/scoring/scorer.py:120-131`.
- Exact sequence:
  1. Validates the domain is in `PRESET_REGISTRY` at `scorer.py:132-134`.
  2. Instantiates the preset at `scorer.py:136-137`.
  3. If no DB path is supplied, creates `copilot_sdk/data/{domain}.db` at `scorer.py:138-141`.
  4. If no graph store is supplied, creates `SQLiteGraphStore(db_path, domain=preset.name)` at `scorer.py:143-146`.
  5. Calls `graph_store.load_latest_centroids(preset.name)` first at `scorer.py:147`.
  6. Only if no checkpoint exists does it load `preset.bootstrap_centroids` at `scorer.py:148-149`.
  7. Instantiates `ProfileScorer(mu=centroids, actions=..., categories=...)` at `scorer.py:151-155`.
- Fallback behavior: Preset fallback/migration only executes when `load_latest_centroids()` returns `None`. If a stale DB checkpoint exists, bootstrap JSON and preset migration are bypassed.
- Warning/log behavior: preset shape mismatches are caught silently. DB checkpoint shape is not validated in `from_preset()` before `ProfileScorer` construction.
- DB interaction: SQLite checkpoint schema stores raw `centroids_json` at `copilot_sdk/graph/sqlite_store.py:89-102`; `load_latest_centroids()` selects latest checkpoint by domain and returns it as a NumPy array at `sqlite_store.py:459-470`.

## Impact Assessment
### Trading
- On-disk bootstrap JSON is legacy `(5,3,6)` with metadata `shape: [5,3,6]`.
- If no DB checkpoint exists, `TradingPreset().bootstrap_centroids` currently migrates to `(5,4,7)` and produced values bounded in `[0.25, 0.7056833066029353]` in the diagnostic run.
- If `apps/trading/backend/data/trading.db` is used, latest `centroid_checkpoints` rows are stale `(5,3,6)`: ids 111, 110, 109 all had category `equity_long` and shape `(5,3,6)`.
- Trading app uses the app-local DB path through `_resolve_scoring_db()` and passes `scoring_db` into `create_scoring_router()` at `apps/trading/backend/app/main.py:230-240`, so stale app-local checkpoints are operationally relevant.
- This is the likely root of the observed health error `mu.shape[1]=3 must equal len(actions)=4`.

### Purchasing
- On-disk bootstrap JSON is legacy `(5,4,6)` with metadata `shape: [5,4,6]`.
- If no DB checkpoint exists, `PurchasingPreset().bootstrap_centroids` currently migrates to `(5,4,7)` and initializes the whole 7th factor plane to `0.5`.
- If `apps/purchasing/backend/data/purchasing.db` is used, latest `centroid_checkpoints` rows are stale `(5,4,6)`: ids 106, 105, 104 all had category `protein` and shape `(5,4,6)`.
- Purchasing app uses the app-local DB path through `_resolve_scoring_db()` and passes `scoring_db` into `create_scoring_router()` at `apps/purchasing/backend/app/main.py:268-278`, so stale app-local checkpoints are operationally relevant.

### DataOps
- On-disk bootstrap JSON matches `(6,5,6)`.
- App-local `apps/dataops/backend/data/dataops.db` latest checkpoint rows are `(6,5,6)`, so no shape mismatch was found.
- `copilot_sdk/data/dataops.db` exists but appears to have an older schema without a `domain` column in `centroid_checkpoints`; it is not the DataOps app-local DB used by `apps/dataops/backend/app/main.py:237-247`.

## Trading New Mapping
- categories: `trend_following`, `mean_reversion`, `event_driven`, `income_strategy`, `scalp_intraday`.
- actions: `strong_execution`, `partial_execution`, `poor_execution`, `skip_recommended`.
- factors: `signal_alignment`, `market_regime`, `position_sizing`, `timing_quality`, `risk_reward_actual`, `emotional_indicator`, `signal_confidence`.
- bootstrap implications:
  - Standing Rule #48 is honored in the preset: actions are execution-quality actions, not directional buy/hold/sell.
  - The current legacy migration treats the old three actions as the first three execution-quality actions and appends a `skip_recommended` centroid.
  - The migration does not regenerate expert-calibrated values for the new action/factor from source data; it fills `signal_confidence` by action with `(0.65, 0.55, 0.50)` and uses the conservative skip vector `(0.30, 0.35, 0.50, 0.50, 0.50, 0.25, 0.40)`.
  - The current JSON file should still be regenerated to persist canonical shape metadata and avoid relying on silent runtime migration.

## Purchasing 7th Factor
- factor: `price_memory_index`.
- description: `purchasing.py:45-46` says it tracks historical price per supplier x category; high means within learned norms, low means anomalous spike or hidden discount.
- initialization recommendation:
  - Current preset migration initializes `price_memory_index` to neutral `0.5` for every category/action cell at `purchasing.py:98-102`.
  - `apps/purchasing/backend/tests/test_purchasing_config_migration.py:133-134` actively asserts `PurchasingPreset().bootstrap_centroids[:, :, 6] == 0.50`.
  - Unless a future calibration script is updated to use seed data containing price memory guidance, neutral `0.5` is the implementation-ready value for the new 7th factor column.

## DB File Interaction
- data directory: `copilot_sdk/data` exists and contains `copilot_sdk/data/dataops.db` only.
- trading.db:
  - App-local file exists at `apps/trading/backend/data/trading.db`, size 593920 bytes.
  - Latest three Trading checkpoint shapes are `(5,3,6)`.
  - Per Standing Rule #46, delete/regenerate `apps/trading/backend/data/trading.db` after Trading preset shape change. Do not migrate it.
- purchasing.db:
  - App-local file exists at `apps/purchasing/backend/data/purchasing.db`, size 876544 bytes.
  - Latest three Purchasing checkpoint shapes are `(5,4,6)`.
  - No standing rule was provided for Purchasing, but the same operational issue exists: DB-first loading bypasses bootstrap migration. Recommended local fix is to delete/regenerate `apps/purchasing/backend/data/purchasing.db` or explicitly clear stale centroid checkpoints under a controlled reset.
- stale checkpoint behavior:
  - `load_latest_centroids()` returns whatever JSON array is stored in the latest checkpoint without checking expected domain shape at `sqlite_store.py:459-470`.
  - `ProfileScorer` receives that array with the current action/category names at `scorer.py:151-155`, so stale checkpoint dimensions can fail during scorer initialization.
- deletion/regeneration recommendation:
  - Trading: delete app-local `trading.db` after regenerating bootstrap JSON and before restart.
  - Purchasing: regenerate/reset app-local `purchasing.db` or clear stale checkpoints before restart.
  - DataOps: no deletion needed for app-local `dataops.db`.

## Preseed Compatibility
- script path: `scripts/preseed_all_copilots.py`.
- Trading:
  - `TRADING_FACTORS` includes `signal_confidence` and comments that existing seeds omit the seventh factor so `extract_factors` defaults it to neutral `0.50` at `scripts/preseed_all_copilots.py:25-34`.
  - Trading domain config still lists only three alternate actions at `scripts/preseed_all_copilots.py:88-96`; this does not prevent scoring with `skip_recommended`, but override alternates are selected only from the three-action list.
  - Score requests are sent to `/api/score` with category/factors/context at `scripts/preseed_all_copilots.py:368-378`.
- Purchasing:
  - `PURCHASING_FACTORS` includes `price_memory_index` and comments that existing seeds omit the seventh factor so `extract_factors` defaults it to neutral `0.50` at `scripts/preseed_all_copilots.py:36-45`.
  - Purchasing domain config includes all four Purchasing actions at `scripts/preseed_all_copilots.py:98-106`.
  - `extract_factors()` reads nested seed factors or entry fields and passes missing/invalid values through `coerce_factor()` at `scripts/preseed_all_copilots.py:229-249`; missing seventh factors become `0.5`.
- required updates:
  - Trading preseed should consider adding `skip_recommended` to `DomainConfig.actions` if override simulation should exercise the full action space.
  - Preseed does not need a hard update to include the seventh factors because both are already included and default to neutral when omitted from seed files.

## Shape-Dependent Test Impact
| File | Line | Old Shape Reference | Active Assertion? | Action |
|---|---:|---|---|---|
| `copilot_sdk/scoring/presets/trading.py` | 91 | Checks legacy `(5,3,6)` for runtime migration | Active compatibility path | Keep until JSON regeneration and compatibility policy are decided. |
| `copilot_sdk/scoring/presets/purchasing.py` | 87 | Checks legacy `(5,4,6)` for runtime migration | Active compatibility path | Keep until JSON regeneration and compatibility policy are decided. |
| `tests/scoring/test_trading_preset.py` | 34 | `EXISTING_ACTIONS` is first three actions | Active compatibility assertion | Keep; validates appended `skip_recommended` without old tensor shape. |
| `tests/scoring/test_trading_preset.py` | 145-146 | Asserts migrated bootstrap shape `(5,4,7)` | Active assertion | Keep; should still pass after JSON regeneration. |
| `apps/trading/backend/tests/test_trading_config_migration.py` | 83-91 | Asserts 20 cells and 7D centroids | Active assertion | Keep; should still pass after JSON regeneration. |
| `apps/trading/backend/tests/test_trading_config_migration.py` | 109-114 | Asserts old cells get `signal_confidence` values | Active migration assertion | May need update if regeneration produces non-migration calibrated signal confidence values. |
| `apps/purchasing/backend/tests/test_purchasing_config_migration.py` | 119-134 | Asserts `(5,4,7)` and neutral 7th factor | Active assertion | Keep if regeneration continues neutral `price_memory_index`; update only if calibrated guidance changes. |
| `apps/purchasing/backend/tests/test_purchasing_config_migration.py` | 137-145 | Asserts legacy sample first six values unchanged | Active migration assertion | May need update if regenerated JSON changes first six values. |
| `tests/scoring/test_dataops_preset.py` | 140-141 | Asserts DataOps `(6,5,6)` | Active assertion | No action. |

## Trading Factor Registry Fallback
- fallback names: `apps/trading/backend/app/factors/registry.py:21-29` hardcodes the same seven names as `TradingPreset().shape.factor_names`.
- match status: PASS. Primary path imports `TradingPreset` and assigns `ALL_FACTOR_NAMES = tuple(TradingPreset().shape.factor_names)` at `registry.py:16-19`; fallback list also includes `signal_confidence`.
- impact: If `TradingPreset` import fails, `compute_factors()` still returns all seven expected core factor names with neutral defaults and factor computer outputs at `registry.py:43-50`.
- exact fix if needed: No fix needed. Leave registry unchanged.

## Bootstrap Regeneration Path
- existing generator: `support/scripts/calibrate_trading_bootstrap.py`, `support/scripts/calibrate_purchasing_bootstrap.py`, and `support/scripts/calibrate_dataops_bootstrap.py` exist.
- generator caveats:
  - The calibration scripts read seeds from `REPO_ROOT / "copilot_sdk.scoring" / "presets" / "..._seed.json"` at `calibrate_trading_bootstrap.py:28-30`, `calibrate_purchasing_bootstrap.py:28-30`, and `calibrate_dataops_bootstrap.py:28-30`. That dotted directory path does not match the actual `copilot_sdk/scoring/presets` path.
  - The scripts write output to the same dotted path at `calibrate_trading_bootstrap.py:109-112`, `calibrate_purchasing_bootstrap.py:119-122`, and `calibrate_dataops_bootstrap.py:119-122`.
  - Trading/Purchasing calibration reads `[... for name in shape.factor_names]` at `calibrate_trading_bootstrap.py:40` and `calibrate_purchasing_bootstrap.py:40-42`; the existing preset seed JSONs omit `signal_confidence` and `price_memory_index`, so the scripts need neutral default handling before they can run on current shape.
- if none, required generator design:
  - Inputs: preset class, seed JSON, categories/actions/factors from `preset.shape`, and domain heuristics for new factors/actions.
  - Output JSON structure: object with `centroids`, `shape`, `mean_confidence`, `noise_scale`, `seed`, `pool_size`, and domain count fields; optionally add `category_names`, `action_names`, and `factor_names` if loaders are later updated to tolerate metadata names.
  - Shape validation: assert `np.asarray(payload["centroids"]).shape == preset.shape.tensor_shape`.
  - Values bounded: assert all centroid values are between `0.0` and `1.0`.
  - Metadata names: current loaders ignore metadata names and only read `data["centroids"]`; adding metadata names is safe for current loaders because unknown keys are ignored, but tests should assert the names if added.
- Fix Plan:
  1. Update calibration scripts or write a one-off local regeneration script that uses the real path `copilot_sdk/scoring/presets`.
  2. For Trading, either materialize the current runtime migration (`TradingPreset().bootstrap_centroids`) to JSON shape `(5,4,7)` or recalibrate from seed data with neutral `signal_confidence=0.5` for missing seed values and the existing skip centroid heuristic.
  3. For Purchasing, materialize the current runtime migration (`PurchasingPreset().bootstrap_centroids`) to JSON shape `(5,4,7)` or recalibrate from seed data with `price_memory_index=0.5` for missing preset seed values.
  4. Do not change DataOps bootstrap unless the DataOps generator path is being fixed opportunistically.
  5. Delete `apps/trading/backend/data/trading.db` after Trading bootstrap/preset shape work, per Standing Rule #46.
  6. Reset `apps/purchasing/backend/data/purchasing.db` or clear stale Purchasing centroid checkpoints because current latest checkpoint shape is `(5,4,6)` and DB-first load bypasses bootstrap migration.
  7. Restart app servers and verify health endpoints.
- validation commands:
  - `python -c "import json, numpy as np; from pathlib import Path; from copilot_sdk.scoring.presets.trading import TradingPreset; from copilot_sdk.scoring.presets.purchasing import PurchasingPreset; checks=[('copilot_sdk/scoring/presets/trading_bootstrap.json', TradingPreset()), ('copilot_sdk/scoring/presets/purchasing_bootstrap.json', PurchasingPreset())]; [print(path, np.asarray(json.load(open(path, encoding='utf-8'))['centroids']).shape, preset.shape.tensor_shape) for path,preset in checks]"`
  - `python -c "from copilot_sdk.scoring.presets.trading import TradingPreset; from copilot_sdk.scoring.presets.purchasing import PurchasingPreset; print(TradingPreset().bootstrap_centroids.shape); print(PurchasingPreset().bootstrap_centroids.shape)"`
  - `python -c "from copilot_sdk.scoring import CompoundingScorer; s=CompoundingScorer.from_preset('trading', db_path='apps/trading/backend/data/trading.db'); print(s.gae_scorer.centroids.shape); s.graph_store.close()"`
  - `python -c "from copilot_sdk.scoring import CompoundingScorer; s=CompoundingScorer.from_preset('purchasing', db_path='apps/purchasing/backend/data/purchasing.db'); print(s.gae_scorer.centroids.shape); s.graph_store.close()"`
- post-fix test commands:
  - `python -m pytest tests/scoring/test_trading_preset.py -q --timeout=120`
  - `python -m pytest apps/trading/backend/tests/test_trading_config_migration.py -q --timeout=120`
  - `python -m pytest apps/trading/backend/tests/ -q --timeout=120`
  - `python -m pytest apps/purchasing/backend/tests/test_purchasing_config_migration.py -q --timeout=120`
  - `python -m pytest apps/purchasing/backend/tests/ -q --timeout=120`
  - `python -m pytest tests/ -q --timeout=120`

## Implementation Prompt Guidance
- files to modify:
  - `copilot_sdk/scoring/presets/trading_bootstrap.json`
  - `copilot_sdk/scoring/presets/purchasing_bootstrap.json`
  - optionally `support/scripts/calibrate_trading_bootstrap.py`
  - optionally `support/scripts/calibrate_purchasing_bootstrap.py`
  - tests that assert specific legacy migration sample values if regenerated centroids differ.
- files not to modify:
  - `copilot_sdk/scoring/presets/trading.py` unless deciding to remove or log migration/fallback behavior.
  - `copilot_sdk/scoring/presets/purchasing.py` unless deciding to remove or log migration/fallback behavior.
  - `copilot_sdk/scoring/scorer.py` unless adding DB checkpoint shape validation in a separate safety hardening task.
  - Trading factor registry; it already matches the new factor list.
- DB files to delete:
  - Delete `apps/trading/backend/data/trading.db` locally after Trading preset/bootstrap shape change, per Standing Rule #46.
  - Reset/delete `apps/purchasing/backend/data/purchasing.db` or clear stale Purchasing centroid checkpoints during local remediation.
  - Do not delete `apps/dataops/backend/data/dataops.db` for this issue.
- tests to run:
  - Preset tests, Trading/Purchasing config migration tests, full Trading backend, full Purchasing backend, and root tests.
- risks:
  - Regenerating JSON from current runtime migration preserves compatibility but not necessarily a newly calibrated expert prior.
  - Running the existing support calibration scripts as-is may write to `copilot_sdk.scoring/...` instead of `copilot_sdk/scoring/...`.
  - App-local stale DB checkpoints can mask correct bootstrap JSON until DBs are reset.

## Blockers
- Existing app-local Trading and Purchasing DB checkpoint shapes are stale and must be remediated before health/startup can be considered stable.
- Existing calibration scripts need path correction and missing-factor default handling before they can be trusted for direct regeneration.
