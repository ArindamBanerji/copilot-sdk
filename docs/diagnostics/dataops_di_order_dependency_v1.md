# DataOps DI Order Dependency Diagnostic

## §1 Failure Description

`tests/test_di_router.py::test_dataops_app_mounts_di_profiles_empty_registry` passes when run alone but returns HTTP 404 in the aggregate `-k dataops` run. The test constructs a DataOps app with `create_app(db_path=":memory:", demo_bundle_path=False)` at `tests/test_di_router.py:177-182`, then requests `/api/di/profiles` at `tests/test_di_router.py:184`. It expects status 200 and three DataOps profiler sources at `tests/test_di_router.py:186-192`.

The DataOps application does define `/api/di/profiles` in its own `create_app()` at `apps/dataops/backend/app/main.py:609-611`, and also mounts the SDK DI router at `apps/dataops/backend/app/main.py:621-622`. Therefore the observed 404 is consistent with the test receiving a different `app.main.create_app`, not with the DataOps DI registry being empty.

## §2 Collection Order

The requested collection command produced 45 selected tests, with the target in this order:

1. `tests/evolution/test_evolve_integration.py::test_dataops_actions_wired_correctly`
2. `tests/evolution/test_toy_rules.py::test_factor_weight_rule_works_with_dataops_action_count`
3. `tests/graph/test_soc_age_projection_contract.py::test_soc_dataops_context_requires_explicit_domain_partition`
4. `tests/rl/test_rl_wiring.py::test_from_preset_dataops_wires_financial_reward`
5. `tests/scoring/test_dataops_preset.py::test_preset_loads`
6. `tests/scoring/test_dataops_preset.py::test_preset_in_registry`
7. `tests/scoring/test_dataops_preset.py::test_from_preset_dataops_works`
8. `tests/scoring/test_dataops_preset.py::test_seed_data_loads`
9. `tests/scoring/test_dataops_preset.py::test_seed_covers_all_categories`
10. `tests/scoring/test_dataops_preset.py::test_seed_category_counts_are_as_expected`
11. `tests/scoring/test_dataops_preset.py::test_seed_action_counts_are_as_expected`
12. `tests/scoring/test_dataops_preset.py::test_seed_factors_match_preset`
13. `tests/scoring/test_dataops_preset.py::test_bootstrap_centroids_shape`
14. `tests/scoring/test_dataops_preset.py::test_bootstrap_produces_target_correct_action_probability`
15. `tests/scoring/test_dataops_preset.py::test_recurring_auto_approved_events_are_correct`
16. `tests/scoring/test_dataops_preset.py::test_first_time_auto_approved_events_are_incorrect`
17. `tests/scoring/test_dataops_preset.py::test_recurrence_frequency_more_predictive_than_source_reliability`
18. `tests/scoring/test_dataops_preset.py::test_fingerprint_shows_recurrence_signal_if_stable`
19. `tests/scoring/test_dataops_preset.py::test_end_to_end_score_learn_fingerprint_smoke`
20. `tests/test_category_mappings.py::test_get_mapping_soc_dataops_returns_mapping_dict`
21. `tests/test_category_mappings.py::test_get_mapping_dataops_purchasing_returns_mapping_dict`
22. `tests/test_dataops_oracle.py::test_dataops_deterministic`
23. `tests/test_dataops_oracle.py::test_dataops_treatment_higher`
24. `tests/test_dataops_oracle.py::test_dataops_correct_modeled`
25. `tests/test_dataops_oracle.py::test_dataops_domain_actions`
26. `tests/test_dataops_oracle.py::test_dataops_exp1_known_lift`
27. `tests/test_dataops_oracle.py::test_dataops_exp2_zero_lift`
28. `tests/test_dataops_oracle.py::test_dataops_exp3_floor_power`
29. `tests/test_dataops_oracle.py::test_dataops_exp4_gate_rejects`
30. `tests/test_dataops_oracle.py::test_readiness_dataops_instrumented`
31. `tests/test_di_router.py::test_dataops_app_mounts_di_profiles_empty_registry`

The collection output also showed that 2,497 tests were deselected. Pytest imports test modules during collection even when their tests do not match `-k dataops`. This distinction is material: `tests/test_schema_currency.py` is not in the selected list, but its module-level import executes during collection and creates the leaked state before item 1 runs.

## §3 Shared State Analysis

### Selected files before the target

| File | Relevant behavior | Shared DI/app state? |
|---|---|---|
| `tests/evolution/test_evolve_integration.py:11-17,22-29` | Builds `CompoundingScorer` instances with temporary databases; tests use scorer-local evolvers and stores. | No DI registry, route table, `app` import, or persistent environment mutation found. |
| `tests/evolution/test_toy_rules.py:1-8,55-80` | Imports and exercises pure evolution-rule classes. | No app or registry state. |
| `tests/graph/test_soc_age_projection_contract.py:39-59,341-346` | Its AGE helper may prepend `ci-platform` to `sys.path`; the helper imports `ci_platform`, not `app`. The projection registry is read and checked at `tests/graph/test_soc_age_projection_contract.py:353-375`. | No DataOps DI state. The `sys.path` change is not the cause of the Trading `app.main` module observed here. |
| `tests/rl/test_rl_wiring.py:14-24,31-42` | Creates `InMemoryGraphStore` instances per scorer. The two `monkeypatch` uses are scoped to individual tests at `tests/rl/test_rl_wiring.py:132-157` and `:189-223`. | No persistent DI/app state. |
| `tests/scoring/test_dataops_preset.py:9-16,72-80` | Prepends the GAE path and imports `gae.profile_scorer`; scorer databases are temporary or explicitly closed, e.g. `:72-80` and `:248-270`. | No `app.main` import or DI registry mutation. The module-level GAE path insertion is unrelated to the observed Trading `app` package. |
| `tests/test_category_mappings.py:82-113` | Creates a local scorer and a local `SharedPatternRegistry` for each test. | No module-level DI registry or `app` package import. |
| `tests/test_dataops_oracle.py:1-7,10-83` | Creates local `DataOpsOracle`/pipeline objects in each test. | No app, route, DI, or environment state. |

The selected predecessors therefore do not provide evidence of the leak.

### The actual collection-time importer

`tests/test_schema_currency.py:1-5` imports `render_shared` and `render_trading` from `scripts.generate_tab_state_types` at module import time. The generator performs these side effects at import time:

- `scripts/generate_tab_state_types.py:12-17` defines `TRADING_BACKEND` and prepends the repository and Trading backend paths to `sys.path`.
- `scripts/generate_tab_state_types.py:19-21` imports `app.state.key_manifest` and `app.state.schemas.trading` using the ambiguous top-level package name `app`.
- `apps/trading/backend/app/__init__.py:3` eagerly imports `.main`, so the import above loads Trading’s `app.main`.
- `apps/trading/backend/app/main.py:532` creates a module-level `app` object as a side effect of importing the module.

The diagnostic import trace observed `app.main` being resolved from:

`copilot-sdk/apps/trading/backend/app/main.py`

while the importing stack included `scripts/generate_tab_state_types.py:20` and `tests/test_schema_currency.py:5`.

### DataOps import behavior

The failing test only prepends the DataOps backend path if that path is absent at `tests/test_di_router.py:177-179`; it then performs the ambiguous import `from app.main import create_app` at `tests/test_di_router.py:180`. Python reuses an already-loaded `sys.modules["app.main"]`; changing `sys.path` does not replace that module or its parent package.

The resulting module state is:

```text
sys.modules["app"]      -> Trading backend app package
sys.modules["app.main"] -> Trading backend app.main
```

The observed 404 is consequently a namespace/module-cache collision. The DI router factory itself is safe with respect to registry state: `copilot_sdk/backend/di_router.py:51-58` receives a registry and creates a fresh closure-local `cache` for each router. It does not use a module-level profile registry or shared route object.

### DataOps `create_app()` safety

DataOps `create_app()` creates a fresh FastAPI instance at `apps/dataops/backend/app/main.py:519-524`, a fresh profiler registry at `:552-555`, and registers routes on that app at `:592-654`. It also sets the context-router evolution-store factory at `:630-632`, which is a separate module-level setter and is a real shared side effect, but it does not explain this 404: the failing call never reaches DataOps `create_app()` because `app.main` is already cached as Trading.

DataOps also has a module-level `app = create_app()` at `apps/dataops/backend/app/main.py:684`, and Trading has the analogous eager global at `apps/trading/backend/app/main.py:532`. Those globals increase import side effects, but the decisive collision is the shared top-level package name `app` in `sys.modules`.

## §4 Root Cause

`tests/test_schema_currency.py` is the causing collection-time importer. Its test body does not need to run; importing the module at `tests/test_schema_currency.py:5` imports `scripts/generate_tab_state_types.py`, which imports Trading’s ambiguous `app` package at `scripts/generate_tab_state_types.py:19-21`. Trading’s package initializer eagerly imports Trading `app.main` at `apps/trading/backend/app/__init__.py:3`.

The leaked state is:

```text
module cache: sys.modules["app"] and sys.modules["app.main"]
```

The DataOps target then executes `from app.main import create_app` at `tests/test_di_router.py:180`, but receives Trading’s cached factory. Trading’s application route registration is in `apps/trading/backend/app/main.py:383-491`; it has no DataOps `/api/di/profiles` route, producing the observed 404. The DataOps route exists at `apps/dataops/backend/app/main.py:609-611`.

ROOT_CAUSE: Collection-time import of `tests/test_schema_currency.py` loads Trading’s top-level `app.main` into `sys.modules` through `scripts/generate_tab_state_types.py` and `apps/trading/backend/app/__init__.py`; the DataOps test’s later unqualified `from app.main` reuses that cached Trading module.

## §5 Fix Options

1. **Systemic — eliminate the ambiguous `app` package boundary (recommended).** Import each backend through a unique package namespace or load the required schema modules under a uniquely named package. The generator should not make `app` resolve differently based on `sys.path` order. This addresses all cross-repo app collisions, not only this test.

2. **Systemic — remove eager application import from backend `app/__init__.py`.** Do not import `.main` from `apps/trading/backend/app/__init__.py:3` (and apply the same rule to other backend packages). This reduces collection-time side effects, but does not by itself make `app.main` unambiguous if another backend package is already cached.

3. **Tactical — make the DataOps test import explicit and isolated.** Before importing DataOps, remove `app` and all `app.*` entries from `sys.modules`, restore/prepend the DataOps backend path, invalidate import caches, and import DataOps. This can make the test deterministic, but it embeds import-cache cleanup in one test and leaves the production/tooling namespace collision intact.

4. **Tactical — lazy-load generator imports.** Move the `app.state` imports in `scripts/generate_tab_state_types.py:19-21` into `render_trading()` or a dedicated loader. This prevents unrelated test collection from importing Trading, but callers that execute `render_trading()` still need an explicit namespace boundary.

5. **Test-only — pair/ordering isolation.** Run the DataOps DI test in a subprocess or separate pytest invocation. This confirms the diagnosis but does not repair the shared import design.

## §6 Recommended Fix

Use option 1 as the durable fix: give backend application code unique import namespaces and make the schema generator import Trading schemas without the generic `app` name. Option 2 should accompany it where feasible to reduce import-time application construction.

As an immediate containment measure, use option 3 in the test while the namespace migration is planned. The containment must explicitly clear both `sys.modules["app"]` and `sys.modules["app.main"]` (including other `app.*` descendants) before importing DataOps; clearing only `sys.path` is insufficient.

Suggested pair commands for the user to run, as requested (not run during this investigation):

```powershell
python -m pytest tests/test_di_router.py::test_dataops_app_mounts_di_profiles_empty_registry tests/test_schema_currency.py -v
python -m pytest tests/test_di_router.py::test_dataops_app_mounts_di_profiles_empty_registry tests/test_s2p_preset.py -v
python -m pytest tests/test_di_router.py::test_dataops_app_mounts_di_profiles_empty_registry tests/test_chain_transfer.py -v
```

The first command is the highest-value reproducer because `tests/test_schema_currency.py:5` is the demonstrated collection-time importer. The pair should be interpreted carefully: because the leak occurs during module collection, the order and import behavior—not only test execution order—matters.

FIX_COMPLEXITY: moderate for the systemic namespace fix; trivial-to-moderate for a tactical test isolation guard.

## §7 Reading Log

Read fully:

- `copilot-sdk/CLAUDE.md`
- `copilot-sdk/graphify-out/GRAPH_REPORT.md`
- `copilot-sdk/tests/test_di_router.py`
- `copilot-sdk/tests/evolution/test_evolve_integration.py`
- `copilot-sdk/tests/evolution/test_toy_rules.py`
- `copilot-sdk/tests/graph/test_soc_age_projection_contract.py`
- `copilot-sdk/tests/rl/test_rl_wiring.py`
- `copilot-sdk/tests/scoring/test_dataops_preset.py`
- `copilot-sdk/tests/test_category_mappings.py`
- `copilot-sdk/tests/test_dataops_oracle.py`
- `copilot-sdk/copilot_sdk/backend/di_router.py`
- `copilot-sdk/apps/dataops/backend/app/main.py`
- `copilot-sdk/tests/test_schema_currency.py`
- `copilot-sdk/scripts/generate_tab_state_types.py`
- `copilot-sdk/apps/trading/backend/app/__init__.py`
- `copilot-sdk/apps/trading/backend/app/main.py`

Diagnostic commands run:

- `python -m pytest tests/ -k dataops --collect-only -q` — 45 selected tests; target is item 31.
- A read-only import-trace probe during collection — confirmed Trading `app.main` is loaded through `tests/test_schema_currency.py:5` → `scripts/generate_tab_state_types.py:20`.
- A read-only aggregate reproduction — confirmed 44 selected tests pass and the target returns 404.
- The target alone — passes in isolation.

No source or test files were modified. Only this diagnostic document was written.

READY: YES
