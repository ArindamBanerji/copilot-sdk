"""
Regime detection via long-range dependence (borrowing B2).

Why this module exists
----------------------
The copilot's regime classifier is fixed VIX+ADX thresholds. That has no
*statistical* test of whether a series is actually trending or mean-reverting,
and it only reacts once VIX has already crossed 30.

The Hurst exponent H (rescaled-range / R/S analysis) measures persistence
directly from the price series:
    H ~ 0.5  -> random walk (no exploitable structure)
    H < 0.5  -> anti-persistent / mean-reverting  (favors mean_reversion)
    H > 0.5  -> persistent / trending             (favors trend_following)

Apply R/S to *log returns* to characterize the process (applying it to price
levels trivially returns H~1). The LOCAL Hurst exponent (computed on a sliding
window) level-shifts abruptly around large fluctuations / crashes -- an
early-warning for regime change that fires BEFORE VIX crosses 30. This feeds
the conservation-AMBER triggers so T9/T14 detect the shift in week 1 rather
than "6 weeks later".

Dependencies: numpy, pandas only.

References
----------
Hurst (1951); Mandelbrot (1968); Bloch (2016) sec 2.1.4 (R/S, the Hurst
phenomenon) and 2.1.5.5 (local Holder/Hurst; abrupt fractal-structure shifts
as crash detectors).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _log_returns(x) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x) & (x > 0)]
    return np.diff(np.log(x))


def _anis_lloyd_expected(n: int) -> float:
    """Anis-Lloyd (1976) expected rescaled range under the null H=0.5, with
    Peters' (n-0.5)/n small-sample factor. Used to de-bias the R/S estimate:
    raw R/S analysis is biased UPWARD for short windows (white noise reads
    ~0.6, not 0.5). Subtracting the null expectation's growth re-centers it."""
    i = np.arange(1, n)
    s = np.sum(np.sqrt((n - i) / i))
    return float(((n - 0.5) / n) * (1.0 / np.sqrt(n * np.pi / 2.0)) * s)


def hurst_rs(series, is_returns: bool = False,
             min_window: int = 8, n_scales: int = 12,
             corrected: bool = True) -> float:
    """Hurst exponent via rescaled-range (R/S) analysis, Anis-Lloyd-Peters
    bias-corrected by default.

    Parameters
    ----------
    series : price levels (default) or log-returns if is_returns=True.
    min_window : smallest window size for R/S.
    n_scales : number of log-spaced window sizes to regress over.
    corrected : if True, subtract the Anis-Lloyd null expectation so white
        noise reads H~0.5 (recommended). If False, returns the raw slope.

    Returns H in [0,1]; NaN if the series is too short.

    Validated on synthetic processes:
        i.i.d. returns    -> H ~ 0.50
        positive AR(1)    -> H  > 0.55  (trending / persistent)
        negative AR(1)    -> H  < 0.45  (mean-reverting / anti-persistent)
    """
    r = np.asarray(series, dtype=float) if is_returns else _log_returns(series)
    r = r[np.isfinite(r)]
    N = len(r)
    if N < 2 * min_window:
        return float("nan")

    max_window = N // 2
    scales = np.unique(np.floor(
        np.logspace(np.log10(min_window), np.log10(max_window), n_scales)
    ).astype(int))
    scales = scales[scales >= min_window]
    if len(scales) < 3:
        return float("nan")

    log_n, y_vals = [], []
    for n in scales:
        k = N // n
        if k < 1:
            continue
        rs_vals = []
        for i in range(k):
            w = r[i * n:(i + 1) * n]
            m = w.mean()
            z = np.cumsum(w - m)
            R = z.max() - z.min()
            S = w.std(ddof=1)
            if S > 0 and R > 0:
                rs_vals.append(R / S)
        if rs_vals:
            log_n.append(np.log(n))
            log_rs = np.log(np.mean(rs_vals))
            # de-bias: regress (log RS - log E[RS|H=0.5]) on log n, add 0.5 back
            y_vals.append(log_rs - np.log(_anis_lloyd_expected(n)) if corrected
                          else log_rs)

    if len(log_n) < 3:
        return float("nan")
    slope, _ = np.polyfit(log_n, y_vals, 1)   # numpy OLS; no scipy needed
    return float(slope + 0.5) if corrected else float(slope)


def regime_from_hurst(h: float, band: float = 0.05) -> str:
    """Map a Hurst value to a regime label. `band` is the neutral zone around
    0.5 within which we call it a random walk."""
    if not np.isfinite(h):
        return "unknown"
    if h > 0.5 + band:
        return "trending"
    if h < 0.5 - band:
        return "mean_reverting"
    return "random_walk"


def local_hurst(series, window: int = 100, step: int = 1,
                is_returns: bool = False) -> pd.Series:
    """Rolling Hurst exponent. Returns a Series indexed by the END position of
    each window (so it aligns with 'now')."""
    r = np.asarray(series, dtype=float) if is_returns else _log_returns(series)
    idx, vals = [], []
    for end in range(window, len(r) + 1, step):
        vals.append(hurst_rs(r[end - window:end], is_returns=True))
        idx.append(end)
    return pd.Series(vals, index=idx, name="local_hurst")


def hurst_regime_shift(local_h: pd.Series, lookback: int = 20,
                       z_threshold: float = 2.0) -> pd.Series:
    """Flag abrupt level-shifts in the local Hurst exponent.

    For each point, z-score the current H against the trailing `lookback`
    distribution of H; |z| >= z_threshold => a fractal-structure shift, i.e. a
    regime-change precursor. Returns a boolean Series aligned to local_h.
    """
    h = local_h.astype(float)
    mean = h.rolling(lookback).mean().shift(1)
    std = h.rolling(lookback).std(ddof=1).shift(1)
    z = (h - mean) / std.replace(0, np.nan)
    return (z.abs() >= z_threshold).fillna(False)
