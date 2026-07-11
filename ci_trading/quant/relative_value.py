"""
Relative-value framing: percentile-in-rolling-history (borrowing B3).

Why this module exists
----------------------
The product def hard-codes rich/cheap and regime thresholds (IV/RV > 1.5,
VIX > 30, avg correlation > 0.6). Fixed thresholds don't travel across assets
or vol regimes. Bloch's practitioner method (sec 5.4.6.2, "Vol Ratio
Percentile") places a signal in its own rolling historical distribution and
bands it by percentile: <15th = cheap, >85th = rich.

This is also the honest on-ramp to AgentEvolver (F12): percentile bands are
per-asset/per-trader learned boundaries with no black box.

Dependencies: numpy, pandas only.

References
----------
Bloch (2016) sec 5.4.6.2 (volatility surface relative value; vol-ratio
percentile in one-year historical context).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_percentile(series: pd.Series, window: int = 252,
                       min_periods: int | None = None) -> pd.Series:
    """Percentile rank (0-100) of each value within its trailing `window`.

    The rank of the current point = share of the trailing window <= current.
    A value at the 88th percentile is richer than 88% of its own recent history.
    """
    s = series.astype(float)
    mp = min_periods or max(20, window // 4)

    def _rank(x: np.ndarray) -> float:
        cur = x[-1]
        return float(np.mean(x <= cur) * 100.0)

    return s.rolling(window, min_periods=mp).apply(_rank, raw=True)


def band(percentile: float, cheap: float = 15.0, rich: float = 85.0) -> str:
    """Label a percentile as cheap / normal / rich."""
    if not np.isfinite(percentile):
        return "unknown"
    if percentile <= cheap:
        return "cheap"
    if percentile >= rich:
        return "rich"
    return "normal"


def zscore(series: pd.Series, window: int = 252,
           min_periods: int | None = None) -> pd.Series:
    """Rolling z-score -- complementary to percentile when a parametric
    distance is wanted (e.g., for AgentEvolver threshold tuning)."""
    s = series.astype(float)
    mp = min_periods or max(20, window // 4)
    mean = s.rolling(window, min_periods=mp).mean()
    std = s.rolling(window, min_periods=mp).std(ddof=1)
    return (s - mean) / std.replace(0, np.nan)
