"""
Portfolio correlation: effective correlation + tail dependence (B5, B6).

Why this module exists
----------------------
The product's CorrelationMonitor (T18) averages a rolling *Pearson* matrix.
Pearson is a linear, finite-variance measure -- exactly the wrong tool for the
scenario T18 is about ("5 diversified positions become 1 bet when VIX spikes").
Two upgrades, both offline (no options), both reusing the Yang-Zhang leg:

B5 -- Effective (basket) correlation. Invert the portfolio-variance identity to
      recover the single average pairwise correlation of the trader's actual
      book, and the "effective single bet" multiplier that T18 quotes.

B6 -- Tail dependence. Bloch (sec 2.1.3): correlation only measures LINEAR
      dependence; "even negligible correlations can greatly influence tail
      probabilities". Instead of fitting a copula, measure the thing
      directly: correlation conditioned on stress days vs unconditional. The
      gap is the crash-correlation warning, delivered before unconditional
      Pearson catches up.

Dependencies: numpy, pandas only.

References
----------
Bloch (2016) sec 2.1.3 (correlation vs dependence, copulas, Sklar), sec 7.6.1
(portfolio-variance identity), and the ch.7 opener (variance/covariance are not
proper risk measures under multifractal/jump dynamics).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class EffectiveCorrelation:
    rho_bar: float                 # average pairwise realized correlation
    portfolio_vol: float           # realized vol of the actual book
    diversified_vol: float         # sqrt(sum w_i^2 sigma_i^2) -- fully-diversified benchmark
    effective_bet_multiplier: float  # portfolio_vol / diversified_vol
    n_effective_bets: float        # diversification ratio^2


def _avg_offdiag(corr: pd.DataFrame) -> float:
    m = corr.values.astype(float)
    n = m.shape[0]
    if n < 2:
        return float("nan")
    iu = np.triu_indices(n, k=1)
    vals = m[iu]
    vals = vals[np.isfinite(vals)]
    return float(vals.mean()) if len(vals) else float("nan")


def effective_correlation(position_returns: pd.DataFrame,
                          weights) -> EffectiveCorrelation:
    """Recover average pairwise correlation from the basket-variance identity:

        sigma_P^2 = sum_i w_i^2 sigma_i^2 + 2 sum_{i<j} w_i w_j sigma_i sigma_j rho_bar
        => rho_bar = (sigma_P^2 - sum_i w_i^2 sigma_i^2)
                     / (2 sum_{i<j} w_i w_j sigma_i sigma_j)

    `position_returns` : DataFrame of per-position periodic returns (one column
                         per position, aligned by date).
    `weights`          : capital weights per position (any scale; not required
                         to sum to 1 -- they represent fractions of the account,
                         and the portfolio return is their weighted sum).
    """
    w = np.asarray(weights, dtype=float)
    R = position_returns.to_numpy(dtype=float)
    mask = np.isfinite(R).all(axis=1)
    R = R[mask]
    if R.shape[0] < 2 or R.shape[1] != len(w):
        return EffectiveCorrelation(*([float("nan")] * 5))

    sigma = R.std(axis=0, ddof=1)
    port = R @ w
    sigma_P = port.std(ddof=1)

    own = np.sum(w ** 2 * sigma ** 2)
    cross = 0.0
    n = len(w)
    for i in range(n):
        for j in range(i + 1, n):
            cross += w[i] * w[j] * sigma[i] * sigma[j]
    rho_bar = (sigma_P ** 2 - own) / (2 * cross) if cross > 0 else float("nan")
    if np.isfinite(rho_bar):
        rho_bar = float(np.clip(rho_bar, -1.0, 1.0))  # guard estimation noise

    diversified = float(np.sqrt(own))
    mult = float(sigma_P / diversified) if diversified > 0 else float("nan")
    # Diversification ratio = weighted-avg vol / portfolio vol; N_eff = DR^2.
    wavg_vol = float(np.sum(np.abs(w) * sigma))
    dr = wavg_vol / sigma_P if sigma_P > 0 else float("nan")
    n_eff = float(dr ** 2) if np.isfinite(dr) else float("nan")

    return EffectiveCorrelation(
        rho_bar=float(rho_bar),
        portfolio_vol=float(sigma_P),
        diversified_vol=diversified,
        effective_bet_multiplier=mult,
        n_effective_bets=n_eff,
    )


@dataclass
class TailDependence:
    unconditional: float
    conditional: float
    gap: float                    # conditional - unconditional
    n_stress_days: int
    stress_mode: str


def tail_dependence(position_returns: pd.DataFrame,
                    market_returns: pd.Series,
                    quantile: float = 0.90,
                    mode: str = "downside") -> TailDependence:
    """Average pairwise correlation on stress days vs. all days.

    mode = "downside" : stress = market in its lower tail (crashes) --
                        conditions on market_returns <= (1-quantile) quantile.
    mode = "absolute" : stress = large |market move| in either direction --
                        conditions on |market_returns| >= quantile quantile.

    A large positive `gap` means positions decouple in calm markets but fuse
    together in stress -- the real T18 warning.
    """
    df = position_returns.copy()
    mkt = market_returns.reindex(df.index)
    valid = mkt.notna() & df.notna().all(axis=1)
    df, mkt = df[valid], mkt[valid]
    if len(df) < 10:
        return TailDependence(float("nan"), float("nan"), float("nan"), 0, mode)

    if mode == "downside":
        thresh = mkt.quantile(1 - quantile)
        stress = mkt <= thresh
    elif mode == "absolute":
        thresh = mkt.abs().quantile(quantile)
        stress = mkt.abs() >= thresh
    else:
        raise ValueError("mode must be 'downside' or 'absolute'")

    uncond = _avg_offdiag(df.corr())
    stressed = df[stress]
    cond = _avg_offdiag(stressed.corr()) if len(stressed) >= 3 else float("nan")
    gap = cond - uncond if np.isfinite(cond) and np.isfinite(uncond) else float("nan")
    return TailDependence(uncond, cond, gap, int(stress.sum()), mode)
