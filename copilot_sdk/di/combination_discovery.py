"""Pure-Python factor-pair discovery for Data Intelligence decisions."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from itertools import combinations
from typing import Any

RESERVED_FACTOR_KEYS = {"entity_id", "metadata"}
CORRECT_OUTCOMES = {"confirmed", "correct", "success"}
INCORRECT_OUTCOMES = {"override", "overridden", "incorrect", "failure"}


@dataclass(frozen=True)
class CombinationCandidate:
    factor_a: str
    factor_b: str
    correlation: float
    p_value: float | None
    p_value_method: str
    sample_size: int
    accuracy_when_aligned: float | None
    accuracy_when_misaligned: float | None
    lift_pp: float
    description: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscoveryReport:
    total_pairs_tested: int
    significant_pairs: int
    candidates: list[CombinationCandidate]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["candidates"] = [candidate.to_dict() for candidate in self.candidates]
        return payload


@dataclass(frozen=True)
class _NormalizedDecision:
    factors: dict[str, float]
    is_correct: bool


class CombinationDiscoveryEngine:
    def __init__(
        self,
        min_sample: int = 30,
        correlation_threshold: float = 0.25,
        p_threshold: float = 0.05,
        lift_threshold_pp: float = 5.0,
        p_value_min_sample: int = 30,
        max_candidates: int = 20,
    ) -> None:
        self.min_sample = max(int(min_sample), 1)
        self.correlation_threshold = abs(float(correlation_threshold))
        self.p_threshold = max(float(p_threshold), 0.0)
        self.lift_threshold_pp = abs(float(lift_threshold_pp))
        self.p_value_min_sample = max(int(p_value_min_sample), 1)
        self.max_candidates = max(int(max_candidates), 0)

    def discover(
        self,
        decisions: list[dict[str, Any]],
        factor_names: list[str] | None = None,
    ) -> DiscoveryReport:
        warnings: list[str] = []
        if not decisions:
            return DiscoveryReport(
                total_pairs_tested=0,
                significant_pairs=0,
                candidates=[],
                warnings=["no_decisions"],
            )

        normalized: list[_NormalizedDecision] = []
        missing_factor_rows = 0
        missing_correctness_rows = 0
        for decision in decisions:
            factors = _normalize_factors(decision, factor_names)
            correctness = _normalize_correctness(decision)
            if len(factors) < 2:
                missing_factor_rows += 1
            if correctness is None:
                missing_correctness_rows += 1
            if len(factors) >= 2 and correctness is not None:
                normalized.append(_NormalizedDecision(factors=factors, is_correct=correctness))

        if missing_factor_rows:
            warnings.append(f"missing_factor_vector_rows={missing_factor_rows}")
        if missing_correctness_rows:
            warnings.append(f"missing_correctness_rows={missing_correctness_rows}")
        if len(normalized) < self.min_sample:
            warnings.append("insufficient_valid_rows")

        names = sorted({name for row in normalized for name in row.factors})
        total_pairs_tested = 0
        candidates: list[CombinationCandidate] = []
        constant_factor_skipped = 0
        constant_target_seen = False

        for factor_a, factor_b in combinations(names, 2):
            pair_rows = [
                row
                for row in normalized
                if factor_a in row.factors and factor_b in row.factors
            ]
            sample_size = len(pair_rows)
            total_pairs_tested += 1
            if sample_size < self.min_sample:
                continue

            values_a = [row.factors[factor_a] for row in pair_rows]
            values_b = [row.factors[factor_b] for row in pair_rows]
            target = [1.0 if row.is_correct else 0.0 for row in pair_rows]

            z_a = _standardize(values_a)
            z_b = _standardize(values_b)
            if z_a is None or z_b is None:
                constant_factor_skipped += 1
                continue

            pair_signal = [left * right for left, right in zip(z_a, z_b, strict=True)]
            correlation, p_value, p_value_method, corr_warnings = self._compute_correlation(pair_signal, target)
            if correlation is None:
                if "constant_target" in corr_warnings:
                    constant_target_seen = True
                continue

            aligned_accuracy, misaligned_accuracy, lift_pp, lift_warnings = _lift_for_pair(
                pair_rows,
                factor_a,
                factor_b,
            )
            candidate_warnings = [*corr_warnings, *lift_warnings]
            if aligned_accuracy is None or misaligned_accuracy is None:
                continue

            if (
                abs(correlation) >= self.correlation_threshold
                and p_value is not None
                and p_value <= self.p_threshold
                and abs(lift_pp) >= self.lift_threshold_pp
            ):
                candidate = CombinationCandidate(
                    factor_a=factor_a,
                    factor_b=factor_b,
                    correlation=correlation,
                    p_value=p_value,
                    p_value_method=p_value_method,
                    sample_size=sample_size,
                    accuracy_when_aligned=aligned_accuracy,
                    accuracy_when_misaligned=misaligned_accuracy,
                    lift_pp=lift_pp,
                    description="",
                    warnings=candidate_warnings,
                )
                candidates.append(
                    CombinationCandidate(
                        **{**candidate.to_dict(), "description": self._generate_description(candidate)}
                    )
                )

        if constant_factor_skipped:
            warnings.append(f"constant_factor_skipped={constant_factor_skipped}")
        if constant_target_seen:
            warnings.append("constant_correctness_target")
        if candidates:
            warnings.append("approximate_p_values")

        candidates.sort(
            key=lambda candidate: (
                -abs(candidate.lift_pp),
                -abs(candidate.correlation),
                candidate.factor_a,
                candidate.factor_b,
            )
        )
        limited = candidates[: self.max_candidates]
        return DiscoveryReport(
            total_pairs_tested=total_pairs_tested,
            significant_pairs=len(limited),
            candidates=limited,
            warnings=warnings,
        )

    def _compute_correlation(
        self,
        x: list[float],
        y: list[float],
    ) -> tuple[float | None, float | None, str, list[str]]:
        warnings: list[str] = []
        r = _pearson(x, y)
        if r is None:
            if _is_constant(y):
                warnings.append("constant_target")
            else:
                warnings.append("constant_signal")
            return None, None, "not_computable", warnings
        if len(x) < self.p_value_min_sample:
            warnings.append("insufficient_sample_for_asymptotic_p")
            return r, None, "insufficient_sample_for_asymptotic_p", warnings

        bounded_r = max(min(r, 0.999999), -0.999999)
        z_value = math.atanh(bounded_r) * math.sqrt(max(len(x) - 3, 1))
        p_value = math.erfc(abs(z_value) / math.sqrt(2.0))
        warnings.append("approximate_p_value")
        return r, p_value, "fisher_z_normal_approx", warnings

    def _generate_description(self, candidate: CombinationCandidate) -> str:
        aligned = _format_percent(candidate.accuracy_when_aligned)
        misaligned = _format_percent(candidate.accuracy_when_misaligned)
        return (
            f"When {candidate.factor_a} and {candidate.factor_b} are both above their medians, "
            f"observed accuracy is {aligned} versus {misaligned} otherwise. "
            f"Observed lift is {candidate.lift_pp:.1f}pp over {candidate.sample_size} "
            "verified decisions. This is discovery evidence, not causal proof."
        )


def discover_combinations(
    decisions: list[dict[str, Any]],
    *,
    min_sample_size: int = 30,
    alpha: float = 0.05,
    min_abs_correlation: float = 0.25,
    max_candidates: int = 20,
) -> DiscoveryReport:
    engine = CombinationDiscoveryEngine(
        min_sample=min_sample_size,
        correlation_threshold=min_abs_correlation,
        p_threshold=alpha,
        max_candidates=max_candidates,
    )
    return engine.discover(decisions)


def _normalize_factors(
    decision: dict[str, Any],
    factor_names: list[str] | None,
) -> dict[str, float]:
    for field_name in ("factors", "factor_values"):
        value = decision.get(field_name)
        if isinstance(value, dict):
            return _numeric_factor_dict(value)

    metadata = decision.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    vector = decision.get("factor_vector")
    names = factor_names or _factor_names(decision, metadata)
    if vector is None:
        vector = metadata.get("factor_vector")
        names = factor_names or _factor_names(metadata, metadata)
    return _numeric_vector(vector, names)


def _numeric_factor_dict(values: dict[Any, Any]) -> dict[str, float]:
    factors: dict[str, float] = {}
    for name, value in values.items():
        key = str(name)
        if key in RESERVED_FACTOR_KEYS:
            continue
        numeric = _safe_float(value)
        if numeric is not None:
            factors[key] = numeric
    return factors


def _factor_names(primary: dict[str, Any], metadata: dict[str, Any]) -> list[str] | None:
    for source in (primary, metadata):
        names = source.get("factor_names")
        if isinstance(names, list) and names:
            return [str(name) for name in names]
    return None


def _numeric_vector(value: Any, factor_names: list[str] | None) -> dict[str, float]:
    if not isinstance(value, (list, tuple)):
        return {}
    numeric_values: list[float] = []
    for item in value:
        numeric = _safe_float(item)
        if numeric is None:
            return {}
        numeric_values.append(numeric)
    names = factor_names or [f"factor_{index}" for index in range(len(numeric_values))]
    if len(names) != len(numeric_values):
        names = [f"factor_{index}" for index in range(len(numeric_values))]
    return dict(zip(names, numeric_values, strict=True))


def _normalize_correctness(decision: dict[str, Any]) -> bool | None:
    for name in ("is_correct", "correct", "verified_correct"):
        value = decision.get(name)
        parsed = _boolish(value)
        if parsed is not None:
            return parsed

    outcome = decision.get("outcome")
    if isinstance(outcome, str):
        lowered = outcome.strip().lower()
        if lowered in CORRECT_OUTCOMES:
            return True
        if lowered in INCORRECT_OUTCOMES:
            return False

    actual = decision.get("actual_action")
    recommended = decision.get("recommended_action")
    if actual not in (None, "") and recommended not in (None, ""):
        return str(actual) == str(recommended)
    return None


def _boolish(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _standardize(values: list[float]) -> list[float] | None:
    mean = sum(values) / len(values)
    centered = [value - mean for value in values]
    denom = math.sqrt(sum(value * value for value in centered))
    if denom == 0:
        return None
    return [value / denom for value in centered]


def _pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        return None
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)
    centered_x = [value - mean_x for value in x]
    centered_y = [value - mean_y for value in y]
    denom_x = sum(value * value for value in centered_x)
    denom_y = sum(value * value for value in centered_y)
    if denom_x == 0 or denom_y == 0:
        return None
    numerator = sum(left * right for left, right in zip(centered_x, centered_y, strict=True))
    return numerator / math.sqrt(denom_x * denom_y)


def _is_constant(values: list[float]) -> bool:
    return not values or all(value == values[0] for value in values)


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _lift_for_pair(
    rows: list[_NormalizedDecision],
    factor_a: str,
    factor_b: str,
) -> tuple[float | None, float | None, float, list[str]]:
    median_a = _median([row.factors[factor_a] for row in rows])
    median_b = _median([row.factors[factor_b] for row in rows])
    aligned_indexes = {
        index
        for index, row in enumerate(rows)
        if row.factors[factor_a] >= median_a and row.factors[factor_b] >= median_b
    }
    aligned = [row for index, row in enumerate(rows) if index in aligned_indexes]
    misaligned = [row for index, row in enumerate(rows) if index not in aligned_indexes]
    if not aligned or not misaligned:
        return None, None, 0.0, ["insufficient_alignment_split"]
    aligned_accuracy = _accuracy(aligned)
    misaligned_accuracy = _accuracy(misaligned)
    lift_pp = (aligned_accuracy - misaligned_accuracy) * 100.0
    return aligned_accuracy, misaligned_accuracy, lift_pp, []


def _accuracy(rows: list[_NormalizedDecision]) -> float:
    return sum(1 for row in rows if row.is_correct) / len(rows)


def _format_percent(value: float | None) -> str:
    if value is None:
        return "unavailable"
    return f"{value * 100:.1f}%"
