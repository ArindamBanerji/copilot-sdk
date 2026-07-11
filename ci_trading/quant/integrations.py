"""
Drop-in integrations against the product def's existing signatures.

These compose the validated primitives (realized_vol, regime, relative_value,
correlation, implied_vol, dispersion) into the exact surfaces the product def
already defines, so the coding session can replace in place:

  - classify_regime(...)                 -> product def sec 10.4  (F10)
  - CorrelationMonitor.check_correlation  -> product def sec 3.5  (T18)
  - IVRVFactor.compute                    -> product def sec 3.5  (T17)

Nothing here changes the (5,4,7) tensor, the FactorComputer protocol, or the
conservation law. These are better *inputs*, not new architecture.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .realized_vol import rolling_yang_zhang_vol, yang_zhang_vol
from .regime import hurst_rs, regime_from_hurst
from .relative_value import rolling_percentile, band
from .correlation import (effective_correlation, tail_dependence,
                          EffectiveCorrelation, TailDependence)
from .implied_vol import model_free_implied_variance, variance_risk_premium


# ---------------------------------------------------------------------------
# B2 + B3 :: enhanced regime classifier  (product def sec 10.4)
# ---------------------------------------------------------------------------
def classify_regime(vix: float,
                    trend_strength: float | None = None,
                    price_history: pd.Series | None = None,
                    vix_history: pd.Series | None = None,
                    hurst_band: float = 0.05) -> dict:
    """Enhanced drop-in for product def sec 10.4 classify_regime().

    Backward compatible: if only (vix, trend_strength) are given it falls back
    to the original fixed-threshold logic. When `price_history` is supplied it
    adds a statistical persistence read (Hurst); when `vix_history` is supplied
    it replaces the hard VIX 20/30 cutoffs with per-asset percentile bands.

    Returns a dict:
        {"regime": <str>, "hurst": <float|None>, "hurst_regime": <str|None>,
         "vix_percentile": <float|None>, "vol_state": <str>}
    where "regime" is the headline label kept compatible with the original
    ("trending" | "ranging" | "volatile"), and the extra fields are available
    for richer downstream logic (category cross-check, conservation triggers).
    """
    # --- vol state: percentile band if history present, else fixed cutoffs ---
    vix_pct = None
    if vix_history is not None and len(vix_history.dropna()) >= 60:
        s = pd.concat([vix_history.dropna(), pd.Series([vix])])
        vix_pct = float(rolling_percentile(s, window=min(252, len(s))).iloc[-1])
        if vix_pct >= 85:
            vol_state = "volatile"
        elif vix_pct >= 60:
            vol_state = "elevated"
        else:
            vol_state = "calm"
    else:
        if vix > 30:
            vol_state = "volatile"
        elif vix > 20:
            vol_state = "elevated"
        else:
            vol_state = "calm"

    # --- persistence: Hurst on log returns if price history present ----------
    h = None
    h_regime = None
    if price_history is not None and len(price_history.dropna()) >= 64:
        h = hurst_rs(price_history.dropna().values)
        h_regime = regime_from_hurst(h, band=hurst_band)

    # --- headline label (compatible with original three-way output) ----------
    if vol_state == "volatile":
        regime = "volatile"
    elif h_regime == "trending":
        regime = "trending"
    elif h_regime == "mean_reverting":
        regime = "ranging"
    elif trend_strength is not None:                 # original ADX fallback
        regime = "trending" if (vol_state == "calm" and trend_strength > 25) else "ranging"
    else:
        regime = "ranging"

    return {"regime": regime, "hurst": h, "hurst_regime": h_regime,
            "vix_percentile": vix_pct, "vol_state": vol_state}


# ---------------------------------------------------------------------------
# B5 + B6 :: rebuilt CorrelationMonitor  (product def sec 3.5, T18)
# ---------------------------------------------------------------------------
@dataclass
class CorrelationAlert:
    avg_correlation: float          # unconditional average pairwise (kept for compat)
    rho_bar: float                  # basket-identity effective correlation (B5)
    effective_multiplier: float     # portfolio vol / diversified-benchmark vol
    n_effective_bets: float
    tail_gap: float                 # conditional - unconditional correlation (B6)
    concentrated_accuracy: float    # trader's accuracy when correlated (unchanged input)
    recommendations: list = field(default_factory=list)


class CorrelationMonitor:
    """Rebuilt T18 monitor. Same role as product def sec 3.5, but the effective
    exposure number is now a closed-form function of real returns (B5) and the
    crash-correlation flag is stress-conditioned (B6) instead of naive Pearson.
    """

    def __init__(self, tail_quantile: float = 0.90, alert_gap: float = 0.20,
                 alert_multiplier: float = 1.5):
        self.tail_quantile = tail_quantile
        self.alert_gap = alert_gap
        self.alert_multiplier = alert_multiplier

    def check_correlation(self,
                          position_returns: pd.DataFrame,
                          weights,
                          market_returns: pd.Series,
                          concentrated_accuracy: float = float("nan"),
                          ) -> CorrelationAlert | None:
        eff: EffectiveCorrelation = effective_correlation(position_returns, weights)
        td: TailDependence = tail_dependence(position_returns, market_returns,
                                             quantile=self.tail_quantile,
                                             mode="downside")
        recs: list[str] = []
        triggered = False
        if np.isfinite(eff.effective_bet_multiplier) and \
                eff.effective_bet_multiplier >= self.alert_multiplier:
            triggered = True
            recs.append(
                f"Effective exposure {eff.effective_bet_multiplier:.1f}x intended "
                f"(rho_bar={eff.rho_bar:.2f}); reduce the most correlated legs."
            )
        if np.isfinite(td.gap) and td.gap >= self.alert_gap:
            triggered = True
            recs.append(
                f"Stress correlation {td.conditional:.2f} vs {td.unconditional:.2f} "
                f"unconditional (+{td.gap:.2f}); diversification collapses in "
                f"drawdowns -- consider a hedge."
            )
        if not triggered:
            return None
        return CorrelationAlert(
            avg_correlation=td.unconditional,
            rho_bar=eff.rho_bar,
            effective_multiplier=eff.effective_bet_multiplier,
            n_effective_bets=eff.n_effective_bets,
            tail_gap=td.gap,
            concentrated_accuracy=concentrated_accuracy,
            recommendations=recs,
        )


# ---------------------------------------------------------------------------
# B1 + B7 + B3 :: IVRVFactor  (product def sec 3.5, T17)
# ---------------------------------------------------------------------------
class IVRVFactor:
    """Factor computer. Returns a [0,1] score where HIGH => implied is rich
    vs realized (premium-selling edge on). Uses model-free implied variance
    (B7), Yang-Zhang realized vol (B1), and percentile banding (B3) rather than
    a fixed IV/RV > 1.5 threshold.

    context expected keys:
        "option_chain": {"strikes","calls","puts","forward","r","T"}   (B7 inputs)
        "ohlc": DataFrame with open/high/low/close over the RV window   (B1 inputs)
        "vrp_history": pd.Series of past VRP values for percentile banding (B3)
    Returns a neutral 0.5 when no option chain is available for this symbol
    (illiquid / no listed options) -- a graceful runtime degradation, not a
    disabled feature.
    """

    def compute(self, entity_id, context) -> float:
        chain = context.get("option_chain")
        ohlc = context.get("ohlc")
        if chain is None or ohlc is None:
            return 0.5  # no chain for this symbol -> neutral

        iv_res = model_free_implied_variance(
            chain["strikes"], chain["calls"], chain["puts"],
            chain["forward"], chain.get("r", 0.0), chain["T"])
        rv = yang_zhang_vol(ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"])
        if not (np.isfinite(iv_res.implied_variance) and np.isfinite(rv)):
            return 0.5
        vrp = variance_risk_premium(iv_res.implied_variance, rv ** 2)

        hist = context.get("vrp_history")
        if hist is not None and len(pd.Series(hist).dropna()) >= 60:
            s = pd.concat([pd.Series(hist, dtype=float).dropna(),
                           pd.Series([vrp])], ignore_index=True)
            pct = float(rolling_percentile(s, window=min(252, len(s))).iloc[-1])
            return float(np.clip(pct / 100.0, 0.0, 1.0))
        # no history: squash VRP sign into [0,1] with a soft scale
        return float(1.0 / (1.0 + np.exp(-vrp / (rv ** 2 + 1e-9))))
