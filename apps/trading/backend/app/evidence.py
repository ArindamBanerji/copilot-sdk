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

try:
    from copilot_sdk.scoring.presets.trading import TradingPreset
except Exception:
    TradingPreset = None  # type: ignore[assignment]


FACTOR_DISPLAY = {
    "signal_alignment": "Signal alignment",
    "market_regime": "Regime fit",
    "position_sizing": "Position sizing",
    "timing_quality": "Timing",
    "risk_reward_actual": "Risk/reward",
    "emotional_indicator": "Decision context",
    "signal_confidence": "Signal confidence",
    "options_delta_exposure": "Options delta exposure",
    "options_iv_percentile": "Options IV percentile",
    "options_gamma_risk": "Options gamma risk",
}


def _polarity_value(value: Any) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        name = str(getattr(value, "name", value)).upper()
        if "POSITIVE" in name:
            return 1
        if "NEGATIVE" in name:
            return -1
        return 0
    if numeric > 0:
        return 1
    if numeric < 0:
        return -1
    return 0


def _load_factor_polarities() -> dict[str, int]:
    if TradingPreset is None:
        return {}
    try:
        polarities = getattr(TradingPreset(), "factor_polarities", {}) or {}
    except Exception:
        return {}
    return {str(name): _polarity_value(value) for name, value in polarities.items()}


FACTOR_POLARITIES = _load_factor_polarities()


def _quality(value: Any) -> str:
    score = _number(value, 0.5)
    if score >= 0.80:
        return "strong"
    if score >= 0.60:
        return "moderate"
    if score >= 0.40:
        return "weak"
    return "poor"


def _polarity_quality(factor_name: str, value: Any) -> str:
    score = _number(value, 0.5)
    polarity = FACTOR_POLARITIES.get(factor_name, 0)
    if polarity > 0:
        base = _quality(score)
        if score >= 0.60:
            return f"{base} (favorable)"
        if score < 0.40:
            return f"{base} (unfavorable)"
        return f"{base} (mixed)"
    if polarity < 0:
        if score <= 0.35:
            return "low (favorable)"
        if score >= 0.65:
            return "high (caution)"
        return "moderate"
    return _quality(score)


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
        dk_weights: Mapping[str, Any] | None = None,
    ) -> str:
        category = str(trade.get("category") or "")
        renderer = {
            "trend_following": self._trend_following,
            "mean_reversion": self._mean_reversion,
            "event_driven": self._event_driven,
            "income_strategy": self._income_strategy,
            "scalp_intraday": self._scalp_intraday,
        }.get(category, self._generic)
        text = renderer(trade, factors, action, confidence, context or {}, dk_weights)
        trust_context = self._trust_context(dk_weights)
        if trust_context:
            text = f"{text} {trust_context}"
        negative = self._negative_evidence(factors, action, dk_weights)
        if negative:
            text = f"{text}\n\n{negative}"
        return text

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
        dk_weights: Mapping[str, Any] | None,
    ) -> str:
        return self._base(
            trade,
            action,
            confidence,
            f"Trend-following setup has {self._factor_phrase('signal_alignment', factors, dk_weights)} signal alignment and {self._factor_phrase('market_regime', factors, dk_weights)} regime fit.",
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
        dk_weights: Mapping[str, Any] | None,
    ) -> str:
        return self._base(
            trade,
            action,
            confidence,
            f"Mean-reversion setup has {self._factor_phrase('timing_quality', factors, dk_weights)} timing and {self._factor_phrase('position_sizing', factors, dk_weights)} position sizing.",
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
        dk_weights: Mapping[str, Any] | None,
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
            f"Event: {label}. Event-driven setup has {self._factor_phrase('signal_confidence', factors, dk_weights)} signal confidence and {self._factor_phrase('risk_reward_actual', factors, dk_weights)} risk/reward.",
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
        dk_weights: Mapping[str, Any] | None,
    ) -> str:
        options_text = _options_analytics_text(context.get("options_factors"))
        thesis = (
            f"Income strategy setup has {self._factor_phrase('risk_reward_actual', factors, dk_weights)} risk/reward "
            f"and {self._factor_phrase('position_sizing', factors, dk_weights)} position sizing."
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
        dk_weights: Mapping[str, Any] | None,
    ) -> str:
        return self._base(
            trade,
            action,
            confidence,
            f"Intraday scalp setup has {self._factor_phrase('timing_quality', factors, dk_weights)} timing and {self._factor_phrase('emotional_indicator', factors, dk_weights)} decision context.",
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
        dk_weights: Mapping[str, Any] | None,
    ) -> str:
        return self._base(
            trade,
            action,
            confidence,
            f"Trading setup has {self._factor_phrase('signal_alignment', factors, dk_weights)} signal alignment and {self._factor_phrase('signal_confidence', factors, dk_weights)} signal confidence.",
            context,
            factors,
        )

    def _factor_phrase(
        self,
        factor_name: str,
        factors: Mapping[str, Any],
        dk_weights: Mapping[str, Any] | None = None,
    ) -> str:
        return f"{_polarity_quality(factor_name, factors.get(factor_name))}{_trust_label(factor_name, dk_weights)}"

    def _negative_evidence(
        self,
        factors: Mapping[str, Any],
        action: str,
        dk_weights: Mapping[str, Any] | None = None,
    ) -> str:
        rows: list[str] = []
        for name in ALL_FACTOR_NAMES:
            value = _number(factors.get(name), 0.5)
            if not _works_against(name, value):
                continue
            weight = _optional_float(dk_weights.get(name)) if dk_weights else None
            if dk_weights is not None and (weight is None or weight <= 0.30):
                continue
            label = FACTOR_DISPLAY.get(name, _display_name(name))
            trust = ""
            if weight is not None:
                trust = ", trusted" if weight >= 0.70 else f", weight {weight:.2f}"
            rows.append(f"{label} is {_polarity_quality(name, value)} ({value:.2f}{trust})")
        if not rows:
            return ""
        joined = "; ".join(rows)
        return f"Working against {action}: {joined}. Consider reducing conviction or waiting for confirmation."

    def _trust_context(self, dk_weights: Mapping[str, Any] | None = None) -> str:
        if not dk_weights:
            return ""
        labels: list[str] = []
        for name in ALL_FACTOR_NAMES:
            label = _trust_label(name, dk_weights)
            if label:
                labels.append(f"{FACTOR_DISPLAY.get(name, _display_name(name))} {label}")
        return "Trust context: " + "; ".join(labels) + "." if labels else ""

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


def _trust_label(factor_name: str, dk_weights: Mapping[str, Any] | None = None) -> str:
    if not dk_weights or factor_name not in dk_weights:
        return ""
    weight = _optional_float(dk_weights.get(factor_name))
    if weight is None:
        return ""
    if weight >= 0.70:
        return f" (trusted, weight {weight:.2f})"
    if weight < 0.30:
        return f" (noisy, weight {weight:.2f})"
    return ""


def _works_against(factor_name: str, value: float) -> bool:
    polarity = FACTOR_POLARITIES.get(factor_name, 0)
    if polarity > 0:
        return value < 0.35
    if polarity < 0:
        return value > 0.65
    return False


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
