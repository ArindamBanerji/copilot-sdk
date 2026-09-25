# C7 — Looped-Operator Depth

Tier: REAL_COMPONENT exported geometry + SIMULATED streams/verification. Truth labels are nearest-centroid geometry-derived. Metrics: routing_quality (informative reads / actual reads) and action_accuracy (correct geometry-derived action / held-out cases); category_accuracy is not measured because category is supplied.

## Operator and protocol

GATE-B1: no existing iterative post-read refine hook was found. This experiment adds a script-only operator: correlated-Gaussian correction (rho=0.25) to the action logits using residuals of the same two acquired dimensions, scaled by their selected Q×K reliability. Each iteration damps halfway toward the corrected logits. No third read or oracle label enters scoring. A0-A3 share per-seed training/evaluation cases; K updates reuse the K-curve harness helper. Convergence means three successive checkpoint-to-checkpoint movements no larger than 1pp in both metrics, after at least 200 decisions; cap 2,000.

Pre-registered rule: B=2 holds iff no refine arm beats A0 by >2pp routing_quality at at least 2/3 seeds for any copilot.

## Results by copilot and arm

| Copilot | Arm | routing_quality mean ± SD | action_accuracy mean ± SD |
|---|---|---:|---:|
| soc | A0_flat | 0.757 ± 0.029 | 0.887 ± 0.076 |
| soc | A1_depth1 | 0.757 ± 0.029 | 0.893 ± 0.064 |
| soc | A2_depth2 | 0.757 ± 0.029 | 0.907 ± 0.042 |
| soc | A3_depth3 | 0.760 ± 0.026 | 0.927 ± 0.061 |
| dataops | A0_flat | 0.577 ± 0.068 | 0.787 ± 0.095 |
| dataops | A1_depth1 | 0.577 ± 0.068 | 0.787 ± 0.095 |
| dataops | A2_depth2 | 0.577 ± 0.068 | 0.787 ± 0.095 |
| dataops | A3_depth3 | 0.577 ± 0.068 | 0.787 ± 0.095 |
| trading | A0_flat | 0.757 ± 0.061 | 0.920 ± 0.060 |
| trading | A1_depth1 | 0.757 ± 0.061 | 0.920 ± 0.060 |
| trading | A2_depth2 | 0.757 ± 0.061 | 0.920 ± 0.060 |
| trading | A3_depth3 | 0.757 ± 0.061 | 0.920 ± 0.060 |

## Delta versus A0

| Copilot | Arm | routing_quality delta mean ± SD | Per-seed routing_quality delta | Seeds >2pp |
|---|---|---:|---|---:|
| soc | A1_depth1 | +0.00pp ± 0.00pp | 42: +0.0pp, 123: +0.0pp, 7: +0.0pp | 0/3 |
| soc | A2_depth2 | +0.00pp ± 0.00pp | 42: +0.0pp, 123: +0.0pp, 7: +0.0pp | 0/3 |
| soc | A3_depth3 | +0.33pp ± 0.58pp | 42: +1.0pp, 123: +0.0pp, 7: +0.0pp | 0/3 |
| dataops | A1_depth1 | +0.00pp ± 0.00pp | 42: +0.0pp, 123: +0.0pp, 7: +0.0pp | 0/3 |
| dataops | A2_depth2 | +0.00pp ± 0.00pp | 42: +0.0pp, 123: +0.0pp, 7: +0.0pp | 0/3 |
| dataops | A3_depth3 | +0.00pp ± 0.00pp | 42: +0.0pp, 123: +0.0pp, 7: +0.0pp | 0/3 |
| trading | A1_depth1 | +0.00pp ± 0.00pp | 42: +0.0pp, 123: +0.0pp, 7: +0.0pp | 0/3 |
| trading | A2_depth2 | +0.00pp ± 0.00pp | 42: +0.0pp, 123: +0.0pp, 7: +0.0pp | 0/3 |
| trading | A3_depth3 | +0.00pp ± 0.00pp | 42: +0.0pp, 123: +0.0pp, 7: +0.0pp | 0/3 |

## Depth pattern and verdict

Depth comparisons are paired within each copilot/seed. The tables report both positive and negative changes; action_accuracy is not substituted for routing_quality in the registered decision rule.

No refine arm exceeded +2pp routing_quality over A0 at two or more of three seeds for any copilot. **B=2 holds under the preregistered materiality rule for this tested operator and these streams.**

Paper sentence: ‘For a script-only correlated-evidence refine operator operating on the same two acquired dimensions, B=2 flat reads remained sufficient under a 2pp routing_quality materiality threshold; iterative refinement added no material routing_quality gain in the tested geometry-derived simulations.’

## Baseline context and null-stakes

The separate BUDGET experiment reported B=2 routing_quality of SOC 78.9%, DataOps 59.5%, and Trading 72.55%. It used five different seeds and a 500-training/200-evaluation protocol, so it is context rather than a matched comparator; A0 here is the proper paired baseline.

Null-stakes: a failure to beat A0 does not establish that all possible refinement mechanisms are useless; it only bounds this preregistered correlated-evidence operator at this depth and evaluation design. Any negative deltas remain evidence against adding this operator, not proof about every alternative.

Convergence status by seed and arm is available in the JSON (`converged`, `convergence_point`, full checkpoints). A max-cap run is reported as not converged rather than relabeled as convergence.
