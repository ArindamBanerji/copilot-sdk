"""
Implied correlation / dispersion (borrowing B8). Requires an options chain.

Why this module exists
----------------------
With single-stock and index implied vols available, the same basket-variance
identity used for realized correlation (correlation.py) yields the market-
standard IMPLIED correlation. Comparing implied vs realized correlation gives
the dispersion signal -- a forward-looking crowding / correlation-risk gauge no
journal tool offers, and the options-aware upgrade path for T18/T20.

Dependencies: numpy only.

References
----------
Bloch (2016) sec 7.6.22 (implied correlation), sec 5.4.6.3 (dispersion relative
value).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class DispersionSignal:
    implied_correlation: float
    realized_correlation: float
    dispersion_gap: float          # implied - realized ; high => dispersion setup


def implied_correlation(index_iv: float, constituent_ivs, weights) -> float:
    """Market-standard implied correlation from the basket-variance identity:

        rho_imp = (sigma_I^2 - sum_i w_i^2 sigma_i^2)
                  / (2 sum_{i<j} w_i w_j sigma_i sigma_j)

    with sigma_I the index implied vol and sigma_i the constituent implied vols.
    """
    sig = np.asarray(constituent_ivs, dtype=float)
    w = np.asarray(weights, dtype=float)
    own = np.sum(w ** 2 * sig ** 2)
    n = len(w)
    cross = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            cross += w[i] * w[j] * sig[i] * sig[j]
    if cross <= 0:
        return float("nan")
    rho = (index_iv ** 2 - own) / (2 * cross)
    return float(np.clip(rho, -1.0, 1.0))


def dispersion_signal(index_iv: float, constituent_ivs, weights,
                      realized_correlation: float) -> DispersionSignal:
    """Implied vs realized correlation. `realized_correlation` comes from
    correlation.effective_correlation(...).rho_bar on the same book."""
    rho_imp = implied_correlation(index_iv, constituent_ivs, weights)
    gap = (rho_imp - realized_correlation
           if np.isfinite(rho_imp) and np.isfinite(realized_correlation)
           else float("nan"))
    return DispersionSignal(rho_imp, float(realized_correlation), gap)
