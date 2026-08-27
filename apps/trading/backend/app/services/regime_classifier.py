"""Market regime classifier and verified-outcome performance mapping."""

from __future__ import annotations

from typing import Any, cast

from copilot_sdk.regime import RegimeDetector, RegimePolicy


REGIMES = ("trending", "ranging", "volatile")
MIN_REGIME_DECISIONS = 10


class RegimeClassifier:
    """Market regime detection from VIX + ADX.

    Thresholds from Trading PD §10.4:
      VIX > 30                 -> volatile
      VIX 20-30                -> ranging
      VIX < 20 + ADX > 25      -> trending
      VIX < 20 + ADX <= 25     -> ranging

    Boundary rules:
      VIX = 30 -> ranging
      VIX = 20 -> ranging
      ADX = 25 -> ranging
    """

    def classify(self, vix: float, adx: float) -> str:
        """Return ``trending``, ``ranging``, or ``volatile``."""
        state = RegimeDetector(RegimePolicy(thresholds={
            "volatile": 30.0,
            "ranging": 20.0,
            "trending": 25.0,
            "calm_vix": 0.0,
            "calm_adx": 0.0,
        })).detect({"vix": vix, "adx": adx})
        return cast(str, state.regime)

    def classify_with_confidence(self, vix: float, adx: float) -> dict[str, Any]:
        """Classify regime with boundary-aware confidence metadata."""
        vix_value = _number(vix, 0.0)
        adx_value = _number(adx, 0.0)
        state = RegimeDetector(RegimePolicy(thresholds={
            "volatile": 30.0,
            "ranging": 20.0,
            "trending": 25.0,
            "calm_vix": 0.0,
            "calm_adx": 0.0,
        })).detect({"vix": vix_value, "adx": adx_value})
        distances = [
            abs(vix_value - 30.0),
            abs(vix_value - 20.0),
            abs(adx_value - 25.0),
        ]
        active_distance = _active_regime_distance(vix_value, adx_value)
        return {
            "regime": state.regime,
            "confidence": state.confidence,
            "vix": round(vix_value, 4),
            "adx": round(adx_value, 4),
            "near_boundary": min(distances) <= 2.0,
        }


class RegimePerformanceMapper:
    """Map verified trading outcomes to per-category regime accuracy."""

    def __init__(self, graph_store: Any, preset: Any, *, domain: str = "trading"):
        self._graph_store = graph_store
        self._preset = preset
        self._domain = domain
        self._categories = set(getattr(getattr(preset, "shape", None), "category_names", []) or [])

    def per_regime_accuracy(self) -> dict[str, dict[str, dict[str, float | int]]]:
        """Return {category: {regime: {accuracy, n_decisions}}} for sampled buckets."""
        buckets = self._buckets()
        result: dict[str, dict[str, dict[str, float | int]]] = {}
        for category, regimes in sorted(buckets.items()):
            for regime, outcomes in sorted(regimes.items()):
                if len(outcomes) < MIN_REGIME_DECISIONS:
                    continue
                result.setdefault(category, {})[regime] = {
                    "accuracy": round(sum(1 for value in outcomes if value) / len(outcomes), 4),
                    "n_decisions": len(outcomes),
                }
        return {category: regimes for category, regimes in result.items() if regimes}

    def regime_edge(self, current_regime: str) -> list[dict[str, Any]]:
        """Rank categories by current-regime edge over each category baseline."""
        regime = _normalize_regime(current_regime)
        buckets = self._buckets()
        rows: list[dict[str, Any]] = []
        for category, regimes in sorted(buckets.items()):
            current = regimes.get(regime, [])
            all_outcomes = [value for values in regimes.values() for value in values]
            if len(current) < MIN_REGIME_DECISIONS or not all_outcomes:
                continue
            regime_accuracy = sum(1 for value in current if value) / len(current)
            baseline_accuracy = sum(1 for value in all_outcomes if value) / len(all_outcomes)
            rows.append(
                {
                    "category": category,
                    "regime_accuracy": round(regime_accuracy, 4),
                    "baseline_accuracy": round(baseline_accuracy, 4),
                    "edge": round(regime_accuracy - baseline_accuracy, 4),
                    "n_decisions": len(current),
                }
            )
        return sorted(rows, key=lambda row: row["edge"], reverse=True)

    def regime_recommendation(self, current_regime: str, conservation_status: dict[str, Any]) -> str:
        """Return a concise observation with conservation context."""
        regime = _normalize_regime(current_regime)
        edges = self.regime_edge(regime)
        if not edges:
            return "Observation: verified regime-specific history is insufficient for a sizing comparison."

        positive = next((row for row in edges if row["edge"] > 0), None)
        negative = next((row for row in reversed(edges) if row["edge"] < 0), None)
        parts = [f"Current: {regime} conditions."]

        if positive is not None:
            edge_pp = round(float(positive["edge"]) * 100)
            if _category_is_green(conservation_status, str(positive["category"])):
                parts.append(f"Your edge: {positive['category']} ({edge_pp:+d}pp).")
            else:
                parts.append(f"Observation: {positive['category']} has the strongest observed regime accuracy.")
        if negative is not None:
            edge_pp = round(float(negative["edge"]) * 100)
            parts.append(f"Observation: {negative['category']} has the weakest observed regime accuracy ({edge_pp:+d}pp).")
        return " ".join(parts)

    def _buckets(self) -> dict[str, dict[str, list[bool]]]:
        decisions = self._verified_decisions()
        buckets: dict[str, dict[str, list[bool]]] = {}
        for decision in decisions:
            category = str(decision.get("category") or "").strip()
            if not category or (self._categories and category not in self._categories):
                continue
            regime = _decision_regime(decision)
            if regime is None:
                continue
            buckets.setdefault(category, {}).setdefault(regime, []).append(bool(decision.get("is_correct")))
        return buckets

    def _verified_decisions(self) -> list[dict[str, Any]]:
        reader = getattr(self._graph_store, "get_verified_decisions", None)
        if not callable(reader):
            return []
        values = reader(self._domain)
        return [value for value in values if isinstance(value, dict)]


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
        text = str(candidate or "").strip()
        if text:
            return _normalize_regime(text)
    return None


def _normalize_regime(value: str) -> str:
    regime = str(value or "").strip().lower()
    return regime if regime in REGIMES else "ranging"


def _category_is_green(conservation_status: dict[str, Any], category: str) -> bool:
    if not isinstance(conservation_status, dict):
        return False
    categories = conservation_status.get("categories")
    candidate: Any = None
    if isinstance(categories, dict):
        candidate = categories.get(category)
    if candidate is None:
        candidate = conservation_status.get(category)
    if isinstance(candidate, dict):
        candidate = candidate.get("status") or candidate.get("conservation_status")
    if candidate is None:
        candidate = conservation_status.get("status") or conservation_status.get("conservation_status")
    return str(candidate or "").strip().upper() in {"GREEN", "SAFE", "OK"}


def _number(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _active_regime_distance(vix: float, adx: float) -> float:
    if vix > 30.0:
        return vix - 30.0
    if vix >= 20.0:
        return min(abs(vix - 20.0), abs(30.0 - vix))
    if adx > 25.0:
        return min(20.0 - vix, adx - 25.0)
    return min(20.0 - vix, abs(25.0 - adx))
