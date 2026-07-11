"""Auxiliary options analytics factors.

These factors are intentionally separate from the Trading scorer factor vector.
They describe options context for explanations and UI surfaces only.
"""

from __future__ import annotations

from datetime import date, datetime
from math import log
from typing import Any

from ci_trading.quant import IVRVFactor as QuantIVRVFactor

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


class _IVRVRatioFactorLegacy:
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


class IVRVRatioFactor:
    """Model-free IV/RV factor wrapper preserving the existing factor key."""

    def __init__(self) -> None:
        self._quant = QuantIVRVFactor()
        self._legacy = _IVRVRatioFactorLegacy()

    def compute(self, context: dict[str, Any]) -> float:
        ticker = _value(context, "ticker", "symbol", "underlying")
        quant_context = self._quant_context(context, ticker)
        if quant_context.get("option_chain") is not None and quant_context.get("ohlc") is not None:
            return _clamp(self._quant.compute(str(ticker or ""), quant_context))

        if _value(context, "implied_volatility", "iv", "impliedVolatility") is not None or _value(
            context,
            "realized_volatility",
            "rv",
            "realizedVolatility",
        ) is not None:
            return self._legacy.compute(context)

        return _clamp(self._quant.compute(str(ticker or ""), quant_context))

    def _quant_context(self, context: dict[str, Any], ticker: Any) -> dict[str, Any]:
        quant_context = {
            "option_chain": _value(context, "option_chain", "optionChain"),
            "ohlc": _value(context, "ohlc"),
            "vrp_history": _value(context, "vrp_history", "vrpHistory"),
        }
        if quant_context["option_chain"] is not None and quant_context["ohlc"] is not None:
            return quant_context
        fetched = _fetch_quant_ivrv_context(ticker)
        for key, value in fetched.items():
            if quant_context.get(key) is None:
                quant_context[key] = value
        return quant_context


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


def _fetch_quant_ivrv_context(ticker: Any) -> dict[str, Any]:
    if not YFINANCE_AVAILABLE or yf is None or not ticker:
        return {}
    try:
        instrument = yf.Ticker(str(ticker).upper())
        history = instrument.history(period="90d")
        if history is None or getattr(history, "empty", False):
            return {}
        ohlc = history.rename(columns={column: str(column).lower() for column in history.columns})
        required = {"open", "high", "low", "close"}
        if not required.issubset(set(ohlc.columns)):
            return {}
        options = getattr(instrument, "options", None) or []
        if not options:
            return {"ohlc": ohlc[list(required)]}
        expiry = str(options[0])
        chain = instrument.option_chain(expiry)
        calls = getattr(chain, "calls", None)
        puts = getattr(chain, "puts", None)
        option_chain = _option_chain_payload(calls, puts, ohlc, expiry)
        return {"option_chain": option_chain, "ohlc": ohlc[["open", "high", "low", "close"]]}
    except Exception:
        return {}


def _option_chain_payload(calls: Any, puts: Any, ohlc: Any, expiry: str) -> dict[str, Any] | None:
    if calls is None or puts is None:
        return None
    try:
        call_prices = _prices_by_strike(calls)
        put_prices = _prices_by_strike(puts)
        strikes = sorted(set(call_prices).intersection(put_prices))
        if len(strikes) < 3:
            return None
        close_values = ohlc["close"].dropna()
        if close_values.empty:
            return None
        expiry_date = datetime.fromisoformat(expiry).date()
        days_to_expiry = max((expiry_date - date.today()).days, 1)
        return {
            "strikes": strikes,
            "calls": [call_prices[strike] for strike in strikes],
            "puts": [put_prices[strike] for strike in strikes],
            "forward": float(close_values.iloc[-1]),
            "r": 0.0,
            "T": days_to_expiry / 365.0,
        }
    except Exception:
        return None


def _prices_by_strike(frame: Any) -> dict[float, float]:
    prices: dict[float, float] = {}
    if "strike" not in frame:
        return prices
    for _, row in frame.iterrows():
        strike = _number(row.get("strike"))
        price = _number(row.get("lastPrice"))
        bid = _number(row.get("bid"))
        ask = _number(row.get("ask"))
        if (price is None or price <= 0) and bid is not None and ask is not None and bid >= 0 and ask > 0:
            price = (bid + ask) / 2.0
        if strike is not None and strike > 0 and price is not None and price > 0:
            prices[float(strike)] = float(price)
    return prices


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
