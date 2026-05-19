# SDK Tensor-Derived PlateauConfig Plan

## 1. Executive Summary

Classification: `READY_TO_IMPLEMENT`.

The SDK contains four in-scope presets: `dataops`, `purchasing`, `s2p`, and `trading`; the registry is defined in `copilot_sdk/scoring/presets/__init__.py:8-13`. Each preset currently returns `PlateauConfig()` with default values instead of tensor-derived copilot-specific values: Trading at `copilot_sdk/scoring/presets/trading.py:59-61`, Purchasing at `copilot_sdk/scoring/presets/purchasing.py:64-66`, DataOps at `copilot_sdk/scoring/presets/dataops.py:66-68`, and S2P at `copilot_sdk/scoring/presets/s2p.py:63-65`.

The implementation should tune plateau detection by category/action cell count, not event counts and not full tensor size. Use:

```text
cells = C * A
density_ratio = cells / 20
plateau_window = round(10 * sqrt(density_ratio))
min_improvement_rate = 0.20
plateau_cooldown = plateau_window * 5
```

Purchasing is the baseline because its live preset has C=5 and A=4, so cells=20; see `copilot_sdk/scoring/presets/purchasing.py:20-46`.

The target values are:

| preset | current | target |
| --- | --- | --- |
| trading | `(10, 0.20, 50)` | `(9, 0.20, 45)` |
| purchasing | `(10, 0.20, 50)` | `(10, 0.20, 50)` |
| s2p | `(10, 0.20, 50)` | `(11, 0.20, 55)` |
| dataops | `(10, 0.20, 50)` | `(12, 0.20, 60)` |

Because three of the four presets differ from the target and the current tests assert identical defaults, implementation is required.

## 2. Current PlateauConfig Definition and Defaults

`PlateauConfig` is a frozen dataclass in `copilot_sdk/evolution/evolver.py:16-20` with these constructor argument names:

| constructor arg | default | evidence |
| --- | ---: | --- |
| `plateau_window` | 10 | `copilot_sdk/evolution/evolver.py:16-18` |
| `min_improvement_rate` | 0.2 | `copilot_sdk/evolution/evolver.py:18-20` |
| `plateau_cooldown` | 50 | `copilot_sdk/evolution/evolver.py:18-20` |

There is no dataclass `__post_init__` validation. The current runtime enablement check is `plateau_window > 0 and min_improvement_rate > 0`; see `copilot_sdk/evolution/evolver.py:22-24`.

## 3. Current Preset Inventory

The preset registry contains exactly these four names in live code: `dataops`, `purchasing`, `s2p`, and `trading`; see `copilot_sdk/scoring/presets/__init__.py:8-13`.

| preset | class | current PlateauConfig evidence |
| --- | --- | --- |
| trading | `TradingPreset` | `return PlateauConfig()` at `copilot_sdk/scoring/presets/trading.py:59-61` |
| purchasing | `PurchasingPreset` | `return PlateauConfig()` at `copilot_sdk/scoring/presets/purchasing.py:64-66` |
| dataops | `DataOpsPreset` | `return PlateauConfig()` at `copilot_sdk/scoring/presets/dataops.py:66-68` |
| s2p | `S2PPreset` | `return PlateauConfig()` at `copilot_sdk/scoring/presets/s2p.py:63-65` |

`tests/test_plateau_preset_config.py` currently asserts all registry presets use the identical default values of 10, 0.2, and 50; see `tests/test_plateau_preset_config.py:11-20`.

## 4. Tensor Geometry Table

Formula:

```text
cells = C * A
density_ratio = cells / 20
plateau_window = round(10 * sqrt(density_ratio))
min_improvement_rate = 0.20
plateau_cooldown = plateau_window * 5
```

The SDK `DomainShape` records `n_categories`, `n_actions`, and `n_factors`; it also exposes `tensor_shape` and `tensor_size`, but this plan intentionally uses only C x A for plateau scaling. Evidence: `copilot_sdk/scoring/config.py:13-38`.

| preset | C | A | d | cells = C x A | current PlateauConfig | target PlateauConfig | formula evidence |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| trading | 5 | 3 | 6 | 15 | `(10, 0.20, 50)` | `PlateauConfig(plateau_window=9, min_improvement_rate=0.20, plateau_cooldown=45)` | Shape from `copilot_sdk/scoring/presets/trading.py:20-41`; target: `round(10 * sqrt(15/20)) = 9`, cooldown `9 * 5 = 45`. |
| purchasing | 5 | 4 | 6 | 20 | `(10, 0.20, 50)` | `PlateauConfig(plateau_window=10, min_improvement_rate=0.20, plateau_cooldown=50)` | Shape from `copilot_sdk/scoring/presets/purchasing.py:20-46`; target: `round(10 * sqrt(20/20)) = 10`, cooldown `10 * 5 = 50`. |
| s2p | 5 | 5 | 7 | 25 | `(10, 0.20, 50)` | `PlateauConfig(plateau_window=11, min_improvement_rate=0.20, plateau_cooldown=55)` | Shape from `copilot_sdk/scoring/presets/s2p.py:17-45`; target: `round(10 * sqrt(25/20)) = 11`, cooldown `11 * 5 = 55`. |
| dataops | 6 | 5 | 6 | 30 | `(10, 0.20, 50)` | `PlateauConfig(plateau_window=12, min_improvement_rate=0.20, plateau_cooldown=60)` | Shape from `copilot_sdk/scoring/presets/dataops.py:20-48`; target: `round(10 * sqrt(30/20)) = 12`, cooldown `12 * 5 = 60`. |

## 5. Scope Decision

### In Scope

- `copilot_sdk/scoring/presets/trading.py`
- `copilot_sdk/scoring/presets/purchasing.py`
- `copilot_sdk/scoring/presets/dataops.py`
- `copilot_sdk/scoring/presets/s2p.py`
- `tests/test_plateau_preset_config.py`

S2P is in scope because the SDK has a local `S2PPreset` and registers it directly; see `copilot_sdk/scoring/presets/s2p.py:11-15` and `copilot_sdk/scoring/presets/__init__.py:8-13`.

### Out of Scope

- Any repo outside `copilot-sdk`
- `s2p-copilot`
- SOC / `gen-ai-roi-demo-v4-v50`
- ci-platform
- GAE
- SDK evolution runtime logic in `copilot_sdk/evolution/evolver.py`
- scoring, reward, conservation, ledger, graph persistence, and app code

## 6. Corrected Formula Rationale

Use C x A because plateau-driving evolution events are distributed over category/action decision cells. The factor count `d` is useful for documentation and tensor context, but it should not scale plateau settings because factor dimensions do not create separate category/action decision cells.

The square root is sub-linear smoothing. It compresses differences relative to linear scaling and keeps tuning conservative:

- Trading has 15 cells, 25% fewer than the purchasing baseline, but the window becomes 9 rather than 7 or 8.
- DataOps has 30 cells, 50% more than baseline, but the window becomes 12 rather than 15.

The rate threshold remains constant at `0.20` to preserve the semantic rule for what counts as insufficient recent improvement while letting the observation window and cooldown scale with category/action density.

## 7. Implementation Plan

Do not change `PlateauConfig` structure or evolution runtime semantics.

Change each preset `plateau_config` property to return explicit constructor arguments:

```python
return PlateauConfig(
    plateau_window=<target_window>,
    min_improvement_rate=0.20,
    plateau_cooldown=<target_window * 5>,
)
```

Exact source edits:

1. `copilot_sdk/scoring/presets/trading.py`: replace `return PlateauConfig()` with `plateau_window=9`, `min_improvement_rate=0.20`, `plateau_cooldown=45`.
2. `copilot_sdk/scoring/presets/purchasing.py`: optionally make the baseline explicit with `plateau_window=10`, `min_improvement_rate=0.20`, `plateau_cooldown=50`.
3. `copilot_sdk/scoring/presets/s2p.py`: replace `return PlateauConfig()` with `plateau_window=11`, `min_improvement_rate=0.20`, `plateau_cooldown=55`.
4. `copilot_sdk/scoring/presets/dataops.py`: replace `return PlateauConfig()` with `plateau_window=12`, `min_improvement_rate=0.20`, `plateau_cooldown=60`.

Comments to add:

- A short comment near the explicit constructor is acceptable if it states the formula without overexplaining:
  `# Tensor-density plateau tuning: window=round(10*sqrt((C*A)/20)); cooldown=5*window.`
- Do not say sqrt amplifies differences. It smooths sub-linearly.

## 8. Test Plan

Update `tests/test_plateau_preset_config.py`.

Required tests:

1. `test_preset_plateau_config_tensor_derived`
   - Iterate the live `PRESET_REGISTRY`.
   - Compute cells as `preset.shape.n_categories * preset.shape.n_actions`.
   - Compute expected window as `round(10 * sqrt(cells / 20))`.
   - Assert `plateau_window == expected_window`.
   - Assert `min_improvement_rate == 0.2`.
   - Assert `plateau_cooldown == expected_window * 5`.
   - This proves C x A is used, not C x A x d.

2. `test_purchasing_is_plateau_baseline`
   - Assert Purchasing has C=5, A=4, cells=20.
   - Assert baseline config is window 10, rate 0.2, cooldown 50.

3. `test_plateau_window_ordering_by_cells`
   - Assert Trading window < Purchasing window < DataOps window.
   - Assert S2P is between Purchasing and DataOps if included in the registry.

4. Keep or adapt `test_scorer_uses_preset_plateau_config`
   - Existing behavior test proves `CompoundingScorer.from_preset(..., evolve=True)` passes the preset config through to `AgentEvolver`; see `tests/test_plateau_preset_config.py:23-57`.

5. Keep `test_plateau_config_backward_compatible`
   - Existing test proves a legacy preset with no plateau config still falls back to `PlateauConfig()`; see `tests/test_plateau_preset_config.py:60-89`.

No tests should require external databases or external repos.

## 9. Validation Commands

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest tests\test_plateau_preset_config.py -v --timeout=120
python -m pytest tests\evolution\test_plateau.py -v --timeout=120
python -m pytest tests/ -q --timeout=120
```

Optional architecture check:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
Select-String -Path copilot_sdk\scoring\presets\*.py -Pattern "PlateauConfig\(" -Context 0,4
```

## 10. Open Questions / Blockers

None for implementation.

The field named `min_improvement_rate` is the live SDK name for the request's `rate_threshold`; see `copilot_sdk/evolution/evolver.py:18-20` and the comparison at `copilot_sdk/evolution/evolver.py:172-175`.

## 11. Reading Log with File:Line Evidence

- Repo grounding rules: `CLAUDE.md:1-12`.
- Graphify report was read as required for architecture questions: `graphify-out/GRAPH_REPORT.md:1-9`.
- PlateauConfig class and defaults: `copilot_sdk/evolution/evolver.py:16-24`.
- Plateau detection window/rate/cooldown semantics: `copilot_sdk/evolution/evolver.py:151-193`.
- Improvement event metadata extraction: `copilot_sdk/evolution/evolver.py:215-242`.
- DomainShape fields and tensor helpers: `copilot_sdk/scoring/config.py:13-38`.
- DomainPreset protocol includes `plateau_config`: `copilot_sdk/scoring/config.py:41-51`.
- Preset registry: `copilot_sdk/scoring/presets/__init__.py:8-13`.
- Trading shape/config: `copilot_sdk/scoring/presets/trading.py:20-41`, `copilot_sdk/scoring/presets/trading.py:59-61`.
- Purchasing shape/config: `copilot_sdk/scoring/presets/purchasing.py:20-46`, `copilot_sdk/scoring/presets/purchasing.py:64-66`.
- DataOps shape/config: `copilot_sdk/scoring/presets/dataops.py:20-48`, `copilot_sdk/scoring/presets/dataops.py:66-68`.
- S2P shape/config: `copilot_sdk/scoring/presets/s2p.py:17-45`, `copilot_sdk/scoring/presets/s2p.py:63-65`.
- Current identical-default preset test: `tests/test_plateau_preset_config.py:11-20`.
- Existing pass-through test: `tests/test_plateau_preset_config.py:23-57`.
- Existing backward-compatible fallback test: `tests/test_plateau_preset_config.py:60-89`.
- Existing plateau behavior tests: `tests/evolution/test_plateau.py:39-157`.
