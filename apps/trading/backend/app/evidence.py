"""Deterministic natural-language evidence for Trading decisions."""

from __future__ import annotations

from typing import Any, Mapping

from app.services.subcategory import get_subcategory

try:
    from app.factors.registry import ALL_FACTOR_NAMES
except Exception:
    ALL_FACTOR_NAMES = (
        "signal_alignment",
        "market_regime",
        "position_sizing",
        "timing_quality",
        "risk_reward_actual",
        "emotional_indicator",
        "signal_confidence",
    )


FACTOR_DISPLAY = {
    "signal_alignment": "Signal alignment",
    "market_regime": "Regime fit",
    "position_sizing": "Position sizing",
    "timing_quality": "Timing",
    "risk_reward_actual": "Risk/reward",
    "emotional_indicator": "Decision context",
    "signal_confidence": "Signal confidence",
}


def _quality(value: Any) -> str:
    score = _number(value, 0.5)
    if score >= 0.80:
        return "strong"
    if score >= 0.60:
        return "moderate"
    if score >= 0.40:
        return "weak"
    return "poor"


def _regime_label(value: Any) -> str:
    return {
        "strong": "aligned with the current regime",
        "moderate": "mostly compatible with the current regime",
        "weak": "only lightly supported by the current regime",
        "poor": "poorly matched to the current regime",
    }[_quality(value)]


def _sizing_label(value: Any) -> str:
    return {
        "strong": "sizing is disciplined",
        "moderate": "sizing is acceptable",
        "weak": "sizing needs caution",
        "poor": "sizing is a material concern",
    }[_quality(value)]


def _emotional_label(value: Any) -> str:
    return {
        "strong": "decision context is clean",
        "moderate": "decision context has manageable pressure",
        "weak": "decision context has caution flags",
        "poor": "decision context has elevated risk",
    }[_quality(value)]


def _emotional_detail(value: Any, context: Mapping[str, Any] | None = None) -> str:
    data = context or {}
    details: list[str] = []

    minutes = _optional_float(data.get("minutes_since_last_trade"))
    if minutes is not None and minutes < 30 and bool(data.get("last_trade_was_loss")):
        details.append("quick re-entry after loss")

    wins = _optional_float(data.get("consecutive_wins"))
    sizing = _optional_float(data.get("size_vs_rolling_avg"))
    if wins is not None and wins >= 3 and sizing is not None and sizing > 1.3:
        details.append("elevated sizing after winning streak")

    if bool(data.get("entry_at_day_extreme")):
        details.append("entry at daily extreme")

    return "; ".join(details) if details else "no flags detected"


class TradingTemplateEngine:
    """Render stable Trading evidence text without external model calls."""

    def render(
        self,
        trade: Mapping[str, Any],
        factors: Mapping[str, Any],
        action: str,
        confidence: float,
        context: Mapping[str, Any] | None = None,
    ) -> str:
        category = str(trade.get("category") or "")
        renderer = {
            "trend_following": self._trend_following,
            "mean_reversion": self._mean_reversion,
            "event_driven": self._event_driven,
            "income_strategy": self._income_strategy,
            "scalp_intraday": self._scalp_intraday,
        }.get(category, self._generic)
        return renderer(trade, factors, action, confidence, context or {})

    def render_factor_breakdown(self, factors: Mapping[str, Any]) -> list[str]:
        ordered = list(ALL_FACTOR_NAMES)
        extras = [key for key in factors if key not in ordered and key in FACTOR_DISPLAY]
        lines: list[str] = []
        for name in [*ordered, *extras]:
            value = _number(factors.get(name), 0.5)
            label = FACTOR_DISPLAY.get(name, _display_name(name))
            lines.append(f"{label}: {value:.2f} ({_quality(value)})")
        return lines

    def render_trust_analysis(self, factor_weights: Mapping[str, Any] | None = None) -> str:
        if not factor_weights:
            return "Trust analysis has insufficient data."
        rows = sorted(
            ((name, _number(weight, 0.0)) for name, weight in factor_weights.items()),
            key=lambda item: (-item[1], item[0]),
        )
        rendered = [
            f"{FACTOR_DISPLAY.get(name, _display_name(name))} {weight:.2f}"
            for name, weight in rows
        ]
        return "Trust weighting: " + "; ".join(rendered) + "."

    def _trend_following(
        self,
        trade: Mapping[str, Any],
        factors: Mapping[str, Any],
        action: str,
        confidence: float,
        context: Mapping[str, Any],
    ) -> str:
        return self._base(
            trade,
            action,
            confidence,
            f"Trend-following setup has {_quality(factors.get('signal_alignment'))} signal alignment and {_regime_label(factors.get('market_regime'))}.",
            context,
            factors,
        )

    def _mean_reversion(
        self,
        trade: Mapping[str, Any],
        factors: Mapping[str, Any],
        action: str,
        confidence: float,
        context: Mapping[str, Any],
    ) -> str:
        return self._base(
            trade,
            action,
            confidence,
            f"Mean-reversion setup has {_quality(factors.get('timing_quality'))} timing and {_sizing_label(factors.get('position_sizing'))}.",
            context,
            factors,
        )

    def _event_driven(
        self,
        trade: Mapping[str, Any],
        factors: Mapping[str, Any],
        action: str,
        confidence: float,
        context: Mapping[str, Any],
    ) -> str:
        subcategory = get_subcategory({
            "category": "event_driven",
            "strategy_tag": trade.get("strategy_tag") or context.get("strategy_tag"),
            "direction": trade.get("direction") or context.get("direction"),
            "notes": trade.get("notes") or context.get("notes"),
            "metadata": trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {},
            "subcategory": trade.get("subcategory") or context.get("subcategory"),
        })
        label = "Volatility play" if subcategory == "volatility" else "Direction play"
        return self._base(
            trade,
            action,
            confidence,
            f"Event: {label}. Event-driven setup has {_quality(factors.get('signal_confidence'))} signal confidence and {_quality(factors.get('risk_reward_actual'))} risk/reward.",
            context,
            factors,
        )

    def _income_strategy(
        self,
        trade: Mapping[str, Any],
        factors: Mapping[str, Any],
        action: str,
        confidence: float,
        context: Mapping[str, Any],
    ) -> str:
        options_text = _options_analytics_text(context.get("options_factors"))
        thesis = (
            f"Income strategy setup has {_quality(factors.get('risk_reward_actual'))} risk/reward "
            f"and {_sizing_label(factors.get('position_sizing'))}."
        )
        if options_text:
            thesis = f"{thesis} {options_text}"
        return self._base(
            trade,
            action,
            confidence,
            thesis,
            context,
            factors,
        )

    def _scalp_intraday(
        self,
        trade: Mapping[str, Any],
        factors: Mapping[str, Any],
        action: str,
        confidence: float,
        context: Mapping[str, Any],
    ) -> str:
        return self._base(
            trade,
            action,
            confidence,
            f"Intraday scalp setup has {_quality(factors.get('timing_quality'))} timing and {_emotional_label(factors.get('emotional_indicator'))}.",
            context,
            factors,
        )

    def _generic(
        self,
        trade: Mapping[str, Any],
        factors: Mapping[str, Any],
        action: str,
        confidence: float,
        context: Mapping[str, Any],
    ) -> str:
        return self._base(
            trade,
            action,
            confidence,
            f"Trading setup has {_quality(factors.get('signal_alignment'))} signal alignment and {_quality(factors.get('signal_confidence'))} signal confidence.",
            context,
            factors,
        )

    def _base(
        self,
        trade: Mapping[str, Any],
        action: str,
        confidence: float,
        thesis: str,
        context: Mapping[str, Any],
        factors: Mapping[str, Any],
    ) -> str:
        ticker = str(trade.get("ticker") or "unknown ticker")
        direction = str(trade.get("direction") or "unknown direction")
        detail = _emotional_detail(factors.get("emotional_indicator"), context)
        return (
            f"{ticker} {direction}: {thesis} "
            f"Recommended action is {action} with {confidence:.0%} confidence. "
            f"Decision context: {detail}."
        )


def _display_name(name: str) -> str:
    return str(name).replace("_", " ").capitalize()


def _number(value: Any, fallback: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    if number != number or number in (float("inf"), float("-inf")):
        return fallback
    return max(0.0, min(number, 1.0))


def _optional_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _options_analytics_text(options_factors: Any) -> str:
    if not isinstance(options_factors, Mapping):
        return ""
    iv_rv = _number(options_factors.get("iv_rv_ratio"), 0.5)
    greeks = _number(options_factors.get("greeks_exposure"), 0.5)
    theta = _number(options_factors.get("theta_efficiency"), 0.5)
    return f"Options analytics-only: IV/RV {iv_rv:.2f}, Greeks {greeks:.2f}, Theta {theta:.2f}."
