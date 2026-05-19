# Block 1.2: Industry Archetype Generator

## 1. Executive Summary

Classification: SCOPE_REPAIR_NEEDED.

Current state: the SDK has two related configuration surfaces. The public `DomainConfig` protocol exposes `categories`, `actions`, `n_factors`, learning parameters, and lifecycle methods (`copilot_sdk/protocols/domain_config.py:9-23`). The current `CompoundingScorer` implementation consumes the newer scoring `DomainPreset` protocol, whose fields are `name`, `shape`, `penalty_ratio`, `bootstrap_centroids`, `eta_confirm`, `eta_override`, `temperature`, and `plateau_config` (`copilot_sdk/scoring/config.py:41-51`). `CompoundingScorer.from_preset()` only constructs presets from `PRESET_REGISTRY` (`copilot_sdk/scoring/scorer.py:115-160`; `copilot_sdk/scoring/presets/__init__.py:8-13`), and there is no `CompoundingScorer(config=...)` constructor path (`copilot_sdk/scoring/scorer.py:87-97`).

Target state: add an offline, deterministic `ArchetypeGenerator` that maps natural-language domain descriptions to an ephemeral `DomainPreset`-compatible config object. Generated configs must not be registered in `PRESET_REGISTRY`; tests should prove this invariant. The generator should live in a new module, `copilot_sdk/generators/archetype.py`, with tests in `tests/test_archetype_generator.py`.

This prompt is plan-only. No source, test, dependency, preset, registry, or config files were changed. No external repos were read, and the design uses no LLM API calls.

## 2. Current Architecture

### DomainConfig and DomainPreset Surfaces

`DomainConfig` is a runtime-checkable protocol with list-based `categories`, `actions`, `n_factors`, `penalty_ratio`, `eta_confirm`, `eta_override`, `d_max`, `tau`, and four methods: `get_initial_centroids`, `get_sigma_profile`, `get_category_index`, and `get_action_index` (`copilot_sdk/protocols/domain_config.py:9-23`). The root package exports `DomainConfig` from `copilot_sdk.protocols` (`copilot_sdk/__init__.py:16-21`; `copilot_sdk/protocols/__init__.py:1-7`). Hello World demonstrates a concrete `DomainConfig`-style class with those fields and methods (`examples/hello_world/config.py:10-35`).

The active scorer path uses `DomainShape` and `DomainPreset`. `DomainShape` stores `n_categories`, `n_actions`, `n_factors`, category/action/factor name tuples, validates name counts in `__post_init__`, and exposes `tensor_shape` as `(n_categories, n_actions, n_factors)` (`copilot_sdk/scoring/config.py:13-39`). `DomainPreset` requires `name`, `shape`, `penalty_ratio`, `bootstrap_centroids`, `eta_confirm`, `eta_override`, `temperature`, and optional `plateau_config` (`copilot_sdk/scoring/config.py:41-51`).

### Preset Registry Mechanics

`PRESET_REGISTRY` is a static dict with exactly `"dataops"`, `"purchasing"`, `"s2p"`, and `"trading"` mapped to their preset classes (`copilot_sdk/scoring/presets/__init__.py:3-13`). Existing tests assert the registry contents for plateau config (`tests/test_plateau_preset_config.py:20-34`) and individual preset registration (`tests/scoring/test_trading_preset.py:69-72`; `tests/scoring/test_purchasing_preset.py:71-75`; `tests/scoring/test_dataops_preset.py:68-73`; `tests/scoring/test_presets.py:12-15`).

### CompoundingScorer Construction

`CompoundingScorer.__init__()` accepts `preset: DomainPreset`, `store: DecisionStore`, `scorer: ProfileScorer`, optional graph/reward/credit/exploration components, and `evolve` (`copilot_sdk/scoring/scorer.py:84-97`). This is the safe direct construction path for generated configs. Existing tests construct `ProfileScorer` from a mock preset's `bootstrap_centroids`, action names, and category names, then pass that preset into `CompoundingScorer` (`tests/scoring/test_scorer.py:35-45`; `tests/scoring/conftest.py:12-37`).

`CompoundingScorer.from_preset()` requires the domain name to exist in `PRESET_REGISTRY`, instantiates the registered preset class, loads or copies `preset.bootstrap_centroids`, constructs `ProfileScorer(mu=centroids, actions=..., categories=...)`, then returns `CompoundingScorer(...)` (`copilot_sdk/scoring/scorer.py:115-160`). It rejects unknown preset names (`copilot_sdk/scoring/scorer.py:126-128`; `tests/scoring/test_scorer.py:58-61`).

### PlateauConfig

`PlateauConfig` is a frozen dataclass with constructor fields `plateau_window: int = 10`, `min_improvement_rate: float = 0.2`, and `plateau_cooldown: int = 50`; it is enabled when window and rate are positive (`copilot_sdk/evolution/evolver.py:16-25`). `CompoundingScorer._setup_evolution()` passes `getattr(self._preset, "plateau_config", None)` into `AgentEvolver` (`copilot_sdk/scoring/scorer.py:537-567`). Tests prove preset plateau configs use the C x A cell formula, constant `min_improvement_rate == 0.2`, and `plateau_cooldown == window * 5` (`tests/test_plateau_preset_config.py:13-34`).

### Seed Centroids and Shape Requirements

Preset centroids are numpy arrays shaped as `DomainShape.tensor_shape`, i.e. `(C, A, d)` (`copilot_sdk/scoring/config.py:32-39`). Trading, Purchasing, and DataOps load bootstrap JSON, validate the loaded centroid shape against `preset.shape.tensor_shape`, and fall back to `np.full(expected_shape, 0.5, dtype=np.float64)` on error (`copilot_sdk/scoring/presets/trading.py:73-83`; `copilot_sdk/scoring/presets/purchasing.py:78-90`; `copilot_sdk/scoring/presets/dataops.py:80-90`). S2P builds a `(5, 5, 7)` tensor from action centroid vectors repeated per category (`copilot_sdk/scoring/presets/s2p.py:72-85`). Existing tests assert bootstrap shapes for Trading `(5, 3, 6)`, Purchasing `(5, 4, 6)`, DataOps `(6, 5, 6)`, and S2P `(5, 5, 7)` (`tests/scoring/test_trading_preset.py:124-125`; `tests/scoring/test_purchasing_preset.py:125-126`; `tests/scoring/test_dataops_preset.py:140-141`; `tests/scoring/test_presets.py:17-48`).

### SDK-Local Preset Shapes

Trading is `(C=5, A=3, d=6)` with categories `equity_long`, `equity_short`, `crypto_spot`, `options`, `etf`; actions `buy`, `hold`, `sell`; and penalty ratio `2.0` (`copilot_sdk/scoring/presets/trading.py:14-45`). Purchasing is `(C=5, A=4, d=6)` with restaurant purchasing categories and penalty ratio `3.0` (`copilot_sdk/scoring/presets/purchasing.py:14-50`). DataOps is `(C=6, A=5, d=6)` with data reliability categories/actions and penalty ratio `10.0` (`copilot_sdk/scoring/presets/dataops.py:14-52`). SDK-local S2P is `(C=5, A=5, d=7)` and penalty ratio `5.0` (`copilot_sdk/scoring/presets/s2p.py:11-49`).

### Dependency Status for sklearn

`pyproject.toml` runtime dependencies are `numpy`, `httpx`, and a profile-scoring dependency; the dev optional dependencies are `pytest`, `fastapi`, and `httpx` (`pyproject.toml:7-15`). There is no `scikit-learn` or `sklearn` dependency in project metadata. A local import probe returned `sklearn_available: True`, but `tests/test_discipline.py` treats `sklearn` as a heavy dependency that must not be loaded during `import copilot_sdk` (`tests/test_discipline.py:145-154`). Therefore the generator may use sklearn only as a lazy optional import inside generator methods, with a deterministic no-sklearn fallback and no root package import side effects.

### Existing Generator / Archetype Code

There is no `copilot_sdk/generators` package today; `Test-Path copilot_sdk/generators` returned `False`. A repo search for Python generator/archetype APIs found no `copilot_sdk.generators`, `from_description`, `archetype`, or `TfidfVectorizer` usage in SDK Python code or tests.

## 3. Four Seed Archetypes

The generator should define four archetypes in the new module as deterministic data objects. Embedded references are normative inputs; live SDK presets are used only to validate feasible shapes and naming style. Generated archetypes are not new registered presets.

### Security Operations Reference

- Archetype name: `security_operations`.
- Canonical description: "Security operations teams investigate credential misuse, lateral movement, malware execution, command-and-control activity, privilege escalation, and data exfiltration. The copilot recommends response actions under high asymmetric error cost where false reassurance is expensive. Signals include identity risk, endpoint telemetry, network movement, data movement, privilege context, and threat confidence."
- Categories: `credential_access`, `lateral_movement`, `data_exfiltration`, `privilege_escalation`, `malware_execution`, `command_and_control`.
- Actions: planned generator defaults should use four generic response actions such as `monitor`, `investigate`, `escalate`, `contain`.
- Factors: planned generator defaults should use six bounded factors such as `identity_risk`, `asset_criticality`, `threat_confidence`, `blast_radius`, `control_coverage`, `analyst_context`.
- C=6, A=4, d=6, cells=24.
- penalty_ratio=20.0.
- Seed centroid strategy: fixed seeded RNG around 0.5, clipped to `[0.0, 1.0]`, shape `(6, 4, 6)`.
- PlateauConfig target: `round(10 * sqrt(24 / 20)) = 11`, rate `0.20`, cooldown `55`.
- Rationale: embedded reference says high asymmetric security response cost; generated only, not a registry preset.

### Procurement / Source-to-Pay Reference

- Archetype name: `source_to_pay`.
- Canonical description: "Source-to-pay teams evaluate invoices, purchase orders, supplier exceptions, contract coverage, and payment terms. The copilot detects duplicate invoices, price variance, quantity mismatch, contract gaps, and format compliance issues. Recommended actions balance automation with buyer review, leakage investigation, and specialist referral."
- Categories: `price_variance`, `duplicate_invoice`, `quantity_mismatch`, `contract_gap`, `format_compliance`.
- Actions: use embedded-compatible five actions aligned with SDK-local S2P style: `auto_approve`, `hold_for_review`, `escalate_to_buyer`, `flag_leakage`, `refer_to_specialist`.
- Factors: use seven factors aligned with SDK-local S2P style: `match_status`, `amount_variance_ratio`, `duplicate_score`, `supplier_exception_history`, `payment_terms_impact`, `commodity_index_correlation`, `tax_regulatory_compliance`.
- C=5, A=5, d=7, cells=25.
- penalty_ratio=5.0.
- Seed centroid strategy: fixed seeded RNG around 0.5 or reuse the deterministic action-vector pattern from SDK-local S2P as a generator template; SDK-local S2P already uses action centroid vectors repeated per category (`copilot_sdk/scoring/presets/s2p.py:72-85`).
- PlateauConfig target: `round(10 * sqrt(25 / 20)) = 11`, rate `0.20`, cooldown `55`.
- Rationale: embedded reference matches the SDK-local `s2p` shape and penalty ratio (`copilot_sdk/scoring/presets/s2p.py:17-49`), but generated output must remain ephemeral.

### DataOps Reference

- Archetype name: `dataops`.
- Canonical description: "Data operations teams monitor schema changes, pipeline failures, data quality incidents, access anomalies, performance degradation, and configuration drift. The copilot recommends approval, investigation, owner escalation, downstream pause, or specialist referral based on operational impact. Signals include impact scope, source reliability, recurrence, urgency, freshness, and business criticality."
- Categories: `schema_change`, `pipeline_failure`, `data_quality`, `access_anomaly`, `performance_degradation`, `configuration_drift`.
- Actions: `auto_approve`, `investigate`, `escalate_to_owner`, `pause_downstream`, `refer_to_specialist`.
- Factors: `impact_scope`, `source_reliability`, `recurrence_frequency`, `downstream_urgency`, `data_freshness`, `business_criticality`.
- C=6, A=5, d=6, cells=30.
- penalty_ratio=10.0.
- Seed centroid strategy: fixed seeded RNG around 0.5, clipped to `[0.0, 1.0]`, shape `(6, 5, 6)`.
- PlateauConfig target: `round(10 * sqrt(30 / 20)) = 12`, rate `0.20`, cooldown `60`.
- Rationale: shape and penalty match SDK-local DataOps dimensions and penalty (`copilot_sdk/scoring/presets/dataops.py:20-52`), with embedded category names taking precedence for the generator archetype.

### Financial Services New Archetype

- Archetype name: `financial_services`.
- Canonical description: "Financial services teams review transaction anomalies, fraud signals, credit risk, compliance breaches, and regulatory reporting exceptions. The copilot recommends approval, review, escalation, or rejection under material but bounded financial and regulatory risk. Signals include transaction amount, counterparty risk, deviation from historical patterns, regulatory exposure, frequency, and velocity."
- Categories: `transaction_anomaly`, `compliance_breach`, `credit_risk`, `fraud_detection`, `regulatory_reporting`.
- Actions: `approve`, `flag_review`, `escalate`, `reject`.
- Factors: `transaction_amount`, `counterparty_risk`, `pattern_deviation`, `regulatory_exposure`, `historical_frequency`, `velocity`.
- C=5, A=4, d=6, cells=20.
- penalty_ratio=8.0.
- Seed centroid strategy: fixed seeded RNG around 0.5, clipped to `[0.0, 1.0]`, shape `(5, 4, 6)`.
- PlateauConfig target: `round(10 * sqrt(20 / 20)) = 10`, rate `0.20`, cooldown `50`.
- Rationale: penalty sits between the embedded high-asymmetry security reference and lower procurement reference.

## 4. Generator Design

Input is natural language text, expected to be 3-5 sentences but accepted at any length. Empty or whitespace-only descriptions should raise a clear `ValueError` unless a later implementation explicitly chooses a documented default.

Output should be an ephemeral `GeneratedDomainPreset` dataclass implementing the `DomainPreset` surface. It should contain `name`, `shape: DomainShape`, `penalty_ratio`, `bootstrap_centroids`, `eta_confirm=0.05`, `eta_override=0.01`, `temperature=0.1`, and `plateau_config: PlateauConfig`. This matches the scorer-required fields in `DomainPreset` (`copilot_sdk/scoring/config.py:41-51`) and the existing preset field pattern (`copilot_sdk/scoring/presets/trading.py:14-70`; `copilot_sdk/scoring/presets/s2p.py:11-74`).

Matching should be local and deterministic. Prefer lazy optional `sklearn.feature_extraction.text.TfidfVectorizer` and cosine similarity when sklearn is available. Because `sklearn` is not a declared dependency and must not load during root SDK import (`pyproject.toml:7-15`; `tests/test_discipline.py:145-154`), sklearn must only be imported inside the generator method. If unavailable, use a deterministic fallback based on normalized token overlap between the input and canonical archetype descriptions.

Overrides may alter `penalty_ratio`, `categories`, `actions`, `factors`, or explicit dimensions only when the resulting `DomainShape` remains internally consistent. Validation must reject duplicate/empty category/action/factor names, non-positive dimensions, non-finite penalty ratios, and dimension/name count mismatches. `DomainShape.__post_init__` already enforces tuple length consistency (`copilot_sdk/scoring/config.py:24-30`).

Centroid generation should be deterministic. Use a fixed seed derived from the archetype name and normalized overrides, create `np.full(shape, 0.5)` plus bounded small deterministic noise such as `[-0.1, 0.1]`, then clip to `[0.0, 1.0]` and store as `np.float64`. This preserves the shape expected by `ProfileScorer(mu=...)`, which existing construction passes from `preset.bootstrap_centroids` (`copilot_sdk/scoring/scorer.py:137-150`).

PlateauConfig should use the current SDK-EVOLUTION-TUNING rule already protected by tests: `cells = C * A`, `window = round(10 * sqrt(cells / 20))`, `min_improvement_rate = 0.20`, `plateau_cooldown = window * 5` (`tests/test_plateau_preset_config.py:13-34`). Do not use `C * A * d`.

## 5. API Design

Future API:

- `ArchetypeGenerator.from_description(text: str, overrides: dict | None = None) -> GeneratedDomainPreset`.
- `ArchetypeGenerator.list_archetypes() -> list[str]`.
- `ArchetypeGenerator.from_archetype(name: str, overrides: dict | None = None) -> GeneratedDomainPreset`.
- Optional transparent helper: `ArchetypeGenerator.score_archetypes(text: str) -> list[tuple[str, float]]`.

Generated configs are ephemeral and must not mutate `PRESET_REGISTRY`. `from_preset()` is intentionally not the primary path because it rejects unknown names not present in the registry (`copilot_sdk/scoring/scorer.py:126-128`). To construct a scorer from a generated preset, future tests should follow the existing direct path: create `DecisionStore`, create `ProfileScorer(mu=preset.bootstrap_centroids, actions=list(preset.shape.action_names), categories=list(preset.shape.category_names))`, then call `CompoundingScorer(preset, store, scorer, graph_store=...)` (`tests/scoring/test_scorer.py:35-45`).

## 6. Module Location

Future files:

- `copilot_sdk/generators/archetype.py` (new): generator, generated preset dataclass, deterministic matching and fallback, centroid builder, plateau helper.
- `copilot_sdk/generators/__init__.py` (new, optional): only if package-level import is needed. Do not import sklearn here.
- `tests/test_archetype_generator.py` (new): offline deterministic tests.

No existing preset, scorer, evolution, registry, dependency, or root package files should change in Prompt 1.

## 7. What Does NOT Change

- Existing preset files remain unchanged.
- `PRESET_REGISTRY` remains unchanged (`copilot_sdk/scoring/presets/__init__.py:8-13`).
- `CompoundingScorer` remains unchanged unless a later implementation prompt explicitly approves a minimal adapter; direct construction already exists (`copilot_sdk/scoring/scorer.py:87-97`).
- `PlateauConfig` class remains unchanged (`copilot_sdk/evolution/evolver.py:16-25`).
- No source/test/config changes were made in this planning prompt.
- No external repo changes or reads.
- No LLM API calls.
- Financial Services is generator-only, not a registered preset.

## 8. Risks and Mitigations

- No single `DomainConfig` class backs current scoring: return `GeneratedDomainPreset`, and optionally provide a DomainConfig-compatible view only if later needed.
- `CompoundingScorer(config=...)` is unsupported: use direct constructor with `GeneratedDomainPreset`, `DecisionStore`, and `ProfileScorer` (`copilot_sdk/scoring/scorer.py:87-97`; `tests/scoring/test_scorer.py:35-45`).
- sklearn unavailable or undeclared: lazy optional import plus token-overlap fallback; do not add dependency in Prompt 1.
- Root SDK heavy import regression: never import sklearn from `copilot_sdk/__init__.py`, since heavy deps are forbidden on root import (`tests/test_discipline.py:145-154`).
- Non-deterministic centroids: derive RNG seed from archetype and overrides; tests assert repeatability.
- Invalid overrides: validate with `DomainShape` and explicit checks before creating centroids (`copilot_sdk/scoring/config.py:24-34`).
- Weak matching signal: expose similarity scores optionally and test obvious nearest-neighbor examples.
- Unsupported names: archetypes store canonical categories/actions/factors, and overrides are validated for non-empty unique strings.
- Penalty semantics differ by domain: use embedded references for generator defaults and do not infer hidden domain costs.
- Plateau field names differ from assumptions: use live `PlateauConfig(plateau_window=..., min_improvement_rate=..., plateau_cooldown=...)` (`copilot_sdk/evolution/evolver.py:16-20`).
- Accidental registry mutation: add `test_no_preset_registry_mutation`.
- Adding dependencies without approval: forbidden in Prompt 1; no `pyproject.toml` edit.

## 9. Test Plan

Future tests:

- `test_from_archetype_soc_produces_valid_config`: generated security config has expected C/A/d, categories, penalty, centroid shape, and plateau config.
- `test_from_archetype_applies_overrides`: safe overrides alter names/penalty and recompute shape, centroids, and PlateauConfig.
- `test_from_description_matches_nearest_archetype`: deterministic industry descriptions select expected archetypes.
- `test_generated_config_constructs_compounding_scorer_or_supported_equivalent`: use the direct constructor path proven by existing scorer tests.
- `test_plateau_config_follows_cells_formula`: assert C x A formula, constant rate, and cooldown equal to 5 x window.
- `test_centroid_shape_matches_categories_actions_factors`: assert generated centroids shape is `(len(categories), len(actions), len(factors))`.
- `test_invalid_description_uses_reasonable_default_or_clear_error`: prefer clear `ValueError` for empty text.
- `test_invalid_archetype_name_raises_clear_error`: unknown names fail with available archetype list.
- `test_no_preset_registry_mutation`: registry contents remain exactly the pre-call set.
- `test_financial_services_archetype_has_expected_shape_and_penalty`: assert C=5, A=4, d=6, cells=20, penalty 8.0.

Tests must be offline, deterministic, and must not call any LLM or external service.

## 10. Files to Modify in Future Implementation

Production files:

- `copilot_sdk/generators/archetype.py` (new): in scope because no generator package exists and no existing archetype code was found; it should import `DomainShape`, `DomainPreset`-compatible fields, and `PlateauConfig` (`copilot_sdk/scoring/config.py:13-51`; `copilot_sdk/evolution/evolver.py:16-25`).
- `copilot_sdk/generators/__init__.py` (new, optional): only to expose `ArchetypeGenerator`; it must not import sklearn.

Test files:

- `tests/test_archetype_generator.py` (new): in scope because existing tests already validate preset/scorer construction and registry invariants (`tests/scoring/test_scorer.py:35-45`; `tests/test_plateau_preset_config.py:20-34`).

Dependency/config files:

- None in Prompt 1. `pyproject.toml` does not declare scikit-learn (`pyproject.toml:7-15`), and adding it requires explicit future approval.

Forbidden files/repos:

- Existing preset files.
- `copilot_sdk/scoring/scorer.py`.
- `copilot_sdk/scoring/presets/__init__.py`.
- `copilot_sdk/evolution/evolver.py`.
- `pyproject.toml` unless a later dependency decision explicitly approves it.
- Any source/test/config file outside the future implementation scope.
- Any external repo.

## 11. Future Implementation Sequence

1. Prompt 1: implement `copilot_sdk/generators/archetype.py`, optional package init, deterministic matching/fallback, generated preset dataclass, centroid builder, plateau helper, and `tests/test_archetype_generator.py`. No registry/scorer/dependency changes.
2. Prompt 2: only if Prompt 1 discovers a construction gap, implement a minimal scorer construction adapter and focused tests. Prefer no source changes because direct construction is already supported.
3. Prompt 3: GPT-5.5 line-by-line and architecture review.
4. Prompt 4: targeted fixer only if P1/P2 findings remain.

## 12. Validation Commands for Future Implementation

Targeted archetype generator tests:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest tests\test_archetype_generator.py -v --timeout=120
```

Existing preset/scorer tests:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest tests\scoring tests\test_plateau_preset_config.py -q --timeout=120
```

Full SDK tests:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest tests/ -q --timeout=120
```

Do not hardcode expected pass counts.

## 13. Reading Log

- `CLAUDE.md:1-58`: grounding contract, public SDK protocol discipline, no-git rule, graphify instruction.
- `graphify-out/GRAPH_REPORT.md:1-136`: architecture navigation and core abstractions.
- `copilot_sdk/protocols/domain_config.py:1-23`: public `DomainConfig` protocol.
- `copilot_sdk/protocols/__init__.py:1-7`: protocol exports.
- `copilot_sdk/__init__.py:1-21`: package exports and public quick-start mention.
- `copilot_sdk/scoring/config.py:1-51`: `DomainShape` and `DomainPreset`.
- `copilot_sdk/scoring/scorer.py:84-160,537-571`: direct constructor, `from_preset`, evolution plateau use.
- `copilot_sdk/scoring/presets/__init__.py:1-15`: `PRESET_REGISTRY`.
- `copilot_sdk/scoring/presets/trading.py:1-83`: Trading preset fields, shape, plateau, centroids.
- `copilot_sdk/scoring/presets/purchasing.py:1-90`: Purchasing preset fields, shape, plateau, centroids.
- `copilot_sdk/scoring/presets/dataops.py:1-90`: DataOps preset fields, shape, plateau, centroids.
- `copilot_sdk/scoring/presets/s2p.py:1-85`: SDK-local S2P preset fields, shape, plateau, centroids.
- `copilot_sdk/evolution/evolver.py:1-25`: `PlateauConfig`.
- `examples/hello_world/config.py:1-35`: concrete `DomainConfig`-style example.
- `tests/test_discipline.py:98-108,145-154`: DomainConfig method expectations and heavy dependency import guard.
- `tests/test_plateau_preset_config.py:1-131`: tensor-derived plateau tests and scorer plateau use.
- `tests/scoring/conftest.py:1-56`: mock preset and centroid shape style.
- `tests/scoring/test_scorer.py:30-75`: direct construction and from_preset tests.
- `tests/scoring/test_trading_preset.py:69-82,124-140`: registry/from_preset/bootstrap shape tests.
- `tests/scoring/test_purchasing_preset.py:71-84,125-136`: registry/from_preset/bootstrap shape tests.
- `tests/scoring/test_dataops_preset.py:68-83,140-152`: registry/from_preset/bootstrap shape tests.
- `tests/scoring/test_presets.py:1-70`: SDK-local S2P shape and scorer tests.
- `pyproject.toml:1-36`: dependencies and mypy settings.

## Prompt Verification Pass

- All referenced existing paths were read; future paths are marked proposed new files.
- The config object interface is proven from `DomainConfig`, `DomainShape`, and `DomainPreset`.
- `from_preset()` and direct construction assumptions are proven from source and tests.
- `PRESET_REGISTRY` mutation is explicitly forbidden.
- Financial Services remains generator-only, not a registered preset.
- Tensor shapes and `PlateauConfig` constructor field names are cited from live code.
- Tests are deterministic and offline.
- No external repos were read.
- No source/test/config files were changed.
