# RL-2 — Two-loop second-derivative curves

Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED labels.

dQ/dN is percentage-point change per 100 verified decisions. `centroid_quality` is K-weighted routing quality from K replayed on the first N transitions; `routing_quality` and `action_accuracy` remain separate.

| Copilot | Approach | N=500 dQ/dN | N=1000 dQ/dN | Plateau N |
|---|---|---:|---:|---:|
| soc | A | 0.000pp/100 | 0.000pp/100 | 250 |
| soc | B1 | 0.178pp/100 | -0.044pp/100 | 750 |
| soc | C | 1.756pp/100 | 0.044pp/100 | 1000 |
| dataops | A | 0.000pp/100 | 0.000pp/100 | 250 |
| dataops | B1 | 0.289pp/100 | 0.067pp/100 | 500 |
| dataops | C | 2.067pp/100 | -0.289pp/100 | 1500 |

## Second derivatives

| Copilot | Approach | d²Q/dN² at centroid plateau |
|---|---|---:|
| soc | A | 0.000 |
| soc | B1 | -1.222 |
| soc | C | -36.074 |
| dataops | A | 0.000 |
| dataops | B1 | -4.778 |
| dataops | C | 4.185 |

Verdict: H2 (2/2 measured copilots met the aggregate H2 comparison).

§6 sentence: Within a fixed deployment, learned routing can sustain compounding past the centroid K-curve plateau; this is a deployment-specific in-distribution result, because RL-CHAR found a -32.75pp OOD gap and therefore portability is not established.

OOD caveat: RL-CHAR classified the FQI gain as overfitting; any curve persistence here is deployment-specific and does not establish portability.

Wall time: 3.48 minutes including the independent rebuild.
