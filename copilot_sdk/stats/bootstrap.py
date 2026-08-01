"""Clustering-aware dispersion diagnostics for conservation quality series."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class DispersionDiagnostic:
    mean: float
    iid_se: float                 # naive s/sqrt(n)
    block_se: float               # block-bootstrap SE of the mean
    inflation: float              # block_se / iid_se ; >1 => clustering matters
    n: int


def block_bootstrap_mean_se(q: Any, block: int = 20, n_boot: int = 2000,
                            seed: int | None = 0) -> DispersionDiagnostic:
    """Stationary (circular) block-bootstrap SE of the mean of q.

    q     : 1-D array-like of the rolling quality score (or per-trade
            verification scores) over the conservation window.
    block : expected block length (~ persistence horizon; 20 is a reasonable
            default for daily-ish trade cadence).
    """
    x = np.asarray(q, dtype=float).reshape(-1)
    x = x[~np.isnan(x)]
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
            length = rng.geometric(1.0 / block)
            take = min(length, n - filled)
            idx[filled:filled + take] = (start + np.arange(take)) % n
            filled += take
        means[b] = x[idx].mean()
    block_se = float(means.std(ddof=1))
    inflation = float(block_se / iid_se) if iid_se > 0 else float("nan")
    return DispersionDiagnostic(float(x.mean()), iid_se, block_se, inflation, n)
