from __future__ import annotations

from pathlib import Path

from copilot_sdk.di import (
    CombinationCandidate,
    CombinationDiscoveryEngine,
    DiscoveryReport,
    discover_combinations,
)


def _decision(
    decision_id: str,
    factors: dict[str, float] | None = None,
    *,
    factor_vector: list[float] | None = None,
    factor_names: list[str] | None = None,
    metadata: dict | None = None,
    is_correct: bool | None = True,
    actual_action: str | None = None,
    recommended_action: str = "approve",
    outcome: str | None = None,
) -> dict:
    row = {
        "decision_id": decision_id,
        "recommended_action": recommended_action,
    }
    if factors is not None:
        row["factors"] = dict(factors)
    if factor_vector is not None:
        row["factor_vector"] = list(factor_vector)
    if factor_names is not None:
        row["factor_names"] = list(factor_names)
    if metadata is not None:
        row["metadata"] = dict(metadata)
    if is_correct is not None:
        row["is_correct"] = is_correct
    if actual_action is not None:
        row["actual_action"] = actual_action
    if outcome is not None:
        row["outcome"] = outcome
    return row


def _correlated_decisions(n: int = 60) -> list[dict]:
    rows = []
    half = n // 2
    for index in range(half):
        rows.append(
            _decision(
                f"aligned-{index}",
                {"alpha": 1.0, "beta": 1.0, "noise": float(index % 5) / 5.0},
                is_correct=True,
            )
        )
    for index in range(n - half):
        rows.append(
            _decision(
                f"misaligned-{index}",
                {
                    "alpha": 1.0 if index % 2 == 0 else 0.0,
                    "beta": 0.0 if index % 2 == 0 else 1.0,
                    "noise": float((index + 2) % 5) / 5.0,
                },
                is_correct=False,
            )
        )
    return rows


def _noise_decisions(n: int = 60) -> list[dict]:
    rows = []
    for index in range(n):
        rows.append(
            _decision(
                f"noise-{index}",
                {
                    "alpha": float(index % 7),
                    "beta": float((index * 3) % 11),
                    "gamma": float((index * 5) % 13),
                },
                is_correct=index % 2 == 0,
            )
        )
    return rows


def test_discover_correlated_pair():
    report = discover_combinations(_correlated_decisions())

    assert report.significant_pairs >= 1
    candidate = report.candidates[0]
    assert {candidate.factor_a, candidate.factor_b} == {"alpha", "beta"}
    assert candidate.p_value is not None
    assert candidate.p_value_method == "fisher_z_normal_approx"


def test_discover_no_significant_random_pair():
    report = discover_combinations(_noise_decisions(), min_abs_correlation=0.95)

    assert report.significant_pairs == 0
    assert report.candidates == []


def test_min_sample_enforced():
    report = discover_combinations(_correlated_decisions(20))

    assert report.significant_pairs == 0
    assert "insufficient_valid_rows" in report.warnings


def test_correlation_computation_known_values():
    engine = CombinationDiscoveryEngine(p_value_min_sample=30)

    r, p_value, method, warnings = engine._compute_correlation([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])

    assert r == 1.0
    assert p_value is None
    assert method == "insufficient_sample_for_asymptotic_p"
    assert "insufficient_sample_for_asymptotic_p" in warnings


def test_p_value_approximation_for_large_sample():
    engine = CombinationDiscoveryEngine()

    r, p_value, method, warnings = engine._compute_correlation(
        [float(index) for index in range(40)],
        [float(index) for index in range(40)],
    )

    assert r is not None and r > 0.99
    assert p_value is not None and p_value < 0.05
    assert method == "fisher_z_normal_approx"
    assert "approximate_p_value" in warnings


def test_p_value_unavailable_for_small_sample():
    engine = CombinationDiscoveryEngine(p_value_min_sample=30)

    r, p_value, method, warnings = engine._compute_correlation(
        [float(index) for index in range(10)],
        [float(index) for index in range(10)],
    )

    assert r is not None
    assert p_value is None
    assert method == "insufficient_sample_for_asymptotic_p"
    assert "insufficient_sample_for_asymptotic_p" in warnings


def test_constant_factor_handled():
    rows = [
        _decision(f"d-{index}", {"constant": 1.0, "beta": float(index)}, is_correct=index % 2 == 0)
        for index in range(40)
    ]

    report = discover_combinations(rows)

    assert report.significant_pairs == 0
    assert "constant_factor_skipped=1" in report.warnings


def test_lift_computation():
    report = discover_combinations(_correlated_decisions())

    candidate = report.candidates[0]
    assert candidate.accuracy_when_aligned == 1.0
    assert candidate.accuracy_when_misaligned == 0.0
    assert candidate.lift_pp == 100.0


def test_description_format_non_causal():
    report = discover_combinations(_correlated_decisions())

    description = report.candidates[0].description
    assert "observed accuracy" in description
    assert "Observed lift" in description
    assert "verified decisions" in description
    assert "not causal proof" in description
    assert "caused" not in description.lower()


def test_sorting_by_absolute_lift():
    rows = _correlated_decisions()
    for index, row in enumerate(rows):
        row["factors"]["delta"] = row["factors"]["alpha"] if index < 45 else 1.0 - row["factors"]["alpha"]

    report = discover_combinations(rows, max_candidates=5)

    lifts = [abs(candidate.lift_pp) for candidate in report.candidates]
    assert lifts == sorted(lifts, reverse=True)


def test_empty_decisions():
    report = discover_combinations([])

    assert report.total_pairs_tested == 0
    assert report.significant_pairs == 0
    assert report.candidates == []
    assert "no_decisions" in report.warnings


def test_single_factor_no_pairs():
    rows = [_decision(f"d-{index}", {"alpha": float(index)}, is_correct=index % 2 == 0) for index in range(40)]

    report = discover_combinations(rows)

    assert report.total_pairs_tested == 0
    assert report.significant_pairs == 0


def test_all_correct_no_meaningful_lift():
    rows = [_decision(f"d-{index}", {"alpha": float(index), "beta": float(index % 3)}, is_correct=True) for index in range(40)]

    report = discover_combinations(rows)

    assert report.significant_pairs == 0
    assert "constant_correctness_target" in report.warnings


def test_all_incorrect_no_meaningful_lift():
    rows = [_decision(f"d-{index}", {"alpha": float(index), "beta": float(index % 3)}, is_correct=False) for index in range(40)]

    report = discover_combinations(rows)

    assert report.significant_pairs == 0
    assert "constant_correctness_target" in report.warnings


def test_missing_factor_vector_skipped_with_warning():
    rows = _correlated_decisions()
    rows.append(_decision("missing-factor", None, is_correct=True))

    report = discover_combinations(rows)

    assert "missing_factor_vector_rows=1" in report.warnings


def test_factor_dict_input_supported():
    report = discover_combinations(_correlated_decisions())

    assert report.candidates
    assert {report.candidates[0].factor_a, report.candidates[0].factor_b} == {"alpha", "beta"}


def test_metadata_factor_vector_supported():
    rows = []
    for index, row in enumerate(_correlated_decisions()):
        rows.append(
            _decision(
                row["decision_id"],
                None,
                metadata={
                    "factor_names": ["alpha", "beta"],
                    "factor_vector": [row["factors"]["alpha"], row["factors"]["beta"]],
                },
                is_correct=row["is_correct"],
            )
        )

    report = discover_combinations(rows)

    assert report.candidates
    assert {report.candidates[0].factor_a, report.candidates[0].factor_b} == {"alpha", "beta"}


def test_missing_correctness_skipped_for_lift():
    rows = _correlated_decisions()
    rows.append(_decision("missing-correctness", {"alpha": 1.0, "beta": 1.0}, is_correct=None))

    report = discover_combinations(rows)

    assert "missing_correctness_rows=1" in report.warnings


def test_public_discover_combinations_helper():
    report = discover_combinations(_correlated_decisions(), min_sample_size=30, alpha=0.05, max_candidates=1)

    assert isinstance(report, DiscoveryReport)
    assert len(report.candidates) <= 1


def test_init_exports():
    assert CombinationCandidate
    assert DiscoveryReport
    assert CombinationDiscoveryEngine
    assert discover_combinations


def test_no_graphstore_or_scorer_dependency():
    source = Path("copilot_sdk/di/combination_discovery.py").read_text(encoding="utf-8")

    assert "GraphStore" not in source
    assert "graph" not in source.lower()
    assert "scorer" not in source.lower()


def test_no_numpy_scipy_dependency():
    source = Path("copilot_sdk/di/combination_discovery.py").read_text(encoding="utf-8").lower()

    assert "numpy" not in source
    assert "scipy" not in source
