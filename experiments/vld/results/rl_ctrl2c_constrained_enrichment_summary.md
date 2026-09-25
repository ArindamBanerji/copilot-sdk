# RL-CTRL-2C Redesign — Constrained Enrichment

Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED. OOD caveat: in-distribution only.

## 1. Baseline and verdict

| Copilot | B0 quality | B0 reads | B0 clean pause | B0 poison detection | Best lambda | Best gain | Best pause | Best poison |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| s2p | 0.634 | 2.000 | 3.3% | 100.0% | 0.0 | 0.06817972246965598 | 0.0 | 1.0 |
| soc | 0.765 | 2.000 | 8.0% | 100.0% | 1.0 | 0.06468764257940918 | 0.0 | 1.0 |

## 2. Lambda frontier

| Copilot | Lambda | Quality | Reads | Clean pause | Poison detection |
|---|---:|---:|---:|---:|---:|
| s2p | 0 | 0.702 | 1.429 | 0.0% | 100.0% |
| s2p | 1 | 0.673 | 1.743 | 0.0% | 100.0% |
| s2p | 5 | 0.572 | 2.638 | 0.0% | 100.0% |
| s2p | 10 | 0.535 | 3.037 | 0.0% | 100.0% |
| s2p | 20 | 0.513 | 3.483 | 0.0% | 100.0% |
| s2p | 50 | 0.551 | 2.894 | 0.0% | 100.0% |
| soc | 0 | 0.779 | 1.120 | 80.0% | 100.0% |
| soc | 1 | 0.830 | 1.749 | 0.0% | 100.0% |
| soc | 5 | 0.709 | 2.489 | 0.0% | 100.0% |
| soc | 10 | 0.733 | 2.339 | 0.0% | 100.0% |
| soc | 20 | 0.631 | 3.078 | 0.0% | 100.0% |
| soc | 50 | 0.632 | 3.069 | 0.0% | 100.0% |

## 3. Interpretation

The redesign uses persistent K state, the R1 calibrated per-domain floor, and the Stage-2 poison-25% protocol. The prior CTRL-2 B2-soft gain is retained only as disqualified context because its poison detection was 9.67% for S2P and 0.67% for SOC.

Verdict: **DEPLOYABLE**.

A deployability claim requires both safety constraints and the preregistered +2.75pp routing_quality gain in both copilots; otherwise the result is a characterized frontier or an infeasible constraint.
