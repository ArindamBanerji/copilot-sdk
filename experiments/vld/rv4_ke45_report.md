# RV-4 / KE-4 / KE-5 Combined Report

## 1. RV-4 Risk-Sensitive Q

Fixed budget confirmed the expected scale-invariance: multiplying Q by a domain penalty ratio does not materially change dimension order at B=2. The risk-fixed arm is near the uniform-fixed arm for each copilot; differences are seed and learning-path noise, not a routing mechanism change.

| Copilot | Penalty | Uniform B=2 | Risk B=2 | Adaptive B | Adaptive gain | Thompson+risk | S1 abstain |
|---|---:|---:|---:|---:|---:|---:|---:|
| soc | 20 | 0.787 | 0.778 | 0.455 | -0.332 | 0.611 | 0.520 |
| dataops | 10 | 0.526 | 0.521 | 0.452 | -0.073 | 0.503 | 1.000 |
| s2p | 5 | 0.666 | 0.660 | 0.589 | -0.078 | 0.632 | 0.440 |
| purchasing | 3 | 0.706 | 0.737 | 0.712 | 0.006 | 0.700 | 0.480 |
| trading | 2 | 0.737 | 0.735 | 0.733 | -0.004 | 0.717 | 0.670 |

Kill/keep verdict: **KILL_OR_QUALIFY**. High-penalty mean adaptive gain was -0.203, low-penalty no-degradation was `False`, and abstain calibration was not degraded: `True`.

The adaptive-budget policy increased reads in high-penalty domains but reduced routing-quality-per-read because later reads are less often informative. Accuracy can still improve in some domains because extra reads recover more cases, but RV-4 as a Q multiplier is not supported as a clean RGI strengthening result.

## 2. KE-4 Distribution Sensitivity

| Distribution | Final routing | Final accuracy | Hurts | Starvation |
|---|---:|---:|---:|---:|
| uniform | 0.542 | 0.756 | 0 | 0.083 |
| clustered | 0.522 | 0.720 | 0 | 0.094 |
| adversarial | 0.510 | 0.728 | 0 | 0.300 |

Pre-registered verdict: **ROBUST**. All three distributions produced positive routing quality over the fixed-control reference region with zero final-checkpoint hurts. The adversarial case was lower than uniform (0.510 vs 0.542) and had higher starvation (0.300), so the effect is robust but distribution-sensitive.

## 3. KE-5 Conservation Interaction

| Arm | Final routing | Final accuracy | Routing dip | Accuracy dip |
|---|---:|---:|---:|---:|
| without_conservation | 0.590 | 0.816 | 0.110 | 0.140 |
| with_conservation | 0.590 | 0.816 | 0.110 | 0.140 |

Mean blocked updates: **0.000**. Final routing cost: **0.000**. Dip reduction: **0.000**.

Under the experimental paper-formula gate, the DataOps trajectory stayed GREEN after the cold-start window, so conservation neither slowed nor improved K learning in this run. This is a neutral interaction result, not evidence that conservation is unnecessary under drift or poisoned verification.

## 4. Combined Implications

- For the paper: KE-4 strengthens the K-learning/RGI claim by showing the DataOps effect survives uniform, clustered, and adversarial training distributions, with the caveat that adversarial training raises starvation.
- For §12.2: distribution sensitivity is validated as measured; risk-sensitive Q should be qualified or moved to a rejected/needs-redesign extension; conservation interaction is measured but neutral under this synthetic trajectory.
- For production: extra budget should be justified by expected accuracy or harm reduction, not by Q scaling alone. Conservation remains a safety boundary for degradation regimes, but this experiment did not trigger it.
