"""Trading score wrapper that tags decisions with regime context."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import logging
import math
from types import MethodType
from typing import Any

from app.factors.market_regime import classify_regime_context
from app.services.regime import DEFAULT_ADX, DEFAULT_VIX
from app.services.regime_monitor import RegimeMonitor
from copilot_sdk.regime import (
    PerRegimeCentroidTracker,
    RegimeConservation,
    RegimeLearningRate,
    RegimeParameters,
)
from copilot_sdk.state import invalidate_cache_event

log = logging.getLogger(__name__)


class TradingRegimeScorerProxy:
    def __init__(self, scorer_proxy: Any, monitor: RegimeMonitor) -> None:
        self._scorer_proxy = scorer_proxy
        self._monitor = monitor
        self._regime_conservation = RegimeConservation()
        self._regime_learning = RegimeLearningRate()
        self._centroid_tracker = PerRegimeCentroidTracker()
        self.graph_store = scorer_proxy.graph_store

    def __getattr__(self, name: str) -> Any:
        return getattr(self._scorer_proxy, name)

    @property
    def _scorer_instance(self) -> Any:
        return getattr(self._scorer_proxy, "_scorer_instance", None)

    @_scorer_instance.setter
    def _scorer_instance(self, value: Any) -> None:
        setattr(self._scorer_proxy, "_scorer_instance", value)

    def _scorer(self) -> Any:
        scorer = self._scorer_proxy._scorer()
        _install_conservation_throttle(scorer, self._monitor, self._regime_conservation)
        scorer._regime_break_active = self._monitor.is_regime_break
        return scorer

    @property
    def centroid_tracker(self) -> PerRegimeCentroidTracker:
        return self._centroid_tracker

    def conditioned_parameters(self, regime: str, *, theta_min: float = 0.0) -> RegimeParameters:
        return RegimeParameters(
            regime=str(regime or "unknown"),
            theta_min=self._regime_conservation.adjust_theta_min(theta_min, regime),
            penalty_ratio=self._regime_conservation.adjust_penalty_ratio(3.0, regime),
            eta=self._regime_learning.adjust_eta(0.05, regime),
        )

    def conservation_status_adjuster(self, payload: dict[str, Any]) -> dict[str, Any]:
        adjusted = dict(payload)
        regime = str(self._monitor.current_regime or "unknown")
        theta_min = _finite_or_none(adjusted.get("theta_min"))
        if theta_min is not None:
            adjusted["base_theta_min"] = theta_min
            adjusted["theta_min"] = self._regime_conservation.adjust_theta_min(theta_min, regime)
            signal = _finite_or_none(adjusted.get("signal"))
            adjusted["headroom"] = None if signal is None else signal - adjusted["theta_min"]
        adjusted["base_penalty_ratio"] = _finite_or_none(adjusted.get("penalty_ratio")) or 3.0
        adjusted["penalty_ratio"] = self._regime_conservation.adjust_penalty_ratio(
            adjusted["base_penalty_ratio"], regime
        )
        adjusted["regime"] = regime
        adjusted["regime_break_active"] = self._monitor.is_regime_break
        return adjusted

    def score(
        self,
        factors: dict[str, float],
        category: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        regime_context = build_regime_context(factors, metadata)
        regime = str(regime_context["regime"])
        parameters = self.conditioned_parameters(regime)
        scorer = self._scorer()
        scorer._trading_active_regime = regime
        scorer._trading_regime_parameters = parameters.to_dict()
        event = self._monitor.record(str(regime_context["regime"]))
        if event == "regime_break":
            log.warning(
                "Regime break detected: %s -> %s",
                self._monitor.previous_regime,
                self._monitor.current_regime,
            )
            invalidate_cache_event("trading", "regime_break")
        tagged_metadata = dict(metadata or {})
        # Keep the canonical headline regime flat for graph consumers while
        # retaining the richer regime_metadata payload for analytics.
        tagged_metadata["regime_tag"] = str(regime_context["regime"])
        tagged_metadata["regime_metadata"] = {
            **regime_context,
            "tagged_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        _tag_analytics_metadata(tagged_metadata)
        result = self._scorer_proxy.score(factors, category, metadata=tagged_metadata)
        payload = asdict(result) if is_dataclass(result) else dict(result)
        payload["regime_context"] = dict(regime_context)
        payload["regime_parameters"] = parameters.to_dict()
        return payload

    def learn(
        self,
        decision_id: str,
        actual_action: str,
        outcome: str = "confirmed",
        *,
        consolidate: bool = False,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Learn through the live scorer using the decision's regime rate."""
        scorer = self._scorer()
        regime = _decision_regime(self.graph_store, decision_id, context, self._monitor.current_regime)
        parameters = self.conditioned_parameters(regime)
        before: Any = getattr(getattr(scorer, "_scorer", None), "centroids", None)
        before_copy: Any = before.copy() if callable(getattr(before, "copy", None)) else before
        original_preset = getattr(scorer, "_preset", None)
        if original_preset is None:
            return self._scorer_proxy.learn(
                decision_id, actual_action, outcome,
                consolidate=consolidate, context=context,
            )
        scorer._preset = _RegimePresetView(original_preset, parameters, self._regime_learning)
        try:
            result = scorer.learn(
                decision_id,
                actual_action,
                outcome,
                consolidate=consolidate,
                context=context,
            )
        finally:
            scorer._preset = original_preset
        after: Any = getattr(getattr(scorer, "_scorer", None), "centroids", None)
        if before_copy is not None and after is not None:
            self._centroid_tracker.record(regime, before_copy, after)
        return result


def _tag_analytics_metadata(metadata: dict[str, Any]) -> None:
    """Persist read-side analytics inputs without changing scorer factors."""
    analytics = dict(metadata.get("analytics") or {})
    regime_metadata = metadata.get("regime_metadata")
    regime = regime_metadata.get("regime") if isinstance(regime_metadata, dict) else None
    if regime:
        analytics["cluster_id"] = f"regime:{regime}"
        analytics["cluster_method"] = "regime_v1"

    implied_raw = _analytics_input(metadata, "implied_volatility", "iv", "impliedVolatility")
    realized_raw = _analytics_input(metadata, "realized_volatility", "rv", "realizedVolatility")
    implied = _normalize_volatility(implied_raw)
    realized = _normalize_volatility(realized_raw)
    if implied is not None:
        analytics["implied_vol"] = implied
        analytics["implied_vol_raw"] = float(implied_raw)
    if realized is not None:
        analytics["realized_vol"] = realized
        analytics["realized_vol_raw"] = float(realized_raw)
    if implied is not None or realized is not None:
        analytics["vol_unit"] = "annualized_decimal"
        analytics["iv_rv_source"] = "request_input"

    metadata["analytics"] = analytics


def _analytics_input(metadata: dict[str, Any], *keys: str) -> Any:
    containers = (metadata, metadata.get("context"), metadata.get("options"))
    for container in containers:
        if not isinstance(container, dict):
            continue
        for key in keys:
            if key in container:
                return container.get(key)
    return None


def _normalize_volatility(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    # Inputs in [0, 1] are annualized decimals; values above 1 are percentages.
    return number / 100.0 if number > 1.0 else number


def build_regime_context(
    factors: dict[str, float] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = dict(metadata or {})
    factors = factors or {}
    vix = _number(source.get("vix_at_entry") or source.get("vix") or source.get("current_vix"), DEFAULT_VIX)
    trend_strength = _number(
        source.get("trend_strength") or source.get("adx") or source.get("trend_strength_at_entry"),
        DEFAULT_ADX,
    )
    details = classify_regime_context(vix, trend_strength)
    return {
        "regime": str(details.get("regime") or "ranging"),
        "hurst": _finite_or_none(details.get("hurst")),
        "vol_state": details.get("vol_state"),
        "vix_percentile": _finite_or_none(details.get("vix_percentile")),
    }


def _install_conservation_throttle(
    scorer: Any,
    monitor: RegimeMonitor,
    conditioner: RegimeConservation | None = None,
) -> None:
    if getattr(scorer, "_trading_regime_throttle_installed", False):
        return
    original = getattr(scorer, "_conservation_pause", None)
    if not callable(original):
        return
    conservation = conditioner or RegimeConservation()

    def throttled_conservation_pause(self: Any) -> dict[str, Any] | None:
        pause_result: Any = original()
        if pause_result is None:
            return None
        if not isinstance(pause_result, dict):
            return None
        pause = dict(pause_result)
        theta_min = _finite_or_none(pause.get("theta_min"))
        if theta_min is not None:
            regime = str(getattr(self, "_trading_active_regime", monitor.current_regime or "unknown"))
            pause["theta_min"] = conservation.adjust_theta_min(theta_min, regime)
            pause["penalty_ratio"] = conservation.adjust_penalty_ratio(
                _finite_or_none(pause.get("penalty_ratio")) or 3.0, regime
            )
            pause["regime"] = regime
            pause["regime_break_active"] = monitor.is_regime_break
        return pause

    scorer._conservation_pause = MethodType(throttled_conservation_pause, scorer)
    scorer._regime_break_active = monitor.is_regime_break
    scorer._trading_regime_throttle_installed = True


def apply_conservation_tightening(payload: dict[str, Any], monitor: RegimeMonitor) -> dict[str, Any]:
    if not monitor.is_regime_break:
        return payload
    adjusted = dict(payload)
    theta_min = _finite_or_none(adjusted.get("theta_min"))
    if theta_min is not None:
        adjusted["theta_min"] = theta_min * monitor.tightening_multiplier
        signal = _finite_or_none(adjusted.get("signal"))
        adjusted["headroom"] = None if signal is None else signal - adjusted["theta_min"]
    adjusted["regime_break_active"] = True
    return adjusted


def _number(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def _finite_or_none(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


class _RegimePresetView:
    """Read-only preset view with only Trading's runtime rates adjusted."""

    def __init__(self, base: Any, parameters: RegimeParameters, learning: RegimeLearningRate) -> None:
        self._base = base
        self._parameters = parameters
        self._learning = learning

    @property
    def eta_confirm(self) -> float:
        return float(self._learning.adjust_eta(float(self._base.eta_confirm), self._parameters.regime))

    @property
    def eta_override(self) -> float:
        return float(self._learning.adjust_eta(float(self._base.eta_override), self._parameters.regime))

    @property
    def penalty_ratio(self) -> float:
        return float(self._parameters.penalty_ratio)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._base, name)


def _decision_regime(
    graph_store: Any,
    decision_id: str,
    context: dict[str, Any] | None,
    fallback: str | None,
) -> str:
    for source in (context or {},):
        candidate = source.get("regime") or source.get("current_regime")
        if candidate:
            return str(candidate)
    reader = getattr(graph_store, "get_decision", None)
    if callable(reader):
        decision = reader(decision_id, domain="trading")
        if isinstance(decision, dict):
            for source in (decision, decision.get("metadata") or {}):
                if isinstance(source, dict):
                    candidate = source.get("regime") or source.get("regime_tag") or source.get("current_regime")
                    if candidate:
                        return str(candidate)
    return str(fallback or "unknown")
