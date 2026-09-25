# F-2: Purchasing conservation-gate calibration

Tier: REAL_COMPONENT geometry + SIMULATED streams/degradation. Gate metric: action_accuracy (geometry-derived outcome correctness).
Pre-registered acceptance: every copilot clean PAUSE-decision rate <5%, while Purchasing and SOC retain slow-drift and 25%-poison detection within 1.5x global-floor lag.

## Diagnosis

| Copilot | Clean base action_accuracy | Δ from 0.75 | Clean PAUSE rate |
|---|---:|---:|---:|
| dataops | 0.770 ± 0.051 | +0.020 | 24.7% |
| trading | 0.909 ± 0.039 | +0.159 | 1.3% |
| purchasing | 0.735 ± 0.040 | -0.015 | 46.1% |
| soc | 0.926 ± 0.048 | +0.176 | 0.7% |
| s2p | 0.822 ± 0.032 | +0.072 | 1.6% |

## Clean PAUSE rate by margin

| Copilot | m=.05 | m=.10 | m=.15 |
|---|---:|---:|---:|
| dataops | 17.9% | 5.9% | 0.2% |
| trading | 18.5% | 8.3% | 2.2% |
| purchasing | 13.5% | 1.4% | 0.3% |
| soc | 27.2% | 11.1% | 5.3% |
| s2p | 7.5% | 0.0% | 0.0% |

## Detection preservation

| Copilot | Margin | Scenario | Global lag mean | Calibrated lag mean | Seeds preserved |
|---|---:|---|---:|---:|---:|
| purchasing | 0.10 | slow_drift | 0.0 | missed | 0/3 |
| purchasing | 0.10 | poison_25 | 11.3 | 64.7 | 0/3 |
| purchasing | 0.15 | slow_drift | 0.0 | missed | 0/3 |
| purchasing | 0.15 | poison_25 | 11.3 | 103.5 | 0/3 |
| soc | 0.10 | slow_drift | missed | 388.0 | 0/3 |
| soc | 0.10 | poison_25 | 90.3 | 45.0 | 3/3 |
| soc | 0.15 | slow_drift | missed | missed | 0/3 |
| soc | 0.15 | poison_25 | 90.3 | 71.0 | 3/3 |

## Recommendation and paper sentence

No swept margin satisfies both the all-copilot <5% clean PAUSE-rate requirement and the pre-registered detection-preservation rule.

"A per-domain floor may reduce clean-stream pauses, but none of the tested margins simultaneously met the all-copilot <5% false-pause and detection-preservation criteria; calibration remains unresolved."

The reported PAUSE rate counts PAUSE decisions, not unique streams. F-2 uses a 500-decision clean diagnostic; C5's cited Purchasing 34.78% PAUSE-decision rate used 900 decisions, so these rates are not directly interchangeable. A lag of 0 means the first recorded PAUSE was at onset (decision 501); it does not by itself establish degradation-specific detection. Any Check B pauses remain active under calibration and are reported in per-decision JSON as `gae_theta`.
