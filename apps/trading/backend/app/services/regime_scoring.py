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
from copilot_sdk.state import invalidate_cache_event

log = logging.getLogger(__name__)


class TradingRegimeScorerProxy:
    def __init__(self, scorer_proxy: Any, monitor: RegimeMonitor) -> None:
        self._scorer_proxy = scorer_proxy
        self._monitor = monitor
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
        _install_conservation_throttle(scorer, self._monitor)
        scorer._regime_break_active = self._monitor.is_regime_break
        return scorer

    def conservation_status_adjuster(self, payload: dict[str, Any]) -> dict[str, Any]:
        return apply_conservation_tightening(payload, self._monitor)

    def score(
        self,
        factors: dict[str, float],
        category: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        regime_context = build_regime_context(factors, metadata)
        event = self._monitor.record(str(regime_context["regime"]))
        if event == "regime_break":
            log.warning(
                "Regime break detected: %s -> %s",
                self._monitor.previous_regime,
                self._monitor.current_regime,
            )
            invalidate_cache_event("trading", "regime_break")
        tagged_metadata = dict(metadata or {})
        tagged_metadata["regime_metadata"] = {
            **regime_context,
            "tagged_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        result = self._scorer_proxy.score(factors, category, metadata=tagged_metadata)
        payload = asdict(result) if is_dataclass(result) else dict(result)
        payload["regime_context"] = dict(regime_context)
        return payload


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


def _install_conservation_throttle(scorer: Any, monitor: RegimeMonitor) -> None:
    if getattr(scorer, "_trading_regime_throttle_installed", False):
        return
    original = getattr(scorer, "_conservation_pause", None)
    if not callable(original):
        return

    def throttled_conservation_pause(self: Any) -> dict[str, Any] | None:
        pause = original()
        if not monitor.is_regime_break:
            return pause
        if pause is None:
            return None
        theta_min = _finite_or_none(pause.get("theta_min"))
        if theta_min is not None:
            pause = dict(pause)
            pause["theta_min"] = theta_min * monitor.tightening_multiplier
            pause["regime_break_active"] = True
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
