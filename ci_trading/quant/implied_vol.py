"""
Model-free implied variance and variance risk premium (borrowing B7).

Why this module exists
----------------------
The naive IVRVFactor plan used "ATM implied vol from broker" -- a single point on
the surface. Bloch (sec 7.1.3) shows the variance swap is a log-contract,
statically replicable by a strike-weighted strip of options. That strip IS the
VIX construction and yields a robust FORWARD variance, not one ATM quote.

The variance risk premium VRP = implied_variance - realized_variance (use the
Yang-Zhang RV from realized_vol.py) is the rigorous form of "premium is rich"
(T17). Band it by percentile (relative_value.py), don't threshold it at 1.5.

Requires an options chain at call time (sourced via py_vollib / broker); the
runtime math here is numpy-only.

References
----------
Bloch (2016) sec 7.1 (variance swap, log-contract replication). Carr & Madan
(1998). CBOE VIX white paper (discrete replication used below).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ImpliedVarianceResult:
    implied_variance: float       # annualized, model-free
    implied_vol: float            # sqrt of the above
    forward: float
    n_strikes: int


def model_free_implied_variance(strikes, call_prices, put_prices,
                                forward: float, r: float, T: float
                                ) -> ImpliedVarianceResult:
    """Discrete model-free implied variance (VIX methodology) for one expiry.

        sigma^2 = (2 e^{rT}/T) * sum_i (dK_i / K_i^2) * Q(K_i)
                  - (1/T) * (F/K0 - 1)^2

    where Q(K_i) is the price of the OUT-OF-THE-MONEY option at strike K_i
    (put for K_i < F, call for K_i > F; average of put & call at the strike
    straddling F), K0 is the first strike <= F, and dK_i is the central spacing
    (K_{i+1}-K_{i-1})/2 (one-sided at the ends).

    Parameters
    ----------
    strikes      : increasing array of strikes.
    call_prices  : call mid prices aligned to `strikes`.
    put_prices   : put mid prices aligned to `strikes`.
    forward      : forward price F for the expiry.
    r            : risk-free rate (cont. comp.).
    T            : time to expiry in years.
    """
    K = np.asarray(strikes, dtype=float)
    C = np.asarray(call_prices, dtype=float)
    P = np.asarray(put_prices, dtype=float)
    order = np.argsort(K)
    K, C, P = K[order], C[order], P[order]
    nK = len(K)
    if nK < 3 or T <= 0:
        return ImpliedVarianceResult(float("nan"), float("nan"), forward, nK)

    # K0 = first strike at or below the forward
    below = K[K <= forward]
    K0 = below[-1] if len(below) else K[0]
    i0 = int(np.where(K == K0)[0][0])

    # OTM option selection: puts below K0, calls above K0, average at K0.
    Q = np.empty(nK)
    Q[:i0] = P[:i0]
    Q[i0 + 1:] = C[i0 + 1:]
    Q[i0] = 0.5 * (C[i0] + P[i0])

    # central strike spacing
    dK = np.empty(nK)
    dK[1:-1] = (K[2:] - K[:-2]) / 2.0
    dK[0] = K[1] - K[0]
    dK[-1] = K[-1] - K[-2]

    disc = np.exp(r * T)
    contrib = (dK / K ** 2) * Q * disc
    var = (2.0 / T) * contrib.sum() - (1.0 / T) * (forward / K0 - 1.0) ** 2
    var = float(var)
    vol = float(np.sqrt(var)) if var > 0 else float("nan")
    return ImpliedVarianceResult(var, vol, float(forward), nK)


def variance_risk_premium(implied_variance: float,
                          realized_variance: float) -> float:
    """VRP = implied - realized (annualized variances). Positive => options
    are rich vs recent realized movement (favors premium selling, T17)."""
    return float(implied_variance - realized_variance)
