# Conservation Stage 3A — Startup Characterization and Drift Tracking

Simulation-only; no production gate change.

## 1. Startup characterization

| Copilot | N=100 floor | N=250 floor | N=500 floor | R1 floor |
|---|---:|---:|---:|---:|
| dataops | 0.610 | 0.625 | 0.643 | 0.669 |
| trading | 0.623 | 0.691 | 0.738 | 0.766 |
| purchasing | 0.557 | 0.633 | 0.634 | 0.655 |
| soc | 0.607 | 0.684 | 0.740 | 0.764 |
| s2p | 0.750 | 0.777 | 0.772 | 0.769 |

The startup fit uses the first N records and evaluates on a disjoint held-out stream segment. N=100 is treated as sufficient when its fitted floor is within 0.05 of the Stage 2 R1 floor.

## 2. Tracking comparison

| Regime | Copilot | clean_pause_rate | slow drift detection | slow drift lag | poison detection | fast-break detection | validated |
|---|---|---:|---:|---:|---:|---:|---|
| T0_static | dataops | 4.7% | 0.0% | missed | 66.7% | 0.0% | False |
| T0_static | trading | 0.0% | 0.0% | missed | 33.3% | 0.0% | False |
| T0_static | purchasing | 0.0% | 0.0% | missed | 66.7% | 33.3% | False |
| T0_static | soc | 0.0% | 0.0% | missed | 66.7% | 0.0% | False |
| T0_static | s2p | 9.3% | 100.0% | 212.66666666666666 | 100.0% | 33.3% | False |
| T1_relative_10 | dataops | 8.1% | 33.3% | 465 | 100.0% | 0.0% | False |
| T1_relative_10 | trading | 0.0% | 0.0% | missed | 100.0% | 0.0% | False |
| T1_relative_10 | purchasing | 0.0% | 0.0% | missed | 66.7% | 33.3% | False |
| T1_relative_10 | soc | 0.0% | 0.0% | missed | 100.0% | 0.0% | False |
| T1_relative_10 | s2p | 9.3% | 100.0% | 212.66666666666666 | 100.0% | 33.3% | False |
| T1_relative_20 | dataops | 4.7% | 0.0% | missed | 66.7% | 0.0% | False |
| T1_relative_20 | trading | 0.0% | 0.0% | missed | 33.3% | 0.0% | False |
| T1_relative_20 | purchasing | 0.0% | 0.0% | missed | 66.7% | 33.3% | False |
| T1_relative_20 | soc | 0.0% | 0.0% | missed | 66.7% | 0.0% | False |
| T1_relative_20 | s2p | 9.3% | 100.0% | 212.66666666666666 | 100.0% | 33.3% | False |
| T1_relative_30 | dataops | 4.7% | 0.0% | missed | 66.7% | 0.0% | False |
| T1_relative_30 | trading | 0.0% | 0.0% | missed | 33.3% | 0.0% | False |
| T1_relative_30 | purchasing | 0.0% | 0.0% | missed | 66.7% | 33.3% | False |
| T1_relative_30 | soc | 0.0% | 0.0% | missed | 66.7% | 0.0% | False |
| T1_relative_30 | s2p | 9.3% | 100.0% | 212.66666666666666 | 100.0% | 33.3% | False |
| T2_cusum_h3 | dataops | 98.5% | 100.0% | 1 | 100.0% | 66.7% | False |
| T2_cusum_h3 | trading | 91.1% | 100.0% | 1 | 100.0% | 100.0% | False |
| T2_cusum_h3 | purchasing | 50.1% | 66.7% | 1 | 100.0% | 33.3% | False |
| T2_cusum_h3 | soc | 33.1% | 33.3% | 1 | 100.0% | 0.0% | False |
| T2_cusum_h3 | s2p | 56.9% | 100.0% | 157.33333333333334 | 100.0% | 100.0% | False |
| T2_cusum_h5 | dataops | 98.1% | 100.0% | 1 | 100.0% | 66.7% | False |
| T2_cusum_h5 | trading | 90.3% | 100.0% | 1 | 100.0% | 100.0% | False |
| T2_cusum_h5 | purchasing | 49.8% | 66.7% | 1 | 100.0% | 33.3% | False |
| T2_cusum_h5 | soc | 0.0% | 33.3% | 896 | 100.0% | 0.0% | False |
| T2_cusum_h5 | s2p | 55.7% | 100.0% | 158.66666666666666 | 100.0% | 100.0% | False |
| T2_cusum_h8 | dataops | 97.8% | 100.0% | 1 | 100.0% | 66.7% | False |
| T2_cusum_h8 | trading | 56.9% | 66.7% | 1 | 100.0% | 100.0% | False |
| T2_cusum_h8 | purchasing | 48.6% | 66.7% | 1 | 100.0% | 33.3% | False |
| T2_cusum_h8 | soc | 0.0% | 33.3% | 899 | 100.0% | 0.0% | False |
| T2_cusum_h8 | s2p | 54.7% | 100.0% | 159.66666666666666 | 100.0% | 100.0% | False |
| T2_ewma_lambda5 | dataops | 36.1% | 33.3% | 1 | 100.0% | 33.3% | False |
| T2_ewma_lambda5 | trading | 4.1% | 0.0% | missed | 100.0% | 0.0% | False |
| T2_ewma_lambda5 | purchasing | 2.8% | 0.0% | missed | 100.0% | 33.3% | False |
| T2_ewma_lambda5 | soc | 0.7% | 0.0% | missed | 100.0% | 0.0% | False |
| T2_ewma_lambda5 | s2p | 35.4% | 100.0% | 162 | 100.0% | 33.3% | False |
| T2_ewma_lambda10 | dataops | 33.1% | 33.3% | 178 | 100.0% | 66.7% | False |
| T2_ewma_lambda10 | trading | 4.1% | 0.0% | missed | 100.0% | 0.0% | False |
| T2_ewma_lambda10 | purchasing | 4.3% | 0.0% | missed | 100.0% | 33.3% | False |
| T2_ewma_lambda10 | soc | 0.6% | 0.0% | missed | 100.0% | 0.0% | False |
| T2_ewma_lambda10 | s2p | 35.9% | 100.0% | 160 | 100.0% | 33.3% | False |
| T2_ewma_lambda20 | dataops | 32.0% | 66.7% | 186.5 | 100.0% | 66.7% | False |
| T2_ewma_lambda20 | trading | 4.1% | 0.0% | missed | 100.0% | 0.0% | False |
| T2_ewma_lambda20 | purchasing | 4.5% | 0.0% | missed | 100.0% | 33.3% | False |
| T2_ewma_lambda20 | soc | 0.5% | 33.3% | 879 | 100.0% | 0.0% | False |
| T2_ewma_lambda20 | s2p | 36.5% | 100.0% | 158.66666666666666 | 100.0% | 33.3% | False |

## 3. Did tracking close the slow-drift gap?

T0 is the static per-domain floor. The selected tracker is **T1_relative_20**; previously missed copilots and their axis results are in the JSON per-copilot aggregates.

## 4. False-pause cost

Acceptance requires clean_pause_rate <5%. Compare each tracker against T0 in the table; any tracker above 5% fails axis 1 even if its lag improves.

## 5. Tracker comparison

Relative movement, standardized CUSUM, and EWMA are all evaluated. The best tracker is selected by validated-copilot count, then lowest mean clean-pause rate.

## 6. H-yes/H-no verdict

**H-no**. Validated copilots: none. Failed copilots: dataops, trading, purchasing, soc, s2p.

## 7. Best tracker

T1_relative_20 with parameters {'X_pct': 0.2}.

## 8. §5 conservation sentence

slow-drift latency is a genuine boundary of accuracy-based gating even with tracking; the static per-domain floor remains the false-pause fix, with slow-drift as an honest limitation.

## 9. Stage 3B

Stage 3B (d² control signal) is **priority** because H-no indicates that accuracy/geometry tracking did not close the slow-drift boundary.
