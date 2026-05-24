"""Auxiliary options analytics factors.

These factors are intentionally separate from the Trading scorer factor vector.
They describe options context for explanations and UI surfaces only.
"""

from __future__ import annotations

from math import log
from typing import Any

try:  # pragma: no cover - availability is environment dependent
    import py_vollib  # noqa: F401

    VOLLIB_AVAILABLE = True
except Exception:  # pragma: no cover - availability is environment dependent
    py_vollib = None  # type: ignore[assignment]
    VOLLIB_AVAILABLE = False

try:  # pragma: no cover - availability is environment dependent
    import yfinance as yf

    YFINANCE_AVAILABLE = True
except Exception:  # pragma: no cover - availability is environment dependent
    yf = None  # type: ignore[assignment]
    YFINANCE_AVAILABLE = False


OPTIONS_FACTOR_NAMES = (
    "iv_rv_ratio",
    "greeks_exposure",
    "theta_efficiency",
)

SELLING_TERMS = (
    "sell",
    "short",
    "credit",
    "premium",
    "covered",
    "wheel",
    "iron_condor",
    "condor",
)
BUYING_TERMS = ("buy", "long", "debit", "paid", "lottery")
NEUTRAL_TERMS = (
    "neutral",
    "straddle",
    "strangle",
    "iron_condor",
    "condor",
    "butterfly",
    "calendar",
)


class IVRVRatioFactor:
    """Score implied-volatility richness versus realized volatility."""

    def compute(self, context: dict[str, Any]) -> float:
        implied = _number(_value(context, "implied_volatility", "iv", "impliedVolatility"))
        realized = _number(_value(context, "realized_volatility", "rv", "realizedVolatility"))
        if implied is None or realized is None:
            fetched_iv, fetched_rv = self._fetch_iv_rv(_value(context, "ticker"))
            implied = implied if implied is not None else fetched_iv
            realized = realized if realized is not None else fetched_rv
        if implied is None or realized is None or realized <= 0:
            return 0.5

        ratio = implied / realized
        tag = _strategy_text(context)
        if _has_any(tag, SELLING_TERMS):
            return _clamp((ratio - 0.8) / 0.8)
        if _has_any(tag, BUYING_TERMS):
            return _clamp((1.4 - ratio) / 0.8)

        try:
            distance = abs(log(max(ratio, 0.0001)))
        except Exception:
            return 0.5
        return _clamp(0.5 + min(distance, 1.0) * 0.5)

    def _fetch_iv_rv(self, ticker: Any) -> tuple[float | None, float | None]:
        if not YFINANCE_AVAILABLE or yf is None or not ticker:
            return (None, None)
        try:
            instrument = yf.Ticker(str(ticker).upper())
            implied = None
            options = getattr(instrument, "options", None) or []
            if options:
                chain = instrument.option_chain(options[0])
                calls = getattr(chain, "calls", None)
                if calls is not None and "impliedVolatility" in calls:
                    values = [
                        _number(value)
                        for value in calls["impliedVolatility"].tolist()
                    ]
                    values = [value for value in values if value is not None and value > 0]
                    implied = sum(values) / len(values) if values else None

            realized = None
            history = instrument.history(period="45d")
            if history is not None and "Close" in history:
                closes = [_number(value) for value in history["Close"].tolist()]
                closes = [value for value in closes if value is not None and value > 0]
                returns = [
                    (closes[index] / closes[index - 1]) - 1.0
                    for index in range(1, len(closes))
                    if closes[index - 1] > 0
                ]
                if len(returns) >= 2:
                    avg = sum(returns) / len(returns)
                    variance = sum((value - avg) ** 2 for value in returns) / (len(returns) - 1)
                    realized = variance ** 0.5 * (252 ** 0.5)
            return (implied, realized)
        except Exception:
            return (None, None)


class GreeksExposureFactor:
    """Score whether the options greeks match the setup type."""

    def compute(self, context: dict[str, Any]) -> float:
        delta = _number(_value(context, "delta"))
        if delta is None:
            return 0.5
        gamma = abs(_number(_value(context, "gamma")) or 0.0)
        vega = abs(_number(_value(context, "vega")) or 0.0)
        abs_delta = abs(delta)
        tag = _strategy_text(context)
        if _has_any(tag, NEUTRAL_TERMS):
            score = 1.0 - min(abs_delta / 0.50, 1.0)
        else:
            score = min(abs_delta / 0.70, 1.0)
        exposure_penalty = min(gamma * 0.15 + vega * 0.05, 0.20)
        return _clamp(score - exposure_penalty)


class ThetaEfficiencyFactor:
    """Score theta drag/capture relative to option premium and hold period."""

    def compute(self, context: dict[str, Any]) -> float:
        theta = _number(_value(context, "theta_daily", "theta"))
        hold_days = _number(_value(context, "hold_days", "days_to_hold"))
        if theta is None or hold_days is None or hold_days <= 0:
            return 0.5
        tag = _strategy_text(context)
        premium_collected = _number(_value(context, "premium_collected", "credit"))
        premium_paid = _number(_value(context, "premium_paid", "debit"))
        theta_cost = abs(theta) * hold_days
        if _has_any(tag, SELLING_TERMS):
            if premium_collected is None or premium_collected <= 0:
                return 0.5
            return _clamp(theta_cost / premium_collected)
        if premium_paid is None or premium_paid <= 0:
            return 0.5
        return _clamp(1.0 - (theta_cost / premium_paid))


OPTIONS_FACTOR_COMPUTERS = {
    "iv_rv_ratio": IVRVRatioFactor(),
    "greeks_exposure": GreeksExposureFactor(),
    "theta_efficiency": ThetaEfficiencyFactor(),
}


def compute_options_factors(context: dict[str, Any] | None) -> dict[str, float]:
    payload = context if isinstance(context, dict) else {}
    values: dict[str, float] = {}
    for name in OPTIONS_FACTOR_NAMES:
        computer = OPTIONS_FACTOR_COMPUTERS[name]
        try:
            values[name] = _clamp(computer.compute(payload))
        except Exception:
            values[name] = 0.5
    return values


def _value(context: dict[str, Any], *keys: str) -> Any:
    metadata = context.get("metadata") if isinstance(context.get("metadata"), dict) else {}
    options = context.get("options") if isinstance(context.get("options"), dict) else {}
    for key in keys:
        if key in context:
            return context.get(key)
        if key in metadata:
            return metadata.get(key)
        if key in options:
            return options.get(key)
    return None


def _strategy_text(context: dict[str, Any]) -> str:
    fields = (
        _value(context, "strategy_tag", "thesis_type"),
        _value(context, "category"),
        _value(context, "subcategory"),
        _value(context, "notes"),
        _value(context, "direction"),
    )
    return " ".join(str(value or "") for value in fields).lower().replace("-", "_").replace(" ", "_")


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    normalized_terms = [term.lower().replace("-", "_").replace(" ", "_") for term in terms]
    return any(term in text for term in normalized_terms)


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _clamp(value: Any) -> float:
    number = _number(value)
    if number is None:
        return 0.5
    return max(0.0, min(number, 1.0))
