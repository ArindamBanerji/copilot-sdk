# RL-CTRL-2 enrichment-loop controller

| Copilot / arm | final quality | plateau | reads/decision | pause rate | poison detection |
|---|---:|---:|---:|---:|---:|
| s2p/B0_fixed | 0.614 | 583 | 2.00 | 4.63% | 2.00% |
| s2p/B1_rule_based | 0.593 | 200 | 1.93 | 2.47% | 2.00% |
| s2p/B2_learned | 0.687 | 1250 | 1.31 | 8.63% | 9.67% |
| soc/B0_fixed | 0.636 | 217 | 2.00 | 6.97% | 6.67% |
| soc/B1_rule_based | 0.637 | 300 | 1.72 | 10.40% | 5.33% |
| soc/B2_learned | 0.691 | 617 | 1.77 | 6.05% | 0.67% |

Verdict: FQI final-quality gains: S2P +0.073, SOC +0.055; in-distribution only.
RL-CTRL-3 breadth: trigger only if situational_priority_confirmed is true; otherwise do not trigger.
OOD caveat: in-distribution geometry-derived/simulated characterization only.
