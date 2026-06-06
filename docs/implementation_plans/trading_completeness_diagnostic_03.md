# Trading Completeness Diagnostic 03

Date: 2026-06-05
Model: gpt-5.3
Task Type: Diagnostic document creation only; no source code changes.
Repo: copilot-sdk
Diagnostic Scope: Trading packaging/PyPI readiness source state, Trading AgentEvolver configuration/wiring, `main.py` mock/fixture context, and `routers/social.py` multi-trader TODO/stub context.
Prior Diagnostics Read: `docs/implementation_plans/trading_backend_filetree_diagnostic.md`; `docs/implementation_plans/trading_deep_chase_diagnostic_01b.md`; `docs/implementation_plans/sdk_backend_endpoint_map_diagnostic_02.md`

## Executive Summary

* Overall verdict: packaging and social/multi-trader source paths are present; Trading evolution is wired but narrow and should remain a supplement item if P84 expects full domain dimension coverage.
* P62 packaging verdict: DROP from implementation queue by source inspection. App-local packaging and `ci-trading` entry point exist, but no install/build command was run.
* P84 AgentEvolver verdict: SUPPLEMENT. Evolution variants/config/provider are real and wired into `main.py`, but visible dimensions cover execution threshold and revenge cooldown only.
* main.py mock verdict: DEMO INFRA. Mock-like hits are seed fixtures and demo bundle restoration, not unconditional production mock returns.
* P7 social/multi-trader verdict: DONE by source inspection. Social endpoints and backing trader profile service exist; the only stub-like signals are exception-suppression `pass` statements in JSON-safe conversion.
* Biggest remaining ambiguity: no runtime packaging install, CLI invocation, API requests, or E2E validation were run by instruction.
* Recommended next prompt: MAP queue update that drops P62 and P7 from implementation, keeps P84 as a targeted supplement, and leaves main.py mock cleanup out of the implementation queue unless demo seeding behavior is later product-scoped.

## Path Resolution

* CLAUDE_SDK value: `C:\Users\baner\CopyFolder\IOT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Repo path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* apps/trading path: `apps/trading`
* main.py path: `apps/trading/backend/app/main.py`
* evolution directory path: `apps/trading/backend/app/evolution`
* social.py path: `apps/trading/backend/app/routers/social.py`
* Prior Diag 01 found: YES
* Prior Diag 01b found: YES
* Prior Diag 02 found: YES

## CLAUDE.md Relevant Notes

* Do not use git directly.
* Docs are aspirational until proven in code; inspect actual source files.
* Cite file and line for behavioral claims.
* Code and tests beat docs; report drift when source and docs disagree.
* Make surgical changes only.
* Repo guidance says to verify after changes, but this task explicitly prohibited tests and allowed only this Markdown write.

## Part 1 - P62 TRD-PYPI Packaging State

### Packaging files inspected

| File | Exists | Relevant Evidence | Notes |
| ---- | -----: | ----------------- | ----- |
| `apps/trading/pyproject.toml` | YES | `[build-system]` at L1; `[project]` at L5; `name = "ci-trading"` at L6; `[project.scripts]` at L51; `ci-trading = "ci_trading.cli:main"` at L52; package include `["ci_trading*"]` at L56. | App-local packaging file. |
| `apps/trading/setup.py` | NO | Relevant packaging file scan found only `apps/trading/pyproject.toml` after excluding `node_modules` and `__pycache__`. | Not needed when `pyproject.toml` is authoritative. |
| `apps/trading/setup.cfg` | NO | Relevant packaging file scan found only `apps/trading/pyproject.toml`. | Not present. |
| `apps/trading/MANIFEST` / `MANIFEST.in` | NO | Relevant packaging file scan found only `apps/trading/pyproject.toml`. | A broader first pass overmatched a frontend `web-app-manifest.js` under `frontend/node_modules`; that is not a Python packaging manifest. |
| SDK root `pyproject.toml` | YES | Root packaging entry-point check found no `ci-trading`, `trading`, `console_scripts`, `[project.scripts]`, or `[tool.poetry.scripts]` matches. | Trading package metadata is app-local, not SDK-root. |
| `apps/trading/ci_trading/cli.py` | YES | `_load_backend_cli` at L16; `cli_path = backend_dir / "cli.py"` at L25; `spec_from_file_location` at L26; `main` at L35; `backend_cli.main(...)` at L38-L39. | Console wrapper delegates to existing backend CLI. |

### Entry point analysis

* ci-trading entry point present: YES
* Entry point mechanism: PEP 621 `[project.scripts]` in `apps/trading/pyproject.toml`.
* Package location: app-local Trading package under `apps/trading`, with setuptools package discovery including `ci_trading*`.
* Evidence:
  * `apps/trading/pyproject.toml` L6 names the package `ci-trading`.
  * `apps/trading/pyproject.toml` L51-L52 defines `ci-trading = "ci_trading.cli:main"`.
  * `apps/trading/pyproject.toml` L54-L56 configures package discovery for `ci_trading*`.
  * `apps/trading/ci_trading/cli.py` L35-L39 defines `main` and delegates to backend CLI.

### P62 Verdict

* Verdict: DROP
* Remaining effort: validation only, if desired.
* Rationale: Packaging metadata and `ci-trading` entry point exist in source. This diagnostic did not run `pip install`, build a wheel, or invoke the console script, so DROP means no further implementation prompt appears necessary from source inspection, not that packaging was live-tested.

## Part 2 - P84 TRD-AGENT-EVOLVER-FULL

### Evolution file inventory

| File | Size | Purpose | Stub/TODO Signals |
| ---- | ---: | ------- | ----------------- |
| `apps/trading/backend/app/evolution/__init__.py` | 0.6KB | Re-exports evolution dimensions, config, variants, and provider functions. | None found in targeted scan. |
| `apps/trading/backend/app/evolution/dimensions.py` | 0.8KB | Defines `TRADING_VARIANT_DIMENSIONS` and default variants. | None found in targeted scan. |
| `apps/trading/backend/app/evolution/evolver_config.py` | 3.5KB | Defines `TRADING_VARIANTS`, `TRADING_EVOLVER_CONFIG`, variant spec conversion, and `get_trading_variants`. | None found in targeted scan. |
| `apps/trading/backend/app/evolution/variant_provider.py` | 0.3KB | Provides `get_trading_variant` lookup over `get_trading_variants`. | None found in targeted scan. |

### Variant dimensions

Variant dimensions found:

* `execution_threshold`: defined in `dimensions.py` in `TRADING_VARIANT_DIMENSIONS`; values `baseline` and `selective`; description controls Trading execution confidence thresholds.
* `revenge_cooldown`: defined in `dimensions.py` in `TRADING_VARIANT_DIMENSIONS`; values `baseline` and `conservative`; description controls post-loss cooldown and post-loss size limits.

Evidence:

* `dimensions.py` defines `TRADING_VARIANT_DIMENSIONS` at L10.
* `evolver_config.py` defines four `VariantSpec` entries at L24-L68: `EXECUTION_THRESHOLD_v1`, `EXECUTION_THRESHOLD_v2`, `REVENGE_COOLDOWN_v1`, and `REVENGE_COOLDOWN_v2`.

Alignment with Trading PD v1.0 concepts:

* Present: execution confidence threshold, skip threshold, post-loss cooldown, post-loss size limit.
* Partial/implicit: position sizing appears through `max_size_ratio`; emotional/behavioral indicator appears through revenge cooldown.
* Not visibly represented as first-class dimensions in the inspected evolution directory: market regime, strategy family beyond variant family, risk regime, timing quality, signal confidence, and broader position-sizing variants.

### Evolver config analysis

* Real config or placeholder: Real config.
* Domain-specific values:
  * `TRADING_EVOLVER_CONFIG` is a `PromptEvolverConfig` at `evolver_config.py` L76-L80 with categories from `TradingPreset().shape.category_names` or fallback Trading categories.
  * Promotion settings are `exploration_constant=1.414`, `promotion_improvement_threshold=0.05`, and `promotion_min_samples=50`.
  * Variant metadata includes Trading-specific thresholds: `strong_execution_confidence`, `skip_threshold`, `cooldown_minutes`, and `max_size_ratio`.
* Evidence:
  * `evolver_config.py` imports `PromptEvolverConfig` and `VariantSpec` at L8.
  * Category derivation/fallback is at L10-L19.
  * `TRADING_EVOLVER_CONFIG` is defined at L76.
  * `get_trading_variant_specs` returns fresh `VariantSpec` instances at L84-L96.
  * `variant_to_payload` returns route/CLI payload shape at L100-L117.
  * `get_trading_variants` returns provider payloads at L120-L123.

### Variant provider / main.py wiring

* get_trading_variants or equivalent exists: YES
* Wired into main.py or SDK evolution router: YES
* Evidence:
  * `evolver_config.py` defines `get_trading_variants` at L120-L123.
  * `variant_provider.py` imports `get_trading_variants` at L5 and defines `get_trading_variant` at L8-L12.
  * `__init__.py` re-exports `get_trading_variant` and `get_trading_variants` at L12-L21.
  * `main.py` imports `get_trading_variants` from `.evolution`.
  * `main.py` wires `create_evolution_router(... variant_provider=get_trading_variants)` in the evolution router include block.

### P84 Verdict

* Verdict: SUPPLEMENT
* Remaining effort: low-medium.
* Rationale: Evolution config/provider are real and wired, with no TODO/pass/stub signals in targeted scans. It is not clearly "FULL" work. However, visible dimensions are narrow, so if P84 expects full Trading AgentEvolver coverage across regime, strategy, risk, timing, signal confidence, position sizing, and emotional indicators, a supplement prompt is still warranted.

## Part 3 - main.py Mock Context

| Line / Context | Mock Signal | Guard / Condition | Classification | Action Needed |
| -------------- | ----------- | ----------------- | -------------- | ------------- |
| L61 `SEED_FIXTURE_PATH = DATA_DIR / "trading_seed_v2.json"` | fixture | Used by auto-seeding path; not a runtime endpoint return. | DEMO INFRA | None for implementation queue unless demo seeding should be removed. |
| L142-L149 `_seed_from_fixtures` reads `SEED_FIXTURE_PATH`; on unavailable/invalid fixture returns zero seed counts. | fixture | Startup seeding helper; handles missing fixture by returning zero counts. | DEMO INFRA | None. |
| L201 warning when no fixture outcomes written. | fixture | Auto-seed warning only. | DEMO INFRA | None. |
| L220 `_seed_from_fixtures` result printed as auto-seeded decisions/outcomes. | fixture | Auto-seeding path. | DEMO INFRA | None. |
| L230 `demo_bundle_path` parameter on `create_app`. | demo | Explicit app factory parameter can disable demo bundle with `False`. | DEMO INFRA | None. |
| L254-L259 `_bundle_path` defaults to repo demo bundle, can be disabled with `demo_bundle_path is False`. | demo | Explicit conditional. | DEMO INFRA | None. |
| L320 `_restore_demo_bundle(seed_graph_store, _bundle_path, domain=DOMAIN)` | demo | Guarded by `_bundle_path is not False`; active AGE path skips auto-seed nearby. | DEMO INFRA | None. |

### main.py Mock Verdict

* Verdict: DEMO INFRA
* If production stubs exist, smallest MAP/fixer item: No production stubs were identified in `main.py` by this diagnostic. If product policy later requires disabling default demo restoration in non-demo environments, create a small config-gating prompt for startup demo seeding only.

## Part 4 - social.py TODOs and P7 TRD-MULTI-TRADER

### social.py endpoints

| Method | Path | Function | Evidence |
| ------ | ---- | -------- | -------- |
| GET | `/api/trading/traders` | `list_traders` | `social.py` L28. |
| GET | `/api/trading/traders/compare` | `compare_traders` | `social.py` L33. |
| GET | `/api/trading/traders/{trader_id}/profile` | `trader_profile` | `social.py` L40. |
| GET | `/api/trading/traders/{trader_id}/edge` | `trader_edge` | `social.py` L44. |
| GET | `/api/trading/social/leaderboard` | `leaderboard` | `social.py` L48. |
| GET | `/api/trading/social` | `social_summary` | `social.py` L53. |
| GET | `/api/trading/profiles` | `profiles` | `social.py` L58. |
| GET | `/api/trading/trader/{trader_id}` | `legacy_trader_profile` | `social.py` L64. |
| POST | `/api/trading/score-as` | `score_as` | `social.py` L68. |

### TODO / stub review

| Line / Context | TODO or Stub | Blocks Multi-Trader? | Notes |
| -------------- | ------------ | -------------------: | ----- |
| L109 exception handler in `_json_safe` around `value.tolist()` | `pass` | NO | Exception suppression for serialization fallback, not feature TODO. |
| L114 exception handler in `_json_safe` around `value.item()` | `pass` | NO | Exception suppression for serialization fallback, not feature TODO. |

Backing service evidence:

* `TraderProfileService` exists at `services/trader_profiles.py` L20.
* It defines `list_traders` L24, `get_trader_profile` L40, `get_trader_edge` L44, `get_trader_comparison` L56, and `leaderboard` L66.
* It groups decisions by trader/entity metadata via `_grouped_decisions` L71 and `_decision_trader` L118-L122.
* Targeted service scan found no TODO, NotImplementedError, standalone pass, or stub signals.

### P7 Verdict

* Verdict: DONE
* Remaining effort: validation only.
* Rationale: Multi-trader API routes and backing service methods exist, use graphstore-backed trader metadata, and no blocking TODO/stub signals were observed in source inspection. This does not prove runtime/API behavior because no tests or server requests were run.

## Final MAP Completeness Table

| Prompt                     | Diagnostic Area | Verdict | Remaining Effort | Key Evidence |
| -------------------------- | --------------- | ------- | ---------------- | ------------ |
| P7 TRD-MULTI-TRADER        | social.py       | DONE | Validation only | Nine social/multi-trader endpoints in `social.py`; `TraderProfileService` backs profile, comparison, edge, and leaderboard. |
| P62 TRD-PYPI               | packaging       | DROP | Validation only | `apps/trading/pyproject.toml` defines `ci-trading` package and `[project.scripts]` entry point to `ci_trading.cli:main`. |
| P84 TRD-AGENT-EVOLVER-FULL | evolution       | SUPPLEMENT | Low-medium | Real VariantSpec/config/provider and main wiring exist; visible dimensions are narrow. |
| main.py mocks              | mock context    | DEMO INFRA | None | Mock-like hits are fixture/demo bundle startup seeding paths, with disable path for demo bundle. |

## Diagnostic Limitations

* This diagnostic does not validate runtime behavior.
* This diagnostic does not run tests.
* This diagnostic does not prove frontend/UI wiring.
* This diagnostic does not prove package installation unless install commands are later run.
* DROP verdict means source inspection suggests the item is complete enough to drop from implementation queue, not that it passed live packaging or E2E validation.

## Recommended Next Step

Run a MAP queue update: drop P62 from implementation work pending packaging validation, mark P7 as done pending runtime/API validation, keep P84 as a focused supplement for broader Trading evolution dimensions, and take no main.py mock action unless product policy requires stricter non-demo startup behavior.
