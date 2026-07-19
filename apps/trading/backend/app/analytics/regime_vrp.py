"""Regime-conditioned VRP rich/cheap analytics."""

from __future__ import annotations

import math
from collections import defaultdict
from statistics import NormalDist
from typing import Any

import pandas as pd

from ci_trading.quant import band, model_free_implied_variance, rolling_percentile, variance_risk_premium


MIN_DECISIONS = 30


def compute_regime_vrp(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [_regime_vrp_row(decision) for decision in decisions]
    rows = [row for row in rows if row is not None]
    grouped: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["regime"])].append(row)

    regimes: dict[str, dict[str, Any]] = {}
    for regime, regime_rows in grouped.items():
        values = pd.Series([float(row["vrp"]) for row in regime_rows])
        percentiles = rolling_percentile(values, window=252, min_periods=min(5, len(values)))
        percentile = _finite(percentiles.iloc[-1]) if len(percentiles) else None
        regimes[regime] = {
            "regime": regime,
            "n_decisions": len(regime_rows),
            "current_vrp": round(float(values.iloc[-1]), 6),
            "percentile": round(percentile, 1) if percentile is not None else None,
            "band": band(percentile) if percentile is not None else "unknown",
        }

    n = len(rows)
    day_zero = n < MIN_DECISIONS
    return {
        "regimes": regimes,
        "n_decisions": n,
        "provenance": "real_measured" if not day_zero else "accumulating",
        "substantiation": "T-R" if not day_zero else "T-O",
        "day_zero": day_zero,
        "decisions_until_measured": max(0, MIN_DECISIONS - n),
    }


def _regime_vrp_row(decision: dict[str, Any]) -> dict[str, float | str] | None:
    regime = (
        decision.get("regime")
        or _nested(decision.get("regime_metadata"), "regime")
        or _nested(decision.get("metadata"), "regime")
        or _nested(_nested(decision.get("metadata"), "regime_metadata"), "regime")
    )
    if not regime:
        return None
    implied = _implied_variance(decision)
    realized = _finite(decision.get("realized_variance"))
    if realized is None:
        rv = _finite(decision.get("rv"))
        realized = rv * rv if rv is not None else None
    if implied is None or realized is None:
        return None
    return {"regime": str(regime), "vrp": variance_risk_premium(implied, realized)}


def _nested(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _implied_variance(decision: dict[str, Any]) -> float | None:
    option_chain = decision.get("option_chain") or decision.get("optionChain")
    if isinstance(option_chain, dict):
        result = _model_free_from_chain(option_chain)
        if result is not None:
            return result

    direct = _finite(decision.get("implied_variance"))
    if direct is not None:
        return direct

    iv = _finite(decision.get("iv") or decision.get("vix_proxy") or decision.get("vixProxy"))
    if iv is None:
        return None
    return _model_free_from_vol_proxy(iv)


def _model_free_from_chain(option_chain: dict[str, Any]) -> float | None:
    strikes = option_chain.get("strikes")
    calls = option_chain.get("call_prices") or option_chain.get("calls")
    puts = option_chain.get("put_prices") or option_chain.get("puts")
    forward = _finite(option_chain.get("forward") or option_chain.get("spot"))
    rate = _finite(option_chain.get("rate") or option_chain.get("r")) or 0.0
    tenor = _finite(option_chain.get("tenor") or option_chain.get("T") or option_chain.get("time_to_expiry"))
    if strikes is None or calls is None or puts is None or forward is None or tenor is None:
        return None
    result = model_free_implied_variance(strikes, calls, puts, forward, rate, tenor)
    return _finite(result.implied_variance)


def _model_free_from_vol_proxy(vol: float) -> float | None:
    sigma = vol / 100.0 if vol > 2.0 else vol
    if sigma <= 0:
        return None
    forward = 100.0
    rate = 0.0
    tenor = 30.0 / 365.0
    strikes = [70.0, 80.0, 90.0, 95.0, 100.0, 105.0, 110.0, 120.0, 130.0]
    calls = [_black_scholes(forward, strike, tenor, rate, sigma, call=True) for strike in strikes]
    puts = [_black_scholes(forward, strike, tenor, rate, sigma, call=False) for strike in strikes]
    result = model_free_implied_variance(strikes, calls, puts, forward, rate, tenor)
    return _finite(result.implied_variance)


def _black_scholes(spot: float, strike: float, tenor: float, rate: float, sigma: float, *, call: bool) -> float:
    if tenor <= 0 or sigma <= 0:
        intrinsic = spot - strike if call else strike - spot
        return max(0.0, intrinsic)
    vol_time = sigma * math.sqrt(tenor)
    d1 = (math.log(spot / strike) + (rate + 0.5 * sigma * sigma) * tenor) / vol_time
    d2 = d1 - vol_time
    normal = NormalDist()
    discount = math.exp(-rate * tenor)
    if call:
        return spot * normal.cdf(d1) - strike * discount * normal.cdf(d2)
    return strike * discount * normal.cdf(-d2) - spot * normal.cdf(-d1)


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
