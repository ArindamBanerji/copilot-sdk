"""
Realized-volatility estimators for the Trading Copilot (borrowing B1).

Why this module exists
----------------------
The copilot pulls full OHLCV from yfinance but historically estimated
"realized volatility" from *closes only* (close-to-close). Close-to-close is
statistically inefficient and, worse, mishandles overnight gaps -- which is
exactly the signal in earnings trades (T19), where the gap IS the move.

Yang-Zhang (2000) is the minimum-variance OHLC estimator: it is drift-
independent, captures overnight gaps, and is ~8-14x more efficient than
close-to-close (5-10 days of data give what close-to-close needs 20-30 for).

Dependencies: numpy, pandas only.

References
----------
Yang, D. & Zhang, Q. (2000), "Drift-Independent Volatility Estimation Based on
High, Low, Open, and Close Prices", Journal of Business 73(3).
Rogers, L.C.G. & Satchell, S.E. (1991).
Bloch (2016), "A Practical Guide to Quantitative Volatility Trading", sec 7.1.2
(realized variance as the sum of squared log returns -- the swap convention,
which this module improves upon for *forecasting*).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _as_series(x) -> pd.Series:
    return x if isinstance(x, pd.Series) else pd.Series(np.asarray(x, dtype=float))


def close_to_close_var(close, trading_periods: int = TRADING_DAYS) -> float:
    """Annualized close-to-close variance. The swap-settlement convention;
    kept for reference / reconciliation, not recommended for forecasting."""
    close = _as_series(close)
    logret = np.log(close / close.shift(1)).dropna()
    if len(logret) < 2:
        return float("nan")
    return float(logret.var(ddof=1) * trading_periods)


def rogers_satchell_var(open_, high, low, close,
                        trading_periods: int = TRADING_DAYS) -> float:
    """Annualized Rogers-Satchell variance. Drift-robust, uses the intraday
    range, but ignores overnight gaps. Prefer this over Yang-Zhang for 24/7
    or gap-free instruments (crypto/FX) where the overnight term has no meaning.
    """
    open_, high, low, close = map(_as_series, (open_, high, low, close))
    u = np.log(high / open_)     # normalized high
    d = np.log(low / open_)      # normalized low
    c = np.log(close / open_)    # normalized close (open-to-close)
    rs = u * (u - c) + d * (d - c)
    rs = rs.dropna()
    if len(rs) == 0:
        return float("nan")
    return float(rs.mean() * trading_periods)


def yang_zhang_var(open_, high, low, close,
                   trading_periods: int = TRADING_DAYS) -> float:
    """Annualized Yang-Zhang variance.

    sigma_yz^2 = sigma_o^2 + k*sigma_oc^2 + (1-k)*sigma_rs^2
      sigma_o^2  = variance of overnight log-returns  ln(O_t / C_{t-1})
      sigma_oc^2 = variance of open-to-close log-returns ln(C_t / O_t)
      sigma_rs^2 = Rogers-Satchell (mean, not a variance-about-mean)
      k = 0.34 / (1.34 + (n+1)/(n-1))
    """
    open_, high, low, close = map(_as_series, (open_, high, low, close))
    df = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})
    df["prev_close"] = df["close"].shift(1)
    df = df.dropna()
    # guard against non-positive prices (bad ticks / halts) -> log would blow up
    df = df[(df[["open", "high", "low", "close", "prev_close"]] > 0).all(axis=1)]
    n = len(df)
    if n < 3:
        return float("nan")

    o = np.log(df["open"] / df["prev_close"])   # overnight
    c = np.log(df["close"] / df["open"])         # open-to-close
    u = np.log(df["high"] / df["open"])
    dd = np.log(df["low"] / df["open"])
    rs = u * (u - c) + dd * (dd - c)

    var_o = o.var(ddof=1)
    var_oc = c.var(ddof=1)
    var_rs = rs.mean()

    k = 0.34 / (1.34 + (n + 1) / (n - 1))
    yz = var_o + k * var_oc + (1.0 - k) * var_rs
    return float(yz * trading_periods)


def yang_zhang_vol(open_, high, low, close,
                   trading_periods: int = TRADING_DAYS) -> float:
    """Annualized Yang-Zhang volatility (sqrt of variance). 0.20 == 20%/yr."""
    v = yang_zhang_var(open_, high, low, close, trading_periods)
    return float(np.sqrt(v)) if v == v and v >= 0 else float("nan")


def rolling_yang_zhang_vol(ohlc: pd.DataFrame, window: int = 20,
                           trading_periods: int = TRADING_DAYS) -> pd.Series:
    """Rolling annualized Yang-Zhang vol over `window` trading days.

    `ohlc` must have columns: open, high, low, close (case-insensitive). Index
    is preserved; the first `window` rows are NaN.
    """
    cols = {c.lower(): c for c in ohlc.columns}
    missing = {"open", "high", "low", "close"} - set(cols)
    if missing:
        raise KeyError(f"rolling_yang_zhang_vol: OHLC frame missing columns {sorted(missing)}; "
                       f"got {list(ohlc.columns)}")
    o, h, l, c = (ohlc[cols["open"]], ohlc[cols["high"]],
                  ohlc[cols["low"]], ohlc[cols["close"]])
    out = pd.Series(index=ohlc.index, dtype=float)
    for end in range(window, len(ohlc) + 1):
        sl = slice(end - window, end)
        out.iloc[end - 1] = yang_zhang_vol(o.iloc[sl], h.iloc[sl],
                                           l.iloc[sl], c.iloc[sl], trading_periods)
    return out


def overnight_gap_share(open_, high, low, close) -> float:
    """Fraction of total variance that lives in overnight gaps:
    var_o / (var_o + var_rs). High share => this name's risk is gap-driven
    (earnings/macro); reduce overnight exposure and treat T19 as a
    volatility (straddle) rather than directional trade.
    """
    open_, high, low, close = map(_as_series, (open_, high, low, close))
    df = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})
    df["prev_close"] = df["close"].shift(1)
    df = df.dropna()
    if len(df) < 3:
        return float("nan")
    o = np.log(df["open"] / df["prev_close"])
    c = np.log(df["close"] / df["open"])
    u = np.log(df["high"] / df["open"])
    dd = np.log(df["low"] / df["open"])
    rs = (u * (u - c) + dd * (dd - c)).mean()
    var_o = o.var(ddof=1)
    denom = var_o + rs
    return float(var_o / denom) if denom > 0 else float("nan")
