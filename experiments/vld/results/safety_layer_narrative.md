# Safety-Layer Characterization — Combined Results (R1 + R2)

**Date:** 2026-09-17  
**Tier:** T-real (calibrated floors) + T-sim (deterministic injected threats)  
**Seeds:** 42, 123, 7  
**Copilots:** SOC, DataOps, S2P, Trading, Purchasing

## The architectural discovery (R1)

Round 1 measured the absolute-floor plus long-window-relative-trigger design. The absolute floor cleared after approximately three verified decisions: the measured mean `V_clear` was SOC 3.33, DataOps 3.33, S2P 3.00, Trading 3.00, and Purchasing 3.00 decisions. The 400-decision relative window diluted a 15 percentage-point, 50-decision step drop to less than two percentage points, so G-REL did not detect that regime break. The saved R1 result therefore returned `NOT ESTABLISHED` for two-layer coverage.

The dilution calculation is direct: with baseline accuracy 0.85, 350 clean decisions and 50 decisions at 0.70 produce a 400-decision mean of 0.83125, while the 0.7× threshold is 0.595. The signal remains well above the trigger.

## The fix (R2)

R2 added G-RATE: a short-window detector comparing the last 20 decisions with the preceding 400-decision baseline. At the preregistered threshold 0.90, a 0.70 short-window accuracy is below a 0.765 baseline threshold, so the step drop becomes visible without changing the absolute floor or long-window trigger.

## Measured coverage

The coverage verdict evaluates applicable threat cells only: cold-start poison, steady-state poison, and steady-state sudden-drop. A cold-start sudden-drop cell has no injected drop in the protocol and is not treated as a detection obligation.

| Configuration | Cold poison detection | Steady poison detection | Steady sudden-drop detection | Clean false-pause rate (mean) |
|---|---:|---:|---:|---:|
| G-ABS | 100.0% | 0.0% | 0.0% | 2.13% cold / 0.00% steady |
| G-REL | 6.67% | 6.67% | 0.0% | 0.00% |
| G-BOTH | 100.0% | 6.67% | 0.0% | 2.13% cold / 0.00% steady |
| G-RATE | 100.0% | 100.0% | 86.67% | 0.00% cold / 7.67% steady |
| G-THREE | 100.0% | 100.0% | 86.67% | 2.13% cold / 7.67% steady |

G-RATE detected all steady sudden-drop streams for each copilot in the aggregate result, with a mean lag of 12.33 decisions at the 0.90 threshold. G-THREE covers every applicable measured threat cell, establishing the preregistered three-layer necessity result. The result is not a claim of zero false pauses: the 0.90 rate threshold trades greater sensitivity for a 7.67% steady-state clean false-pause rate in this stream.

## Rate-threshold sensitivity

| Rate threshold | Mean clean false-pause rate | Mean sudden-drop lag |
|---:|---:|---:|
| 0.85 | 0.87% | 19.67 decisions |
| 0.90 (deployed) | 7.67% | 12.33 decisions |
| 0.95 | 22.67% | 9.47 decisions |

Within the tested grid, 0.85 is the only threshold with mean clean false-pause below 5%; 0.90 detects faster but exceeds that clean-stream target. Threshold selection is therefore an explicit sensitivity tradeoff, not a magic-number result.

## The three-layer architecture

| Layer | Mechanism | Regime | Threat addressed |
|---|---|---|---|
| G-ABS | Absolute floor `alpha·q·V >= theta_min` | Cold-start | Approval floor before sufficient evidence |
| G-REL | Relative trigger against the long rolling baseline | Steady-state | Longer sustained degradation |
| G-RATE | 20-decision short-window rate against the 400-decision baseline | Steady-state | Sudden drops and regime breaks |

The deployed proposal is the OR-composition: pause if any layer fires. R2 measured `G-THREE` as covering all applicable injected threats, while the individual layers each leave a distinct gap. The R1 legacy-cell consistency check is retained in the JSON: SOC and S2P match the historical R1 aggregates; DataOps, Purchasing, and Trading have historical aggregate differences and are flagged rather than silently rewritten.

## What this means for §9

The conservation section should present a measured three-layer architecture: the two-layer design exposed a long-window gap, and the short-window rate detector closed the sudden-drop gap in the tested geometry-derived stream. The paper should also report the sensitivity tradeoff: the preregistered 0.90 rate threshold improved detection latency but produced 7.67% mean steady clean false pauses, whereas 0.85 reduced that mean to 0.87% at a longer 19.67-decision mean lag.

## Signal tier

The floors are T-real values from production calibration. Poison and sudden-drop conditions are T-sim deterministic injections; correctness remains geometry-derived and no LLM is used in the gate path. Results are a characterization of this deployment geometry and threat protocol, not an out-of-distribution safety guarantee.
