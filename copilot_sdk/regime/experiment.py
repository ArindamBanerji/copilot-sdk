"""Deterministic regime-break replay and re-convergence experiment.

The experiment is intentionally synthetic and domain-neutral.  It uses a
small, documented regime geometry rather than customer or market data, so a
report can never be mistaken for measured deployment evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random
from threading import RLock
from typing import Any, Mapping


_GEOMETRY: dict[str, tuple[float, ...]] = {
    "calm": (0.20, 0.20, 0.20, 0.20),
    "ranging": (0.45, 0.50, 0.45, 0.50),
    "trending": (0.70, 0.35, 0.65, 0.40),
    "volatile": (0.90, 0.80, 0.75, 0.90),
}


@dataclass(frozen=True)
class RegimeBreakScenario:
    """A reproducible sequence with one pre/post-regime boundary."""

    pre_regime: str
    post_regime: str
    decisions_per_regime: int
    pre_observations: tuple[tuple[float, ...], ...]
    post_observations: tuple[tuple[float, ...], ...]
    seed: int
    period: str

    @property
    def break_index(self) -> int:
        return self.decisions_per_regime

    @property
    def total_decisions(self) -> int:
        return self.decisions_per_regime * 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "pre_regime": self.pre_regime,
            "post_regime": self.post_regime,
            "decisions_per_regime": self.decisions_per_regime,
            "break_index": self.break_index,
            "total_decisions": self.total_decisions,
            "seed": self.seed,
            "period": self.period,
            "pre_observations": [list(row) for row in self.pre_observations],
            "post_observations": [list(row) for row in self.post_observations],
        }


@dataclass(frozen=True)
class ConvergenceCurve:
    """Per-decision convergence measurements for one experiment arm."""

    arm: str
    regime: str
    accuracies: tuple[float, ...]
    distances: tuple[float, ...]
    decisions_to_threshold: int | None
    final_accuracy: float
    initial_accuracy: float
    threshold: float
    initialized_from_prior_geometry: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "regime": self.regime,
            "accuracies": list(self.accuracies),
            "distances": list(self.distances),
            "decisions_to_threshold": self.decisions_to_threshold,
            "final_accuracy": self.final_accuracy,
            "initial_accuracy": self.initial_accuracy,
            "threshold": self.threshold,
            "initialized_from_prior_geometry": self.initialized_from_prior_geometry,
        }


@dataclass(frozen=True)
class ExperimentReport:
    """JSON-safe comparison of cold-start and regime-indexed recovery."""

    experiment: str
    scenario: dict[str, Any]
    cold_start_curve: ConvergenceCurve
    regime_indexed_curve: ConvergenceCurve
    gamma: float | None
    statistical_test: dict[str, Any]
    convergence_plot_data: dict[str, list[dict[str, float | int]]]
    report_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment": self.experiment,
            "scenario": self.scenario,
            "cold_start_curve": self.cold_start_curve.to_dict(),
            "regime_indexed_curve": self.regime_indexed_curve.to_dict(),
            "gamma": self.gamma,
            "statistical_test": self.statistical_test,
            "convergence_plot_data": self.convergence_plot_data,
            "report_hash": self.report_hash,
        }


def generate_regime_break(
    pre_regime: str,
    post_regime: str,
    decisions_per_regime: int,
    *,
    seed: int = 202003,
    period: str = "2020-03",
) -> RegimeBreakScenario:
    """Generate a deterministic historical-style regime-break replay.

    ``period`` is a provenance label for the scenario (for example
    ``2020-03`` or ``2022``); observations remain synthetic by design.
    """

    count = int(decisions_per_regime)
    if count <= 0:
        raise ValueError("decisions_per_regime must be positive")
    pre = _canonical_regime(pre_regime)
    post = _canonical_regime(post_regime)
    rng = random.Random(seed)
    pre_target = _GEOMETRY[pre]
    post_target = _GEOMETRY[post]
    return RegimeBreakScenario(
        pre_regime=pre,
        post_regime=post,
        decisions_per_regime=count,
        pre_observations=_observations(pre_target, count, rng),
        post_observations=_observations(post_target, count, rng),
        seed=seed,
        period=str(period),
    )


class ReConvergenceExperiment:
    """Run cold-start and regime-indexed arms against one scenario."""

    def __init__(self, *, threshold: float = 0.85, base_eta: float = 0.18) -> None:
        if not 0.0 < threshold <= 1.0:
            raise ValueError("threshold must be in (0, 1]")
        if not 0.0 < base_eta <= 1.0:
            raise ValueError("base_eta must be in (0, 1]")
        self.threshold = float(threshold)
        self.base_eta = float(base_eta)
        self._lock = RLock()

    def run(self, scenario: RegimeBreakScenario, *, cold_start: bool) -> ConvergenceCurve:
        """Run one post-break arm and return its convergence curve."""

        target = _GEOMETRY[scenario.post_regime]
        neutral = tuple(0.0 for _ in target)
        if cold_start or scenario.pre_regime == scenario.post_regime:
            current = neutral
            indexed = False
        else:
            # The closest retained prior geometry is the pre-break geometry.
            # It is a real warm start, but not an oracle copy of the target.
            current = _GEOMETRY[scenario.pre_regime]
            indexed = True
        starting_geometry = current
        observations = scenario.post_observations
        # Use one common denominator for both arms.  Per-arm normalization
        # would erase the warm-start advantage by making each arm's initial
        # error look equally large.
        initial_distance = max(_distance(neutral, target), 1e-12)
        accuracies: list[float] = []
        distances: list[float] = []
        eta = self._learning_rate(scenario.post_regime)
        with self._lock:
            for observation in observations:
                current = _update(current, observation, eta)
                distance = _distance(current, target)
                accuracy = _clamp(1.0 - distance / initial_distance)
                distances.append(round(distance, 8))
                accuracies.append(round(accuracy, 8))
        crossing = next((i + 1 for i, value in enumerate(accuracies) if value >= self.threshold), None)
        initial_accuracy = _clamp(1.0 - _distance(starting_geometry, target) / initial_distance)
        return ConvergenceCurve(
            arm="cold_start" if cold_start else "regime_indexed",
            regime=scenario.post_regime,
            accuracies=tuple(accuracies),
            distances=tuple(distances),
            decisions_to_threshold=crossing,
            final_accuracy=accuracies[-1],
            initial_accuracy=round(initial_accuracy, 8),
            threshold=self.threshold,
            initialized_from_prior_geometry=indexed,
        )

    def report(self, scenario: RegimeBreakScenario) -> ExperimentReport:
        """Run both arms and construct the auditable comparison report."""

        cold = self.run(scenario, cold_start=True)
        indexed = self.run(scenario, cold_start=False)
        gamma = _gamma(cold.decisions_to_threshold, indexed.decisions_to_threshold)
        test = {
            "method": "threshold_crossing_ratio",
            "null": "gamma <= 1",
            "gamma_gt_1": gamma is not None and gamma > 1.0,
            "status": "PASS" if gamma is not None and gamma > 1.0 else "NOT_PROVEN",
            "synthetic": True,
        }
        plot = {
            "cold_start": [
                {"decision": i + 1, "accuracy": value}
                for i, value in enumerate(cold.accuracies)
            ],
            "regime_indexed": [
                {"decision": i + 1, "accuracy": value}
                for i, value in enumerate(indexed.accuracies)
            ],
        }
        body = {
            "experiment": "EXP-REGIME",
            "scenario": scenario.to_dict(),
            "cold_start_curve": cold.to_dict(),
            "regime_indexed_curve": indexed.to_dict(),
            "gamma": gamma,
            "statistical_test": test,
            "convergence_plot_data": plot,
        }
        digest = hashlib.sha256(_json(body).encode("utf-8")).hexdigest()
        return ExperimentReport(
            experiment="EXP-REGIME",
            scenario=scenario.to_dict(),
            cold_start_curve=cold,
            regime_indexed_curve=indexed,
            gamma=gamma,
            statistical_test=test,
            convergence_plot_data=plot,
            report_hash=digest,
        )

    def run_report(self, scenario: RegimeBreakScenario) -> ExperimentReport:
        """Alias for callers that prefer an explicit report-oriented name."""

        return self.report(scenario)

    def _learning_rate(self, regime: str) -> float:
        # Volatile recovery is deliberately slower, preserving the shipped
        # regime-conditioned learning policy while still testing geometry.
        multiplier = {"volatile": 0.5, "calm": 1.5}.get(regime, 1.0)
        return self.base_eta * multiplier


def run_experiment(
    *,
    pre_regime: str = "calm",
    post_regime: str = "volatile",
    decisions_per_regime: int = 250,
    seed: int = 202003,
    period: str = "2020-03",
    threshold: float = 0.85,
) -> ExperimentReport:
    """Convenience entry point for scripts and notebooks."""

    scenario = generate_regime_break(
        pre_regime,
        post_regime,
        decisions_per_regime,
        seed=seed,
        period=period,
    )
    return ReConvergenceExperiment(threshold=threshold).report(scenario)


def _observations(target: tuple[float, ...], count: int, rng: random.Random) -> tuple[tuple[float, ...], ...]:
    return tuple(
        tuple(round(_clamp(value + rng.gauss(0.0, 0.012)), 8) for value in target)
        for _ in range(count)
    )


def _update(current: tuple[float, ...], observation: tuple[float, ...], eta: float) -> tuple[float, ...]:
    return tuple(current_value + eta * (observed - current_value) for current_value, observed in zip(current, observation))


def _distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def _gamma(cold: int | None, indexed: int | None) -> float | None:
    if cold is None or indexed is None or indexed <= 0:
        return None
    return round(cold / indexed, 8)


def _canonical_regime(regime: str) -> str:
    value = str(regime).strip().lower()
    if value not in _GEOMETRY:
        raise ValueError(f"unsupported regime: {regime}")
    return value


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
