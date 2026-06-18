"""DK-aware trust analysis for Trading signals."""

from __future__ import annotations

import math
from typing import Any

from app.factors.registry import ALL_FACTOR_NAMES, TRADING_FACTOR_COMPUTERS, compute_factors


class TrustAnalyzer:
    """Two-signal trust analysis: DK weights in Phase B, variance in Phase A."""

    NOISE_THRESHOLD = 0.30

    def analyze(
        self,
        scorer: Any,
        trades: list[dict[str, Any]],
        category: str | None = None,
    ) -> dict[str, Any]:
        phase = scorer.get_phase()
        dk_weights = scorer.get_dk_weights() if phase == "B" else None
        dk_unavailable = phase == "B" and not dk_weights
        mode = "variance" if dk_unavailable else ("dk" if phase == "B" else "variance")

        if mode == "dk":
            factors = self._dk_analysis(scorer, category, weights=dk_weights)
            per_category = self._all_categories(scorer, weights=dk_weights)
        else:
            factors = self._variance_analysis(trades)
            per_category = None

        weight_key = "dk_weight" if mode == "dk" else "variance_score"
        factors_sorted = sorted(factors, key=lambda item: item.get(weight_key, 0.0), reverse=True)
        for index, factor in enumerate(factors_sorted):
            factor["rank"] = index + 1

        hero_insight = self._hero_insight(factors_sorted, mode)
        if dk_unavailable:
            hero_insight = f"Phase B reached but DK weights not yet available. {hero_insight}"

        categories = self._categories(scorer)
        return {
            "mode": mode,
            "phase": phase,
            "available_categories": categories,
            "factors": factors_sorted,
            "factor_names": list(ALL_FACTOR_NAMES),
            "implemented": list(TRADING_FACTOR_COMPUTERS),
            "top_signal": factors_sorted[0]["name"] if factors_sorted else None,
            "noise_signals": [factor["name"] for factor in factors_sorted if factor.get("is_noise")],
            "hero_insight": hero_insight,
            "per_category": per_category,
            "decisions_until_dk": self._decisions_until_dk(scorer) if mode == "variance" else None,
            "total_trades": len(trades),
            "trust_scores": self._trust_score_map(factors_sorted),
        }

    def _dk_analysis(
        self,
        scorer: Any,
        category: str | None = None,
        weights: list[list[float]] | None = None,
    ) -> list[dict[str, Any]]:
        if weights is None:
            weights = scorer.get_dk_weights()
        if not weights:
            return []
        categories = self._categories(scorer)
        factors = self._factors(scorer)

        if category and category in categories:
            row = weights[categories.index(category)]
        else:
            row = [sum(column) / len(column) for column in zip(*weights)]

        return self._format_weights(row, factors)

    def _all_categories(
        self,
        scorer: Any,
        weights: list[list[float]] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        if weights is None:
            weights = scorer.get_dk_weights()
        if not weights:
            return {}
        categories = self._categories(scorer)
        factors = self._factors(scorer)
        return {
            category: self._format_weights(weights[index], factors)
            for index, category in enumerate(categories)
            if index < len(weights)
        }

    def _format_weights(self, row: list[float], factors: list[str]) -> list[dict[str, Any]]:
        result = []
        for index, name in enumerate(factors):
            weight = float(row[index]) if index < len(row) else 0.0
            result.append(
                {
                    "name": name,
                    "dk_weight": round(weight, 4),
                    "is_noise": weight < self.NOISE_THRESHOLD,
                    "trust_label": self._dk_label(weight),
                }
            )
        return result

    @staticmethod
    def _dk_label(weight: float) -> str:
        if weight >= 0.60:
            return "highly_trusted"
        if weight >= 0.30:
            return "trusted"
        return "noise"

    def _variance_analysis(self, trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
        computed = [compute_factors(trade) for trade in trades[:500]]
        result = []
        for factor in ALL_FACTOR_NAMES:
            values = [float(row.get(factor, 0.5)) for row in computed]
            n_samples = len(values)
            average = sum(values) / n_samples if n_samples else 0.5
            variance = self._population_variance(values)
            sigma = math.sqrt(variance)
            trust_label = self._trust_label(factor, variance, n_samples)
            result.append(
                {
                    "name": factor,
                    "variance": round(variance, 6),
                    "variance_score": round(max(0.0, 1.0 - min(variance / 0.15, 1.0)), 6),
                    "mean": round(average, 6),
                    "n_samples": n_samples,
                    "trust_label": trust_label,
                    "sigma": round(sigma, 6),
                    "is_noise": trust_label in {"noisy", "very_noisy"},
                }
            )
        return result

    def _hero_insight(self, factors: list[dict[str, Any]], mode: str) -> str:
        if not factors:
            return "Insufficient data for trust analysis."

        top = factors[0]
        noise = [factor["name"] for factor in factors if factor.get("is_noise")]

        if mode == "dk":
            message = f"Your most trusted signal is {top['name']}."
            if noise:
                carries = "carry" if len(noise) > 1 else "carries"
                target = "them" if len(noise) > 1 else "it"
                message += (
                    f" {', '.join(noise)} {carries} little signal - "
                    f"DK learned to ignore {target}."
                )
            return message

        message = f"Most consistent factor: {top['name']}."
        if noise:
            shows = "show" if len(noise) > 1 else "shows"
            message += f" {', '.join(noise)} {shows} high variance."
        return message

    def _decisions_until_dk(self, scorer: Any) -> int | None:
        try:
            total = len(scorer.graph_store.get_decisions("trading", limit=10000))
            threshold = getattr(scorer, "_dk_transition_threshold", 200)
            remaining = max(0, int(threshold) - total)
            return remaining if remaining > 0 else None
        except Exception:
            return None

    @staticmethod
    def _population_variance(values: list[float]) -> float:
        if not values:
            return 0.0
        average = sum(values) / len(values)
        return sum((value - average) ** 2 for value in values) / len(values)

    @staticmethod
    def _trust_label(factor: str, variance: float, n_samples: int) -> str:
        if factor not in TRADING_FACTOR_COMPUTERS:
            return "not_computed"
        if n_samples == 0:
            return "insufficient_data"
        if variance < 0.01:
            return "highly_trusted"
        if variance < 0.03:
            return "trusted"
        if variance < 0.08:
            return "moderate"
        if variance < 0.15:
            return "noisy"
        return "very_noisy"

    @staticmethod
    def _trust_score_map(factors: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {str(factor["name"]): dict(factor) for factor in factors}

    @staticmethod
    def _shape(scorer: Any) -> Any | None:
        preset = getattr(scorer, "_preset", None)
        return getattr(preset, "shape", None)

    def _categories(self, scorer: Any) -> list[str]:
        shape = self._shape(scorer)
        return list(getattr(shape, "category_names", []) or [])

    def _factors(self, scorer: Any) -> list[str]:
        shape = self._shape(scorer)
        return list(getattr(shape, "factor_names", []) or list(ALL_FACTOR_NAMES))
