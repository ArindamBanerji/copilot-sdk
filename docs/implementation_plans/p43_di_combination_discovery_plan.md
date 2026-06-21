# P43 DI Combination Discovery Plan

Date: 2026-06-14

## Executive Verdict

READY_FOR_IMPLEMENTATION: YES

P43 can be implemented as a small, isolated Data Intelligence module that
operates over Python decision dictionaries. The current DI package already has
stable dataclass/export conventions, and GraphStore already exposes decision
read methods that return dictionaries containing factor vectors and verified
outcome fields. P43 does not require GraphStore, scorer, conservation, package,
profiler, or NL-query changes.

Key evidence:

- DI currently exports `NLQueryRouter`, `ProfileConfig`, `SourceProfile`,
  `BaseSourceProfiler`, and P42 query-pattern symbols from
  `copilot_sdk/di/__init__.py:3` and `copilot_sdk/di/__init__.py:16`.
- P30 models are simple frozen dataclasses: `ProfileConfig` at
  `copilot_sdk/di/models.py:10` and `SourceProfile` at
  `copilot_sdk/di/models.py:22`.
- `BaseSourceProfiler` accepts a connector and optional `ProfileConfig`, then
  returns a `SourceProfile` without GraphStore/scorer coupling
  (`copilot_sdk/di/profiler.py:19`, `copilot_sdk/di/profiler.py:26`,
  `copilot_sdk/di/profiler.py:68`).
- The public `GraphStore` protocol already exposes `get_decision`,
  `get_all_decisions`, and `get_verified_decisions`
  (`copilot_sdk/graph/protocol.py:39`, `copilot_sdk/graph/protocol.py:50`,
  `copilot_sdk/graph/protocol.py:53`).
- SQLite decisions store `factor_vector_json`, `recommended_action`,
  `confidence`, and `created_at` (`copilot_sdk/graph/sqlite_store.py:407`).
- SQLite verified rows join outcomes and include `actual_action`, `is_correct`,
  and `verified_at` (`copilot_sdk/graph/sqlite_store.py:1868`,
  `copilot_sdk/graph/sqlite_store.py:1873`).

## DI Module State

Current DI files:

- `copilot_sdk/di/__init__.py`
- `copilot_sdk/di/models.py`
- `copilot_sdk/di/profiler.py`
- `copilot_sdk/di/nl_query.py`
- `copilot_sdk/di/query_patterns.py`

Current exports:

- `NLQueryRouter`
- `ProfileConfig`
- `SourceProfile`
- `BaseSourceProfiler`
- `QueryResult`
- `QueryPattern`
- `MultiEntityPattern`
- `TimeWindowPattern`
- `AggregationPattern`
- `ComparisonPattern`
- `AccuracyPattern`

Evidence: `__all__` is defined in `copilot_sdk/di/__init__.py:16`.

P30 compatibility:

- `ProfileConfig` has numeric source-quality weights, a freshness window, and
  `required_fields` (`copilot_sdk/di/models.py:10`).
- `SourceProfile` represents source quality metrics, not decision-combination
  candidates (`copilot_sdk/di/models.py:22`).
- P43 should not edit `models.py` or `profiler.py`; new output models should
  live in `combination_discovery.py`.

Name conflicts:

- Search found no existing `CombinationCandidate` or `DiscoveryReport` in
  `copilot_sdk/di` or tests.
- There is an existing top-level `copilot_sdk.discovery` package with
  `DiscoveryEngine` and cross-system patterns. It is advisory cross-copilot
  infrastructure, not DI decision-list factor-pair discovery. Evidence:
  `DiscoveryEngine` registers copilots and pattern objects
  (`copilot_sdk/discovery/engine.py:20`, `copilot_sdk/discovery/engine.py:37`);
  `CentroidCorrelationPattern` operates over scorer centroid geometry
  (`copilot_sdk/discovery/patterns.py:24`, `copilot_sdk/discovery/patterns.py:36`).

Import/export convention:

- DI exports are centralized in `copilot_sdk/di/__init__.py`.
- P43 should add `CombinationCandidate`, `DiscoveryReport`, and a discovery
  function/class to `__all__` while preserving all existing symbols.

## Decision Data Contract

P43 implementation should accept:

```python
discover_combinations(decisions: list[dict[str, Any]], *, min_sample_size: int = 30, alpha: float = 0.05, max_candidates: int = 20) -> DiscoveryReport
```

No GraphStore object is required. Callers can pass `graph_store.get_verified_decisions(domain)`
results, but P43 must not call GraphStore methods itself.

### Required Fields

Each included row must normalize:

- factor values from at least two factor names.
- correctness as `True` or `False`.

Rows missing factor data or correctness are skipped and counted in report
warnings/metadata.

### Optional Fields

Optional fields useful for descriptions and future filters:

- `decision_id`
- `category`
- `recommended_action`
- `actual_action`
- `created_at`
- `verified_at`
- `amount`, `value`, `decision_value`, or `metadata.value`

Value fields are not required for P43 v1; if implemented, they should be
normalized only as metadata/context and not used for significance unless tests
cover that behavior.

### Factor Vector Normalization

Supported factor sources, in priority order:

1. `factors`: dict of numeric factor names to values.
2. `factor_values`: dict of numeric factor names to values.
3. `factor_vector`: list/tuple of numeric values plus factor names from
   `factor_names`, `metadata.factor_names`, or generated names `factor_0`,
   `factor_1`, ...
4. `metadata.factor_vector`: list/tuple of numeric values plus
   `metadata.factor_names` or generated names.

SQLite evidence:

- `write_decision()` stores factor names through the `factors` dict and derives
  `factor_vector` from `metadata.factor_vector` or factor order
  (`copilot_sdk/graph/sqlite_store.py:970`, `copilot_sdk/graph/sqlite_store.py:971`).
- `write_governed_decision()` stores `factor_names` and `factor_vector` in
  metadata and stores a numeric factor dict keyed by factor name
  (`copilot_sdk/graph/sqlite_store.py:1040`, `copilot_sdk/graph/sqlite_store.py:1046`).
- `_decision_from_row()` returns both `factors` and `factor_vector`
  (`copilot_sdk/graph/sqlite_store.py:2858`, `copilot_sdk/graph/sqlite_store.py:2859`).

Normalization rules:

- Ignore non-numeric factor values.
- Exclude reserved/non-factor keys frequently embedded in `factors`, including
  `entity_id` and `metadata`.
- If generated names are required, use deterministic `factor_{index}` names.
- A row contributes to a pair only when both pair factors and correctness are
  available.

### Correctness Normalization

Supported correctness sources, in priority order:

1. boolean `is_correct`
2. boolean `correct`
3. boolean `verified_correct`
4. numeric 0/1 forms of the above
5. string `outcome` values:
   - correct: `confirmed`, `correct`, `success`
   - incorrect: `override`, `overridden`, `incorrect`, `failure`
6. if both `actual_action` and `recommended_action` exist, equality means
   correct.

SQLite evidence:

- `write_outcome()` writes `actual_action`, `actual_index`, `is_correct`, and
  `verified_at` (`copilot_sdk/graph/sqlite_store.py:1108`,
  `copilot_sdk/graph/sqlite_store.py:1133`).
- `_verified_from_row()` returns `actual_action`, `actual_index`,
  `is_correct`, `verified_at`, `context`, and `outcome_metadata`
  (`copilot_sdk/graph/sqlite_store.py:2869`, `copilot_sdk/graph/sqlite_store.py:2874`).

### Missing-Field Behavior

P43 must:

- return an empty `DiscoveryReport` for empty decisions.
- skip rows with missing/invalid factor vectors.
- skip rows with missing correctness.
- count skipped rows in `DiscoveryReport.warnings`.
- avoid throwing on mixed decision shapes.
- avoid GraphStore method requirements.

## Statistical Design

P43 should be statistically conservative and explicit about approximations.

### Pair Features

For each factor pair `(a, b)` and each row with both numeric values:

- `x_i = value_a`
- `y_i = value_b`
- `correct_i = 1.0 if normalized correctness is True else 0.0`

Compute Pearson correlation between a pair-combination score and correctness.
Recommended pair-combination score:

```python
pair_score_i = z_a_i * z_b_i
```

where `z_a` and `z_b` are standardized factor values over the pair sample. This
captures interaction strength while remaining pure Python and scale-safe.

If implementation prefers raw product `value_a * value_b`, it must document that
choice and tests must cover scale sensitivity. Recommended implementation is
standardized product.

### Pearson Formula

For arrays `x` and `y` of length `n`:

```text
r = sum((x_i - mean_x) * (y_i - mean_y)) /
    sqrt(sum((x_i - mean_x)^2) * sum((y_i - mean_y)^2))
```

Constant-factor safety:

- If either variance term is zero, skip the pair.
- Add candidate/report warning: `constant_factor_skipped`.

All-correct/all-incorrect safety:

- Correctness variance is zero, so Pearson denominator is zero.
- Skip significance and return no significant candidates.
- Add report warning: `constant_correctness_target`.

### P-Value Approximation

Use Fisher z normal approximation with stdlib `math` only:

```text
z = atanh(r) * sqrt(n - 3)
p ≈ erfc(abs(z) / sqrt(2))
```

Required behavior:

- p-values are approximate, not exact.
- `p_value_method = "fisher_z_normal_approximation"` only when `n >= 30`.
- For `n < 30`:
  - `p_value = None`
  - `p_value_method = "insufficient_sample_for_asymptotic_p"`
  - do not mark the pair significant based on p-value.
  - add warning `insufficient_sample_for_asymptotic_p`.

This avoids exact p-value overclaim and satisfies the P43 small-sample rule.

### Significance Criteria

A pair is significant only when:

- `sample_size >= min_sample_size` (default `30`)
- both pair-score and correctness variance are non-zero
- `p_value is not None`
- `p_value <= alpha` (default `0.05`)
- `abs(correlation) >= min_abs_correlation` (recommended default `0.25`)

Candidates should be sorted by:

1. significant pairs first
2. descending `abs(correlation)`
3. descending `abs(lift_pp)`
4. factor names ascending for deterministic tie-breaks

### Lift Computation

Define aligned rows as rows whose pair score is greater than or equal to the
pair-score median:

```text
aligned = pair_score >= median(pair_score)
misaligned = pair_score < median(pair_score)
```

Then:

```text
accuracy_when_aligned = correct_aligned / n_aligned
accuracy_when_misaligned = correct_misaligned / n_misaligned
lift_pp = (accuracy_when_aligned - accuracy_when_misaligned) * 100
```

If either side is empty, set the corresponding accuracy and `lift_pp` to `None`
and add warning `insufficient_alignment_split`.

### Candidate Description

Use non-causal wording:

```text
"Factor pair {factor_a} + {factor_b} is associated with decision quality in this sample (r={correlation:.3f}, n={sample_size}). This is discovery evidence, not causal proof."
```

Do not claim the pair predicts future outcomes or should mutate scorer behavior.

### Warning / Metadata Fields

Report-level warnings should include:

- `no_decisions`
- `insufficient_valid_rows`
- `missing_factor_vector_rows=N`
- `missing_correctness_rows=N`
- `constant_factor_skipped=N`
- `constant_correctness_target`
- `approximate_p_values`

Candidate-level warnings should include:

- `approximate_p_value`
- `insufficient_sample_for_asymptotic_p`
- `insufficient_alignment_split`

## Output Model Design

Implement in `copilot_sdk/di/combination_discovery.py`.

### CombinationCandidate

Recommended frozen dataclass:

```python
@dataclass(frozen=True)
class CombinationCandidate:
    factor_a: str
    factor_b: str
    correlation: float | None
    p_value: float | None
    p_value_method: str
    sample_size: int
    accuracy_when_aligned: float | None
    accuracy_when_misaligned: float | None
    lift_pp: float | None
    description: str
    warnings: list[str] = field(default_factory=list)
```

Add `to_dict()` if useful for API-facing callers, mirroring `SourceProfile.to_dict()`
(`copilot_sdk/di/models.py:38`).

### DiscoveryReport

Recommended frozen dataclass:

```python
@dataclass(frozen=True)
class DiscoveryReport:
    total_pairs_tested: int
    significant_pairs: int
    candidates: list[CombinationCandidate]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    warnings: list[str] = field(default_factory=list)
```

Add `to_dict()` with ISO timestamp conversion for consistency with
`SourceProfile.to_dict()`.

### Public API

Recommended:

```python
def discover_combinations(
    decisions: list[dict[str, Any]],
    *,
    min_sample_size: int = 30,
    alpha: float = 0.05,
    min_abs_correlation: float = 0.25,
    max_candidates: int = 20,
) -> DiscoveryReport:
    ...
```

Optional class wrapper:

```python
class CombinationDiscovery:
    def discover(self, decisions: list[dict[str, Any]]) -> DiscoveryReport: ...
```

If a class is added, keep it stateless/config-only and pure Python.

## File Plan

Allowed implementation files:

- `copilot-sdk/copilot_sdk/di/combination_discovery.py`
- `copilot-sdk/copilot_sdk/di/__init__.py`
- `copilot-sdk/tests/test_combination_discovery.py`
- `copilot-sdk/docs/implementation_plans/p43_di_combination_discovery_plan.md`

Forbidden implementation files:

- `copilot-sdk/copilot_sdk/graph/*`
- `copilot-sdk/copilot_sdk/scoring/*`
- `copilot-sdk/copilot_sdk/di/models.py`
- `copilot-sdk/copilot_sdk/di/profiler.py`
- `copilot-sdk/copilot_sdk/di/nl_query.py`
- `copilot-sdk/copilot_sdk/di/query_patterns.py`
- package files

## Test Plan

Create `tests/test_combination_discovery.py`.

Required tests:

1. `test_correlated_pair_detected`
2. `test_no_significant_pair_for_noise`
3. `test_min_sample_enforced`
4. `test_pearson_known_values`
5. `test_fisher_p_value_approximation_for_large_sample`
6. `test_small_sample_p_value_unavailable`
7. `test_constant_factors_skipped`
8. `test_lift_computation`
9. `test_candidate_description_is_non_causal`
10. `test_candidates_sorted_deterministically`
11. `test_empty_decisions_report`
12. `test_single_factor_report`
13. `test_all_correct_skips_significance`
14. `test_all_incorrect_skips_significance`
15. `test_missing_factor_vector_rows_skipped`
16. `test_missing_correctness_rows_skipped`
17. `test_factor_vector_with_factor_names`
18. `test_factors_dict_excludes_metadata_and_entity_id`
19. `test_metadata_factor_vector_supported`
20. `test_init_export_preservation`
21. `test_no_graphstore_or_scorer_dependency`

Tests should use synthetic decision dictionaries only. Do not require SQLite,
GraphStore, scorer, or conservation objects.

## Validation Plan

Run from `copilot-sdk`:

```powershell
python -m pytest tests/test_combination_discovery.py -q --timeout=120
python -m pytest tests/ -k "di or combination" -q --timeout=120
python -m pytest tests/test_di_profiler.py tests/test_nl_query_extended.py -q --timeout=120
python -m pytest tests/ -q --timeout=120
```

Baseline validation run during discovery:

```powershell
python -m pytest tests/ -k "di or combination" -q --timeout=120
```

Result:

- `181 passed, 6 skipped, 1245 deselected, 2868 warnings`

Optional full baseline was also run:

```powershell
python -m pytest tests/ -q --timeout=120
```

Result:

- `1370 passed, 62 skipped, 2868 warnings`

## Risks / No-Go Conditions

No-go if implementation discovers that:

- factor vectors cannot be normalized safely from existing decision dictionaries.
- correctness cannot be normalized without writing outcomes or querying GraphStore.
- p-values cannot be represented honestly with stdlib-only approximation.
- adding DI exports breaks P30/P42 imports.
- implementation requires GraphStore/scorer/conservation/package changes.

Known limitations to document in implementation:

- P43 is association discovery, not causal proof.
- Fisher z p-values are asymptotic approximations.
- No p-value significance for `n < 30`.
- Constant factors and all-correct/all-incorrect samples cannot produce Pearson
  significance.

## Recommended Next Prompt Summary

Implement P43 with:

- `copilot_sdk/di/combination_discovery.py` containing the two output dataclasses,
  normalization helpers, Pearson/Fisher helpers, and `discover_combinations()`.
- Additive exports in `copilot_sdk/di/__init__.py`.
- Tests in `tests/test_combination_discovery.py`.
- No GraphStore, scorer, conservation, DI profiler, DI NL-query, or package changes.

## Implementation Addendum - 2026-06-15

Implemented files:

- Created `copilot_sdk/di/combination_discovery.py`.
- Created `tests/test_combination_discovery.py`.
- Updated `copilot_sdk/di/__init__.py` with additive exports.

Statistical design implemented:

- `CombinationDiscoveryEngine.discover()` normalizes decision dictionaries into
  numeric factor maps plus verified correctness labels.
- Supported factor locations are `factor_vector`, `factor_values`,
  `metadata.factor_vector`, and `factors` dictionaries.
- Supported correctness locations are `is_correct`, `correct`,
  `verified_correct`, clear outcome strings, and
  `actual_action == recommended_action`.
- Pair signal follows the plan: each factor is standardized across the pair
  sample, then the pair interaction score is `z_factor_a * z_factor_b`.
- Pearson correlation is computed between the pair interaction score and the
  correctness target.
- Candidate lift uses a median split: aligned rows have both factors at or above
  their medians, and misaligned rows are all other valid rows.
- Candidate significance requires minimum sample, correlation threshold,
  approximate p-value threshold, and lift threshold.

Public API implemented:

```python
discover_combinations(
    decisions,
    *,
    min_sample_size=30,
    alpha=0.05,
    min_abs_correlation=0.25,
    max_candidates=20,
)
```

P-value method and limitations:

- For `n >= 30`, p-values use Fisher z normal approximation:
  `atanh(r) * sqrt(n - 3)` and `math.erfc(abs(z) / sqrt(2))`.
- `p_value_method` is `"fisher_z_normal_approx"` when this approximation is
  used.
- For `n < 30`, `p_value=None` and
  `p_value_method="insufficient_sample_for_asymptotic_p"`.
- Approximate p-values are not presented as exact tests.
- Constant signals, constant targets, all-correct samples, and all-incorrect
  samples are skipped honestly with warnings instead of producing false
  candidates.

Tests added:

- Correlated pair discovery and no-significant-pair behavior.
- Minimum sample enforcement.
- Pearson known values.
- Fisher p-value approximation and small-sample p-value unavailability.
- Constant factor handling.
- Lift computation.
- Non-causal description wording.
- Deterministic candidate sorting.
- Empty decisions and single-factor reports.
- All-correct and all-incorrect safety.
- Missing factor vector and missing correctness warnings.
- `factors` dictionary and `metadata.factor_vector` support.
- Public helper behavior.
- Additive DI exports.
- No GraphStore/scorer and no NumPy/SciPy dependency checks.

Validation run so far:

```powershell
python -m pytest tests/test_combination_discovery.py -q --timeout=120
```

Result:

- `22 passed, 44 warnings`

```powershell
python -m pytest tests/ -k "di or combination" -q --timeout=120
```

Result:

- `203 passed, 6 skipped, 1245 deselected, 2912 warnings`

```powershell
python -m pytest tests/test_di_profiler.py tests/test_nl_query_extended.py -q --timeout=120
```

Result:

- `59 passed, 118 warnings`

```powershell
python -m pytest tests/ -q --timeout=120
```

Result:

- `1392 passed, 62 skipped, 2912 warnings`

Scope control:

- No GraphStore files changed.
- No scorer files changed.
- No conservation files changed.
- No package files changed.
- No DI profiler, DI NL-query, or query-pattern modules changed.

Known limitations:

- P43 reports associations in verified decision dictionaries only; it is not a
  causal inference engine.
- P-values are asymptotic approximations and unavailable for small samples.
- Dictionary factor-name inference is deterministic by sorted key order; list
  vectors without names use `factor_0`, `factor_1`, and so on.
