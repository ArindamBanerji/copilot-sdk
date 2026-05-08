"""Factor noise fingerprint computation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FactorFingerprint:
    name: str
    sigma: float
    weight: float
    interpretation: str


@dataclass(frozen=True)
class FingerprintResult:
    factors: list[FactorFingerprint]
    overall_win_rate: float
    per_category_precision: dict[str, float]
    decisions_analyzed: int


def compute_fingerprint(decisions: list[dict], factor_names: list[str]) -> FingerprintResult:
    """Compute factor precision fingerprints from verified decisions."""

    if len(decisions) < 5:
        return FingerprintResult(
            factors=[
                FactorFingerprint(
                    name=name,
                    sigma=0.5,
                    weight=0.0,
                    interpretation="insufficient data",
                )
                for name in factor_names
            ],
            overall_win_rate=0.0,
            per_category_precision={},
            decisions_analyzed=len(decisions),
        )

    vectors = np.asarray([d["factor_vector"] for d in decisions], dtype=np.float64)
    if vectors.ndim != 2 or vectors.shape[1] != len(factor_names):
        raise ValueError("decision factor vectors must match factor_names length")

    correct_mask = np.asarray([bool(d.get("is_correct", False)) for d in decisions])
    correct_vectors = vectors[correct_mask]
    incorrect_vectors = vectors[~correct_mask]

    sigmas: list[float] = []
    for index in range(len(factor_names)):
        correct_sigma = _group_sigma(correct_vectors[:, index])
        incorrect_sigma = _group_sigma(incorrect_vectors[:, index])
        sigmas.append(max((correct_sigma + incorrect_sigma) / 2.0, 0.01))

    raw_weights = np.asarray([1.0 / (sigma**2) for sigma in sigmas], dtype=np.float64)
    max_weight = float(raw_weights.max()) if raw_weights.size else 1.0
    normalized = raw_weights / max_weight if max_weight > 0 else raw_weights

    fingerprints = [
        FactorFingerprint(
            name=name,
            sigma=round(float(sigma), 3),
            weight=round(float(weight), 3),
            interpretation=_interpret_sigma(float(sigma)),
        )
        for name, sigma, weight in zip(factor_names, sigmas, normalized)
    ]

    return FingerprintResult(
        factors=fingerprints,
        overall_win_rate=round(float(correct_mask.mean()), 3),
        per_category_precision=_per_category_precision(decisions),
        decisions_analyzed=len(decisions),
    )


def _group_sigma(values: np.ndarray) -> float:
    if values.size < 3:
        return 0.5
    return float(np.std(values, ddof=0))


def _interpret_sigma(sigma: float) -> str:
    if sigma < 0.10:
        return "clean"
    if sigma < 0.20:
        return "moderate"
    return "noisy"


def _per_category_precision(decisions: list[dict]) -> dict[str, float]:
    by_category: dict[str, list[bool]] = {}
    for decision in decisions:
        category = str(decision["category"])
        by_category.setdefault(category, []).append(bool(decision.get("is_correct", False)))

    return {
        category: round(sum(values) / len(values), 3)
        for category, values in by_category.items()
        if len(values) >= 3
    }
