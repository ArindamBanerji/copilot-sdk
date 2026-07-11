"""Quant-rigor enhancements for the Trading Copilot (from Bloch 2016)."""
from .realized_vol import (
    yang_zhang_var, yang_zhang_vol, rogers_satchell_var,
    close_to_close_var, rolling_yang_zhang_vol, overnight_gap_share,
)
from .regime import (
    hurst_rs, regime_from_hurst, local_hurst, hurst_regime_shift,
)
from .relative_value import rolling_percentile, band, zscore
from .correlation import (
    effective_correlation, tail_dependence,
    EffectiveCorrelation, TailDependence,
)
from .conservation_stats import block_bootstrap_mean_se, DispersionDiagnostic
from .implied_vol import (
    model_free_implied_variance, variance_risk_premium, ImpliedVarianceResult,
)
from .dispersion import implied_correlation, dispersion_signal, DispersionSignal
from .integrations import classify_regime, CorrelationMonitor, IVRVFactor

__all__ = [
    "yang_zhang_var", "yang_zhang_vol", "rogers_satchell_var",
    "close_to_close_var", "rolling_yang_zhang_vol", "overnight_gap_share",
    "hurst_rs", "regime_from_hurst", "local_hurst", "hurst_regime_shift",
    "rolling_percentile", "band", "zscore",
    "effective_correlation", "tail_dependence",
    "EffectiveCorrelation", "TailDependence",
    "block_bootstrap_mean_se", "DispersionDiagnostic",
    "model_free_implied_variance", "variance_risk_premium",
    "ImpliedVarianceResult",
    "implied_correlation", "dispersion_signal", "DispersionSignal",
    "classify_regime", "CorrelationMonitor", "IVRVFactor",
]
