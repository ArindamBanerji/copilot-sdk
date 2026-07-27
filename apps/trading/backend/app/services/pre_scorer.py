"""Read-only pre-trade scoring support."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from copilot_sdk.scoring.presets.trading import TradingPreset


@dataclass
class PreScoreResult:
    """Read-only score preview. No Decision is persisted."""

    recommended_action: str
    confidence: float
    probabilities: dict[str, float]
    category: str
    factor_values: dict[str, float]
    similar_trades: list[dict[str, Any]]
    category_accuracy: float
    current_regime: str | None
    regime_accuracy: float | None
    warning: str | None


class PreScorer:
    """Pre-trade decision support. Read-only by construction."""

    def __init__(
        self,
        scorer: Any,
        graph_store: Any,
        regime_classifier: Any | None = None,
        *,
        preset: Any | None = None,
        domain: str = "trading",
    ) -> None:
        self._scorer = scorer
        self._store = graph_store
        self._regime = regime_classifier
        self._preset = preset or TradingPreset()
        self._domain = domain
        shape = self._preset.shape
        self._factor_names = tuple(shape.factor_names)
        self._action_names = tuple(shape.action_names)

    def pre_score(self, category: str, factors: dict[str, float]) -> PreScoreResult:
        """Score a trade without persisting a Decision node."""

        score_read_only = getattr(self._scorer, "score_read_only", None)
        if not callable(score_read_only):
            raise RuntimeError("pre-score requires score_read_only")

        clean_factors = {name: float(factors[name]) for name in self._factor_names}
        result = score_read_only(clean_factors, category)
        probabilities = self._probabilities(getattr(result, "probabilities", []))
        factor_vector = [clean_factors[name] for name in self._factor_names]
        current_regime, _overall_regime_accuracy = self._regime_context()
        category_accuracy = self._category_accuracy(category)
        regime_accuracy = (
            self._regime_accuracy(category, current_regime)
            if current_regime is not None
            else None
        )

        return PreScoreResult(
            recommended_action=str(getattr(result, "action", "")),
            confidence=round(_finite_float(getattr(result, "confidence", 0.0)), 6),
            probabilities=probabilities,
            category=category,
            factor_values=dict(clean_factors),
            similar_trades=self._find_similar(category, factor_vector),
            category_accuracy=category_accuracy,
            current_regime=current_regime,
            regime_accuracy=regime_accuracy,
            warning=self._generate_warning(category, category_accuracy, current_regime, regime_accuracy),
        )

    def _find_similar(
        self,
        category: str,
        factor_vector: list[float],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Find same-category historical decisions by cosine similarity."""

        if _is_zero_vector(factor_vector):
            return []
        decisions = self._all_decisions()
        correctness = self._correctness_by_decision()
        rows: list[dict[str, Any]] = []
        for decision in decisions:
            if str(decision.get("category") or "") != category:
                continue
            candidate = _decision_vector(decision, self._factor_names)
            similarity = _cosine_similarity(factor_vector, candidate)
            if similarity is None:
                continue
            rows.append(
                {
                    "decision_id": decision.get("decision_id"),
                    "similarity": round(similarity, 6),
                    "action": decision.get("recommended_action") or decision.get("action"),
                    "is_correct": correctness.get(str(decision.get("decision_id"))) if decision.get("is_correct") is None else decision.get("is_correct"),
                    "timestamp": decision.get("created_at") or decision.get("timestamp"),
                }
            )
        return sorted(rows, key=lambda row: row["similarity"], reverse=True)[:limit]

    def _category_accuracy(self, category: str) -> float:
        """Return correct / verified total for a category."""

        outcomes = [
            bool(decision.get("is_correct"))
            for decision in self._verified_decisions()
            if str(decision.get("category") or "") == category
        ]
        if not outcomes:
            return 0.0
        return round(sum(1 for value in outcomes if value) / len(outcomes), 4)

    def _regime_context(self) -> tuple[str | None, float | None]:
        """Return current regime and overall accuracy in that regime."""

        regime = self._current_regime()
        if regime is None:
            return None, None
        outcomes = [
            bool(decision.get("is_correct"))
            for decision in self._verified_decisions()
            if _decision_regime(decision) == regime
        ]
        if not outcomes:
            return regime, None
        return regime, round(sum(1 for value in outcomes if value) / len(outcomes), 4)

    def _generate_warning(
        self,
        category: str,
        accuracy: float,
        regime: str | None,
        regime_accuracy: float | None,
    ) -> str | None:
        """Generate a plain-language warning for weak verified history."""

        if regime is not None and regime_accuracy is not None and regime_accuracy < 0.50:
            return (
                f"Your accuracy in {regime} conditions: {_percent(regime_accuracy)}. "
                "Consider reducing size."
            )
        if accuracy < 0.60:
            return f"Your accuracy in {category}: {_percent(accuracy)}. Consider reducing size."
        return None

    def _regime_accuracy(self, category: str, regime: str | None) -> float | None:
        if regime is None:
            return None
        outcomes = [
            bool(decision.get("is_correct"))
            for decision in self._verified_decisions()
            if str(decision.get("category") or "") == category
            and _decision_regime(decision) == regime
        ]
        if not outcomes:
            return None
        return round(sum(1 for value in outcomes if value) / len(outcomes), 4)

    def _current_regime(self) -> str | None:
        if self._regime is None:
            return None
        for method_name in ("current_regime", "get_current_regime"):
            method = getattr(self._regime, method_name, None)
            if not callable(method):
                continue
            try:
                payload = method()
            except Exception:
                return None
            if isinstance(payload, dict):
                return _normalize_regime(payload.get("regime"))
            return _normalize_regime(payload)
        return None

    def _probabilities(self, probabilities: Any) -> dict[str, float]:
        if isinstance(probabilities, dict):
            return {
                str(action): round(_finite_float(probabilities.get(action)), 6)
                for action in self._action_names
            }
        if isinstance(probabilities, (list, tuple)):
            return {
                action: round(_finite_float(probabilities[index]), 6)
                for index, action in enumerate(self._action_names)
                if index < len(probabilities)
            }
        return {}

    def _all_decisions(self) -> list[dict[str, Any]]:
        reader = getattr(self._store, "get_all_decisions", None)
        if not callable(reader):
            return []
        values = reader(domain=self._domain)
        return [value for value in values if isinstance(value, dict)]

    def _verified_decisions(self) -> list[dict[str, Any]]:
        reader = getattr(self._store, "get_verified_decisions", None)
        if not callable(reader):
            return []
        values = reader(domain=self._domain)
        return [value for value in values if isinstance(value, dict)]

    def _correctness_by_decision(self) -> dict[str, bool]:
        return {
            str(decision["decision_id"]): bool(decision.get("is_correct"))
            for decision in self._verified_decisions()
            if decision.get("decision_id") is not None
        }


def _decision_vector(decision: dict[str, Any], factor_names: tuple[str, ...]) -> list[float]:
    vector = decision.get("factor_vector")
    if isinstance(vector, (list, tuple)):
        try:
            values = [float(value) for value in vector]
        except (TypeError, ValueError):
            values = []
        if len(values) >= len(factor_names):
            return values[: len(factor_names)]

    factors = decision.get("factors")
    if isinstance(factors, dict):
        return [_finite_float(factors.get(name)) for name in factor_names]
    return []


def _cosine_similarity(left: list[float], right: list[float]) -> float | None:
    if not left or len(left) != len(right) or _is_zero_vector(left) or _is_zero_vector(right):
        return None
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm <= 0.0 or right_norm <= 0.0:
        return None
    return max(-1.0, min(1.0, dot / (left_norm * right_norm)))


def _is_zero_vector(values: list[float]) -> bool:
    return not values or all(abs(value) <= 1e-12 for value in values)


def _decision_regime(decision: dict[str, Any]) -> str | None:
    candidates: list[Any] = [decision.get("regime"), decision.get("current_regime")]
    for key in ("metadata", "context", "outcome_metadata"):
        value = decision.get(key)
        if isinstance(value, dict):
            candidates.extend([value.get("regime"), value.get("current_regime")])
            nested = value.get("context")
            if isinstance(nested, dict):
                candidates.extend([nested.get("regime"), nested.get("current_regime")])
    for candidate in candidates:
        regime = _normalize_regime(candidate)
        if regime is not None:
            return regime
    return None


def _normalize_regime(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    return text if text in {"trending", "ranging", "volatile"} else None


def _finite_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def _percent(value: float) -> str:
    return f"{round(float(value) * 100)}%"
