"""
Clustering-aware dispersion for the conservation law (borrowing B4).

Why this module exists
----------------------
Bloch (sec 2.2.1): signed returns show ~no autocorrelation, but ABSOLUTE and
SQUARED returns exhibit strong long-range dependence -- volatility clustering.
The conservation law theta_min = 23.53 / (alpha * V) and its variance bounds
are cleanest under i.i.d. assumptions. When the quality series q clusters
(good runs followed by good runs, bad by bad), the i.i.d. standard error of
the window mean UNDERSTATES true dispersion, and a strategy can read
conservation-GREEN across a calm cluster then blow through theta_min when the
cluster breaks (the T9 "strategy that stopped working" failure).

This module provides a block-bootstrap standard error of the window-mean q that
respects autocorrelation, plus the ratio to the naive i.i.d. SE. Use the
clustering-aware SE (or max of the two) when gating sizing promotion.

Dependencies: numpy, pandas only. This is a diagnostic to feed ConservationMonitor,
not a replacement for it.

References
----------
Bloch (2016) sec 2.2.1 (long memory in absolute/squared returns; tail index
alpha ~ 3-4). Politis & Romano (1994) stationary bootstrap.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class DispersionDiagnostic:
    mean: float
    iid_se: float                 # naive s/sqrt(n)
    block_se: float               # block-bootstrap SE of the mean
    inflation: float              # block_se / iid_se ; >1 => clustering matters
    n: int


def block_bootstrap_mean_se(q, block: int = 20, n_boot: int = 2000,
                            seed: int | None = 0) -> DispersionDiagnostic:
    """Stationary (circular) block-bootstrap SE of the mean of q.

    q     : 1-D array-like of the rolling quality score (or per-trade
            verification scores) over the conservation window.
    block : expected block length (~ persistence horizon; 20 is a reasonable
            default for daily-ish trade cadence).
    """
    x = np.asarray(pd.Series(q, dtype=float).dropna())
    n = len(x)
    if n < 3:
        return DispersionDiagnostic(
            mean=float("nan"),
            iid_se=float("nan"),
            block_se=float("nan"),
            inflation=float("nan"),
            n=n,
        )

    rng = np.random.default_rng(seed)
    iid_se = float(x.std(ddof=1) / np.sqrt(n))

    means = np.empty(n_boot)
    for b in range(n_boot):
        idx = np.empty(n, dtype=int)
        filled = 0
        while filled < n:
            start = rng.integers(0, n)
            length = rng.geometric(1.0 / block)     # random block length
            take = min(length, n - filled)
            idx[filled:filled + take] = (start + np.arange(take)) % n
            filled += take
        means[b] = x[idx].mean()
    block_se = float(means.std(ddof=1))
    inflation = float(block_se / iid_se) if iid_se > 0 else float("nan")
    return DispersionDiagnostic(float(x.mean()), iid_se, block_se, inflation, n)
