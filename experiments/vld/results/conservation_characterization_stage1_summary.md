# Conservation Characterization Stage 1

Analysis-only; geometry is REAL_COMPONENT and streams/degradations are SIMULATED.

## 1. Q1 — below-floor structure

| Copilot | N=50 | N=100 | N=200 |
|---|---:|---:|---:|
| dataops | 18.7% | 15.3% | 21.3% |
| trading | 0.0% | 0.0% | 0.0% |
| purchasing | 47.3% | 48.1% | 51.3% |
| soc | 0.0% | 0.0% | 0.0% |
| s2p | 11.1% | 3.9% | 0.0% |

At N=100, copilots above 10% below-floor time: dataops, purchasing. This is structural across domains.

## 2. Q2 — Pareto surface

The viable operating-point test is clean_pause_rate < 5% and mean lag < 150 records across all five copilots. The full θ×N×condition surface is in the JSON artifact. See per-copilot rows below for the current point (0.75,100).

| Copilot | Clean pause | Slow drift lag | Poison 25 lag | Fast break lag |
|---|---:|---:|---:|---:|
| dataops | 13.7% | 217.5 | 50.7 | 39.0 |
| trading | 0.7% | missed | 90.7 | missed |
| purchasing | 34.8% | 0.0 | 11.3 | 53.3 |
| soc | 0.4% | missed | 90.3 | missed |
| s2p | 3.5% | 328.0 | 40.0 | 0.0 |

## 3. Q3 — lag drivers

1. **degradation_magnitude**: Pearson r=-0.5829978488828699.
2. **base_accuracy**: Pearson r=0.43525370896396937.
3. **margin_std**: Pearson r=0.1550055219790377.
4. **decision_volume**: Pearson r=undefined.

## 4. Q4 — alternative signals

| Signal family | Parameter | Result |
|---|---:|---|
| absolute_floor | 0.75 / 100 | Per-copilot/per-condition clean rates and lags are in JSON |
| relative_change | 0.2 | Per-copilot/per-condition clean rates and lags are in JSON |
| relative_change | 0.3 | Per-copilot/per-condition clean rates and lags are in JSON |
| relative_change | 0.5 | Per-copilot/per-condition clean rates and lags are in JSON |
| distributional_shift | 0.05 | Per-copilot/per-condition clean rates and lags are in JSON |
| distributional_shift | 0.1 | Per-copilot/per-condition clean rates and lags are in JSON |
| distributional_shift | 0.2 | Per-copilot/per-condition clean rates and lags are in JSON |

## 5. Stage 2 proposal

**Regime:** composite. The absolute floor has a domain-specific clean-pause frontier, while relative change improves comparability but is not uniformly fast and factor drift is not uniformly discriminative. Stage 2 should test a composite calibrated floor plus relative-change guard, with drift retained as an audit signal.

Stage 2 requires operator sign-off before running.

## 6. Characterization verdict

The conservation gate's problem is **mixed, with calibration and statistic limitations rather than a single universal defect**. The Q1/Q2 surface shows whether the absolute floor is domain-specific and whether any retuning clears the joint clean-pause/lag rule; Q3 quantifies whether base accuracy, degradation magnitude, margin volatility, or fixed volume explains lag; Q4 compares relative change and distributional shift on identical streams. These results characterize candidate regimes only and do not adopt a gate change.
