# SDK Evolution Plateau Tuning Plan

## 1. Executive Summary

Classification: `BLOCKED_NO_RELIABLE_EVENT_DATA`.

The current SDK preset premise is true: the SDK registry exposes `dataops`, `purchasing`, `s2p`, and `trading` presets, and each preset currently returns a default `PlateauConfig()` instead of copilot-specific values. Evidence: `copilot_sdk/scoring/presets/__init__.py:8-13`, `copilot_sdk/scoring/presets/trading.py:59-61`, `copilot_sdk/scoring/presets/purchasing.py:64-66`, `copilot_sdk/scoring/presets/dataops.py:66-68`, and `copilot_sdk/scoring/presets/s2p.py:63-65`.

The requested data-driven tuning cannot be completed from the current persisted SQLite files. Existing app DBs have decisions, verified outcomes, and centroid checkpoints, but no `evolution_events` table:

| DB | decisions | verified outcomes | centroid checkpoints | evolution events |
| --- | ---: | ---: | ---: | --- |
| `apps/trading/backend/data/trading.db` | 358 | 111 | 111 | table missing |
| `apps/purchasing/backend/data/purchasing.db` | 342 | 106 | 106 | table missing |
| `apps/dataops/backend/data/dataops.db` | 289 | 200 | 201 | table missing |

This matters because SQLite evolution events are persisted only through `SQLiteGraphStore.save_evolution_event()`, which creates and inserts into `evolution_events`; see `copilot_sdk/graph/sqlite_store.py:164-198`. Without that table in the app DBs, event-per-decision and event-per-verified-decision ratios are not measurable from existing preseed/generated DBs.

The repo provides generation paths, but they are not sufficient evidence for immediate tuning. `scripts/preseed_all_copilots.py` seeds Trading, Purchasing, and DataOps through running backend APIs, not direct offline DB generation; see `scripts/preseed_all_copilots.py:1-5`, `scripts/preseed_all_copilots.py:83-120`, and `scripts/preseed_all_copilots.py:357-413`. `scripts/evolve_demo.py` is a local synthetic evolution demo that prints `event_count`; see `scripts/evolve_demo.py:43-71`. It can help collect future comparable data, but its synthetic factor generation should not be used as observed preseed event frequency without an explicit validation run design.

Recommendation: do not tune `PlateauConfig` yet. First collect reliable evolution-event data through an agreed canonical run, then tune presets with measured ratios.

## 2. Current PlateauConfig Definition

`PlateauConfig` is defined as a frozen dataclass with:

| field | current default | evidence |
| --- | ---: | --- |
| `plateau_window` | 10 | `copilot_sdk/evolution/evolver.py:16-18` |
| `min_improvement_rate` | 0.2 | `copilot_sdk/evolution/evolver.py:18-20` |
| `plateau_cooldown` | 50 | `copilot_sdk/evolution/evolver.py:18-20` |

It is enabled only when `plateau_window > 0` and `min_improvement_rate > 0`; see `copilot_sdk/evolution/evolver.py:22-24`.

`AgentEvolver` receives the provided plateau config or falls back to `PlateauConfig()`; see `copilot_sdk/evolution/evolver.py:33-38`.

## 3. Current Preset Values

The SDK preset registry contains four presets: `dataops`, `purchasing`, `s2p`, and `trading`; see `copilot_sdk/scoring/presets/__init__.py:8-13`.

All four presets return `PlateauConfig()` with no overrides:

| preset | current config evidence | effective values |
| --- | --- | --- |
| trading | `copilot_sdk/scoring/presets/trading.py:59-61` | window 10, min rate 0.2, cooldown 50 |
| purchasing | `copilot_sdk/scoring/presets/purchasing.py:64-66` | window 10, min rate 0.2, cooldown 50 |
| dataops | `copilot_sdk/scoring/presets/dataops.py:66-68` | window 10, min rate 0.2, cooldown 50 |
| s2p | `copilot_sdk/scoring/presets/s2p.py:63-65` | window 10, min rate 0.2, cooldown 50 |

`tests/test_plateau_preset_config.py` currently asserts these identical defaults across the registry; see `tests/test_plateau_preset_config.py:11-20`.

## 4. Copilot Tensor/Event Volume Evidence

### Tensor Shapes

| preset | categories | actions | factors | tensor size | evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| trading | 5 | 3 | 6 | 90 | `copilot_sdk/scoring/presets/trading.py:20-41`; `copilot_sdk/scoring/config.py:36-38` |
| purchasing | 5 | 4 | 6 | 120 | `copilot_sdk/scoring/presets/purchasing.py:20-46`; `copilot_sdk/scoring/config.py:36-38` |
| dataops | 6 | 5 | 6 | 180 | `copilot_sdk/scoring/presets/dataops.py:20-48`; `copilot_sdk/scoring/config.py:36-38` |
| s2p | 5 | 5 | 7 | 175 | `copilot_sdk/scoring/presets/s2p.py:17-45`; `copilot_sdk/scoring/config.py:36-38` |

S2P is an SDK-side preset, not only an external repo reference, because `S2PPreset` is registered in the SDK preset registry; see `copilot_sdk/scoring/presets/s2p.py:11-15` and `copilot_sdk/scoring/presets/__init__.py:8-13`.

The optional external S2P reference exists separately and uses the same high-level tensor dimensions `(5, 5, 7)`; see `../s2p-copilot/backend/app/domains/s2p/config.py:1-5` and `../s2p-copilot/backend/app/domains/s2p/config.py:64-67`.

### Persisted Event Volume

Measured from current SQLite DBs:

| copilot | measured decisions | measured verified decisions | measured evolution events | event ratio | event / verified ratio |
| --- | ---: | ---: | ---: | --- | --- |
| trading | 358 | 111 | unavailable: `evolution_events` table missing | unavailable | unavailable |
| purchasing | 342 | 106 | unavailable: `evolution_events` table missing | unavailable | unavailable |
| dataops | 289 | 200 | unavailable: `evolution_events` table missing | unavailable | unavailable |
| s2p | no SDK app DB found | no SDK app DB found | unavailable | unavailable | unavailable |

The app data directories do contain app-local DBs for trading, purchasing, and dataops. They also contain fixture/seed JSON files, but those JSON files are not persisted evolution-event ledgers. Evidence: the preseed script defines Trading, Purchasing, and DataOps seed paths at `scripts/preseed_all_copilots.py:83-120`; DataOps and Purchasing have `evolution_fixtures.json` under app data, but those are backend fixture files rather than `evolution_events` rows.

## 5. Plateau Detection Semantics

`CompoundingScorer` passes the preset plateau config into `AgentEvolver` during setup; see `copilot_sdk/scoring/scorer.py:561-567`.

Evolution runs only after at least 10 verified decisions are available; see `copilot_sdk/scoring/scorer.py:573-579`.

Plateau detection uses only improvement-bearing events from the ledger:

1. If the config is disabled, `_plateau_result()` returns `None`; see `copilot_sdk/evolution/evolver.py:151-153`.
2. If a cooldown is active, the cooldown is decremented and evolution is skipped; see `copilot_sdk/evolution/evolver.py:155-163`.
3. If fewer improvement events exist than `plateau_window`, no plateau is detected; see `copilot_sdk/evolution/evolver.py:165-167`.
4. The most recent `plateau_window` improvement events are selected; see `copilot_sdk/evolution/evolver.py:171`.
5. `positive_count / len(recent_events)` is compared to `min_improvement_rate`; if the rate is at or above the threshold, no plateau is detected; see `copilot_sdk/evolution/evolver.py:172-175`.
6. If the rate is below threshold, `plateau_detected` is recorded with config metadata and cooldown is set; see `copilot_sdk/evolution/evolver.py:177-193`.

Improvement events are derived from event metadata keys such as `gain`, `improvement`, `gain_pp`, `improvement_pp`, and `superiority_pp`; see `copilot_sdk/evolution/evolver.py:215-230`.

The tests cover detection, non-detection, cooldown behavior, config defaults, and event logging; see `tests/evolution/test_plateau.py:79-157`.

## 6. Design Options

### Option A: Tune immediately from current DB counts

Rejected. The current DBs do not contain `evolution_events`, so there is no measured evolution-event frequency to justify per-copilot threshold differences.

### Option B: Tune from tensor sizes only

Rejected. Tensor size differences are real, but the requested tuning criterion is observed preseed evolution-event frequency. Tensor size alone does not prove event cadence.

### Option C: Generate comparable event data first, then tune

Recommended. Use an agreed canonical run to produce and persist evolution-event data for Trading, Purchasing, and DataOps, and optionally SDK-side S2P if an app/runtime path is added. Then derive `plateau_window`, `min_improvement_rate`, and `plateau_cooldown` from the measured event ratios.

Candidate collection paths:

- API preseed path: `scripts/preseed_all_copilots.py` seeds 200 decisions per selected copilot through running backends; see `scripts/preseed_all_copilots.py:22`, `scripts/preseed_all_copilots.py:299-340`, and `scripts/preseed_all_copilots.py:357-413`.
- Local synthetic path: `scripts/evolve_demo.py` runs `CompoundingScorer.from_preset(... evolve=True)` and prints history event count; see `scripts/evolve_demo.py:43-71`.

Use the API preseed path for observed app data. Use the local synthetic path only as a secondary smoke test unless explicitly accepted as the measurement source.

## 7. Recommended Tuning Table

No tuning values are recommended yet because measured evolution-event ratios are unavailable.

| copilot | measured decisions | measured verified decisions | measured evolution events | event ratio | proposed window | proposed rate_threshold | proposed cooldown | rationale |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| trading | 358 | 111 | unavailable | unavailable | no change | no change | no change | Current DB lacks `evolution_events`; do not guess. |
| purchasing | 342 | 106 | unavailable | unavailable | no change | no change | no change | Current DB lacks `evolution_events`; do not guess. |
| dataops | 289 | 200 | unavailable | unavailable | no change | no change | no change | Current DB lacks `evolution_events`; do not guess. |
| s2p | unavailable | unavailable | unavailable | unavailable | no change | no change | no change | SDK preset exists, but no SDK-side S2P app DB/event data was found. |

Future tuning rule after data is collected:

- Keep `window >= 5`.
- Keep `0 < min_improvement_rate < 1`.
- Keep `cooldown >= window`.
- Higher measured evolution-event volume should generally use a larger `plateau_window` and/or stricter `min_improvement_rate`.
- Lower measured evolution-event volume should generally use a smaller `plateau_window` and/or lower `min_improvement_rate`.
- Keep values simple, e.g. windows in `5`, `10`, `15`, `20` increments and cooldowns that are integer multiples of the selected window.

## 8. No Tuning Recommendation

No production tuning should be implemented in this pass. The default values are identical and therefore eligible for future differentiation, but reliable measured evolution-event data is missing.

## 9. Exact Implementation Scope

Deferred implementation scope after event data exists:

- `copilot_sdk/scoring/presets/trading.py`
- `copilot_sdk/scoring/presets/purchasing.py`
- `copilot_sdk/scoring/presets/dataops.py`
- `copilot_sdk/scoring/presets/s2p.py`, only if SDK-side S2P data is collected or a clear policy is approved
- `tests/test_plateau_preset_config.py`
- possibly a new behavioral test file proving each preset config is passed into `CompoundingScorer` and that plateau detection behavior changes as intended

Forbidden for the future tuning implementation unless separately justified:

- `copilot_sdk/evolution/evolver.py`
- scoring, reward, conservation, evolution ledger, graph persistence logic
- app source files outside tests/data collection tooling
- any repo outside `copilot-sdk`

## 10. Test Plan

When reliable event data exists and implementation is approved:

1. Update `tests/test_plateau_preset_config.py` so it asserts measured, copilot-specific values rather than identical defaults. The existing test currently asserts all presets have window 10, rate 0.2, cooldown 50; see `tests/test_plateau_preset_config.py:11-20`.
2. Keep `test_scorer_uses_preset_plateau_config` or an equivalent behavioral test proving `CompoundingScorer.from_preset(..., evolve=True)` passes the preset config into `AgentEvolver`; see `tests/test_plateau_preset_config.py:23-57`.
3. Add behavioral plateau tests for at least the lowest-volume and highest-volume chosen configs using seeded ledger events, modeled after `tests/evolution/test_plateau.py:58-98`.
4. Add a measurement test or diagnostic script test only if a canonical event collection workflow is formalized. Source-only tests are insufficient for tuning correctness.

## 11. Validation Commands

Discovery-only validation used:

```powershell
python "$env:TEMP\_sdk_plateau_counts.py"
```

Future implementation validation:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest tests\test_plateau_preset_config.py -v --timeout=120
python -m pytest tests\evolution\test_plateau.py -v --timeout=120
python -m pytest tests/ -q --timeout=120
```

Future data collection, if using existing scripts:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python scripts\preseed_all_copilots.py --force
```

Only run that command with the intended Trading, Purchasing, and DataOps backends running, because the script talks to backend APIs; see `scripts/preseed_all_copilots.py:1-5`.

## 12. Open Questions / Blockers

1. No persisted `evolution_events` data is present in the existing app DBs, so measured event ratios are unavailable.
2. The preseed script seeds through live backend APIs, so a repeatable measurement run needs a defined environment and reset policy.
3. `scripts/evolve_demo.py` can produce synthetic event counts, but it uses synthetic factors and an in-memory graph store subclass; see `scripts/evolve_demo.py:19-27` and `scripts/evolve_demo.py:36-71`. Decide whether this is acceptable only for smoke testing or also for tuning data.
4. SDK-side `s2p` is a preset, but no SDK app-local S2P DB was found in this repo. External S2P config is reference-only.

## 13. Reading Log with File:Line Evidence

- Repo rule: docs are aspirational until proven in code: `CLAUDE.md:1-12`.
- SDK preset registry: `copilot_sdk/scoring/presets/__init__.py:8-13`.
- `DomainShape.tensor_size`: `copilot_sdk/scoring/config.py:32-38`.
- Trading shape and plateau config: `copilot_sdk/scoring/presets/trading.py:20-41`, `copilot_sdk/scoring/presets/trading.py:59-61`.
- Purchasing shape and plateau config: `copilot_sdk/scoring/presets/purchasing.py:20-46`, `copilot_sdk/scoring/presets/purchasing.py:64-66`.
- DataOps shape and plateau config: `copilot_sdk/scoring/presets/dataops.py:20-48`, `copilot_sdk/scoring/presets/dataops.py:66-68`.
- SDK S2P shape and plateau config: `copilot_sdk/scoring/presets/s2p.py:17-45`, `copilot_sdk/scoring/presets/s2p.py:63-65`.
- External S2P reference dimensions: `../s2p-copilot/backend/app/domains/s2p/config.py:1-5`, `../s2p-copilot/backend/app/domains/s2p/config.py:64-67`.
- PlateauConfig definition and enabled rule: `copilot_sdk/evolution/evolver.py:16-24`.
- AgentEvolver plateau config fallback: `copilot_sdk/evolution/evolver.py:33-38`.
- Scorer passes preset plateau config: `copilot_sdk/scoring/scorer.py:561-567`.
- Evolution requires at least 10 verified decisions before running: `copilot_sdk/scoring/scorer.py:573-579`.
- Plateau detection semantics: `copilot_sdk/evolution/evolver.py:151-193`.
- Improvement event extraction: `copilot_sdk/evolution/evolver.py:215-230`.
- Evolution ledger persistence call: `copilot_sdk/evolution/ledger.py:25-40`.
- SQLite evolution table creation and insert: `copilot_sdk/graph/sqlite_store.py:164-198`.
- Plateau tests: `tests/evolution/test_plateau.py:79-157`.
- Preset plateau tests: `tests/test_plateau_preset_config.py:11-20`, `tests/test_plateau_preset_config.py:23-57`, `tests/test_plateau_preset_config.py:60-89`.
- Preseed script scope and domains: `scripts/preseed_all_copilots.py:1-5`, `scripts/preseed_all_copilots.py:22`, `scripts/preseed_all_copilots.py:83-120`, `scripts/preseed_all_copilots.py:299-340`, `scripts/preseed_all_copilots.py:357-413`, `scripts/preseed_all_copilots.py:474-500`.
- Local evolution demo: `scripts/evolve_demo.py:19-27`, `scripts/evolve_demo.py:43-71`, `scripts/evolve_demo.py:75-85`.
