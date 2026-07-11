"""
Correctness tests for the quant-enhancement package. Each test uses synthetic
data with KNOWN ground truth so the estimators are validated, not just executed.

Run:  python -m pytest tests/test_quant.py -q       (or: python tests/test_quant.py)
"""
import math
import numpy as np
import pandas as pd

from ci_trading.quant import (
    yang_zhang_vol, close_to_close_var, rogers_satchell_var,
    hurst_rs, local_hurst, hurst_regime_shift,
    rolling_percentile, band,
    effective_correlation, tail_dependence,
    block_bootstrap_mean_se,
    model_free_implied_variance, variance_risk_premium,
    implied_correlation,
    classify_regime, CorrelationMonitor,
)

RNG = np.random.default_rng(7)
TRADING_DAYS = 252


# --------------------------------------------------------------------------- #
# helpers                                                                      #
# --------------------------------------------------------------------------- #
def simulate_ohlc(n_days=750, ann_vol=0.20, steps_per_day=64, gaps=False,
                  overnight_vol=0.0, seed=1):
    """Continuous GBM sampled intraday to produce realistic O/H/L/C at a known
    annualized volatility. If gaps=True, inject overnight jumps of size
    ~ N(0, overnight_vol) between prior close and next open."""
    rng = np.random.default_rng(seed)
    dt_day = 1.0 / TRADING_DAYS
    dt = dt_day / steps_per_day
    sig = ann_vol
    rows = []
    price = 100.0
    for _ in range(n_days):
        if gaps:
            price *= math.exp(-0.5 * overnight_vol**2 + overnight_vol * rng.standard_normal())
        o = price
        path = [o]
        for _ in range(steps_per_day):
            price *= math.exp(-0.5 * sig**2 * dt + sig * math.sqrt(dt) * rng.standard_normal())
            path.append(price)
        c = price
        rows.append((o, max(path), min(path), c))
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    return df


def ar1_returns(n=4000, phi=0.0, sigma=0.01, seed=3):
    rng = np.random.default_rng(seed)
    e = rng.normal(0, sigma, n)
    r = np.zeros(n)
    for t in range(1, n):
        r[t] = phi * r[t-1] + e[t]
    return r


def prices_from_returns(r, p0=100.0):
    return p0 * np.exp(np.cumsum(r))


def fbm_increments(n, H, seed=0):
    """Fractional Gaussian noise with target Hurst H via spectral synthesis.
    The canonical ground-truth generator for Hurst estimation."""
    r = np.random.default_rng(seed)
    m = 1
    while m < n:
        m *= 2
    m *= 2
    f = np.fft.rfftfreq(m)[1:]
    amp = np.sqrt(f ** (1 - 2 * H))
    phases = r.uniform(0, 2 * np.pi, len(f))
    spec = np.concatenate([[0.0], amp * np.exp(1j * phases)])
    x = np.fft.irfft(spec, n=m)[:n]
    return x / x.std()


def bs_price(S, K, T, r, sigma, call=True):
    from math import log, sqrt, exp, erf
    def ncdf(x):
        return 0.5 * (1 + erf(x / sqrt(2)))
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    if call:
        return S * ncdf(d1) - K * exp(-r * T) * ncdf(d2)
    return K * exp(-r * T) * ncdf(-d2) - S * ncdf(-d1)


# --------------------------------------------------------------------------- #
# B1 -- Yang-Zhang realized vol                                                #
# --------------------------------------------------------------------------- #
def test_yang_zhang_recovers_known_vol():
    df = simulate_ohlc(ann_vol=0.20, gaps=False, seed=11)
    yz = yang_zhang_vol(df.open, df.high, df.low, df.close)
    assert 0.16 < yz < 0.24, f"YZ vol {yz:.3f} should be ~0.20"


def test_yang_zhang_catches_overnight_gap_that_c2c_misses():
    # Build days where each session opens with a big gap then fully reverts,
    # so close-to-close ~ 0 but the true risk (gaps) is large.
    rng = np.random.default_rng(5)
    rows = []
    c_prev = 100.0
    for _ in range(400):
        gap = rng.choice([-0.03, 0.03])          # 3% overnight gap
        o = c_prev * (1 + gap)
        c = c_prev                               # fully reverts by close
        hi = max(o, c) * 1.001
        lo = min(o, c) * 0.999
        rows.append((o, hi, lo, c))
        c_prev = c
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    yz = yang_zhang_vol(df.open, df.high, df.low, df.close)
    c2c = math.sqrt(close_to_close_var(df.close))
    assert yz > 5 * max(c2c, 1e-6), f"YZ {yz:.3f} must dominate c2c {c2c:.4f} on gap-revert"


def test_rogers_satchell_finite_and_positive():
    df = simulate_ohlc(ann_vol=0.30, seed=13)
    rs = rogers_satchell_var(df.open, df.high, df.low, df.close)
    assert rs > 0 and math.isfinite(rs)
    assert 0.20 < math.sqrt(rs) < 0.40


# --------------------------------------------------------------------------- #
# B2 -- Hurst / regime                                                         #
# --------------------------------------------------------------------------- #
def test_hurst_random_walk_near_half():
    # ground truth: fGn at H=0.5 is a random walk in price
    h = hurst_rs(prices_from_returns(fbm_increments(4000, 0.5, seed=21) * 0.01))
    assert 0.44 < h < 0.56, f"random-walk H {h:.3f} should be ~0.5"


def test_hurst_trending_above_half():
    # ground truth: fGn at H=0.75 (persistent)
    h = hurst_rs(prices_from_returns(fbm_increments(4000, 0.75, seed=22) * 0.01))
    assert h > 0.60, f"persistent H {h:.3f} should be > 0.60 (target 0.75)"


def test_hurst_mean_reverting_below_half():
    # ground truth: fGn at H=0.30 (anti-persistent)
    h = hurst_rs(prices_from_returns(fbm_increments(4000, 0.30, seed=23) * 0.01))
    assert h < 0.42, f"anti-persistent H {h:.3f} should be < 0.42 (target 0.30)"


def test_local_hurst_and_shift_flag():
    r = np.concatenate([ar1_returns(2000, phi=0.0, seed=31),
                        ar1_returns(2000, phi=0.5, seed=32)])
    lh = local_hurst(prices_from_returns(r), window=250, step=25)
    assert lh.notna().sum() > 5
    flags = hurst_regime_shift(lh, lookback=6, z_threshold=1.5)
    assert flags.any(), "expected at least one regime-shift flag across the join"


# --------------------------------------------------------------------------- #
# B3 -- percentile bands                                                       #
# --------------------------------------------------------------------------- #
def test_rolling_percentile_ranks_extremes():
    s = pd.Series(np.arange(300, dtype=float))
    pct = rolling_percentile(s, window=100)
    assert pct.iloc[-1] > 95, "monotone-increasing series: last point is near-max"
    assert band(pct.iloc[-1]) == "rich"


# --------------------------------------------------------------------------- #
# B5 -- effective correlation                                                  #
# --------------------------------------------------------------------------- #
def test_effective_correlation_perfectly_correlated():
    base = pd.Series(RNG.normal(0, 0.01, 500))
    R = pd.DataFrame({f"p{i}": base for i in range(4)})   # identical -> rho=1
    eff = effective_correlation(R, weights=[1, 1, 1, 1])
    assert eff.rho_bar > 0.98, f"rho_bar {eff.rho_bar:.3f} should be ~1"
    assert eff.effective_bet_multiplier > 1.8


def test_effective_correlation_independent():
    R = pd.DataFrame({f"p{i}": RNG.normal(0, 0.01, 3000) for i in range(5)})
    eff = effective_correlation(R, weights=[1, 1, 1, 1, 1])
    assert abs(eff.rho_bar) < 0.10, f"independent rho_bar {eff.rho_bar:.3f} ~ 0"
    assert eff.n_effective_bets > 3.0, "5 independent bets -> N_eff well above 3"


def test_effective_correlation_recovers_known_rho():
    # one-factor model: r_i = sqrt(rho)*F + sqrt(1-rho)*eps_i  -> pairwise corr = rho
    rho = 0.4
    n = 6000
    F = RNG.normal(0, 1, n)
    R = pd.DataFrame({f"p{i}": (math.sqrt(rho) * F + math.sqrt(1 - rho) * RNG.normal(0, 1, n)) * 0.01
                      for i in range(5)})
    eff = effective_correlation(R, weights=[1] * 5)
    assert abs(eff.rho_bar - rho) < 0.06, f"rho_bar {eff.rho_bar:.3f} vs {rho}"


# --------------------------------------------------------------------------- #
# B6 -- tail dependence                                                        #
# --------------------------------------------------------------------------- #
def test_tail_dependence_detects_crash_correlation():
    n = 4000
    mkt = pd.Series(RNG.normal(0, 0.01, n))
    # calm days: idiosyncratic; stress days (big down market): move together
    stress = mkt < mkt.quantile(0.10)
    cols = {}
    for i in range(4):
        base = RNG.normal(0, 0.01, n)
        base[stress.values] = mkt.values[stress.values] * 1.2 + RNG.normal(0, 0.001, stress.sum())
        cols[f"p{i}"] = base
    R = pd.DataFrame(cols)
    td = tail_dependence(R, mkt, quantile=0.90, mode="downside")
    assert td.gap > 0.3, f"stress gap {td.gap:.3f} should be large & positive"
    assert td.conditional > td.unconditional + 0.3, \
        f"conditional {td.conditional:.3f} must exceed unconditional {td.unconditional:.3f}"


# --------------------------------------------------------------------------- #
# B4 -- clustering-aware dispersion                                            #
# --------------------------------------------------------------------------- #
def test_block_bootstrap_inflation_on_autocorrelated_series():
    q_iid = pd.Series(RNG.normal(0.6, 0.1, 400))
    q_clustered = pd.Series(0.6 + pd.Series(ar1_returns(400, phi=0.8, sigma=0.05, seed=41)).values)
    d_iid = block_bootstrap_mean_se(q_iid, block=20, n_boot=800)
    d_clu = block_bootstrap_mean_se(q_clustered, block=20, n_boot=800)
    assert abs(d_iid.inflation - 1.0) < 0.4, f"iid inflation {d_iid.inflation:.2f} ~ 1"
    assert d_clu.inflation > 1.4, f"clustered inflation {d_clu.inflation:.2f} should exceed 1.4"


# --------------------------------------------------------------------------- #
# B7 -- model-free implied variance                                           #
# --------------------------------------------------------------------------- #
def test_model_free_iv_recovers_constant_smile():
    S0, r, T, sigma = 100.0, 0.0, 0.25, 0.20
    F = S0 * math.exp(r * T)
    strikes = np.arange(60, 141, 2.5)
    calls = np.array([bs_price(S0, K, T, r, sigma, call=True) for K in strikes])
    puts = np.array([bs_price(S0, K, T, r, sigma, call=False) for K in strikes])
    res = model_free_implied_variance(strikes, calls, puts, F, r, T)
    assert abs(res.implied_vol - sigma) < 0.01, f"recovered {res.implied_vol:.4f} vs {sigma}"


def test_variance_risk_premium_sign():
    assert variance_risk_premium(0.05, 0.03) > 0
    assert variance_risk_premium(0.02, 0.04) < 0


# --------------------------------------------------------------------------- #
# B8 -- implied correlation                                                    #
# --------------------------------------------------------------------------- #
def test_implied_correlation_bounds():
    ic = implied_correlation(index_iv=0.18, constituent_ivs=[0.25, 0.28, 0.22, 0.30],
                             weights=[0.25, 0.25, 0.25, 0.25])
    assert 0.0 < ic < 1.0, f"implied corr {ic:.3f} out of expected range"


# --------------------------------------------------------------------------- #
# integrations                                                                 #
# --------------------------------------------------------------------------- #
def test_classify_regime_backward_compatible():
    out = classify_regime(vix=35)
    assert out["regime"] == "volatile"
    out2 = classify_regime(vix=15, trend_strength=30)
    assert out2["regime"] == "trending"


def test_classify_regime_uses_hurst():
    r = ar1_returns(phi=0.5, seed=51)
    px = pd.Series(prices_from_returns(r))
    out = classify_regime(vix=15, price_history=px)
    assert out["hurst_regime"] == "trending"
    assert out["regime"] == "trending"


def test_correlation_monitor_fires_on_concentration():
    n = 1500
    base = pd.Series(RNG.normal(0, 0.01, n))
    R = pd.DataFrame({f"p{i}": base + RNG.normal(0, 0.001, n) for i in range(4)})  # ~1 corr
    mkt = base
    mon = CorrelationMonitor(alert_multiplier=1.5)
    alert = mon.check_correlation(R, weights=[1, 1, 1, 1], market_returns=mkt)
    assert alert is not None
    assert alert.rho_bar > 0.9
    assert len(alert.recommendations) >= 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {fn.__name__}: {e}")
        except Exception as e:
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
