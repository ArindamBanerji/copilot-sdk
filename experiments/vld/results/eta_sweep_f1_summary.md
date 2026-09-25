# F-1: ProfileScorer eta sweep

Tier: REAL_COMPONENT geometry + SIMULATED streams, verification, mu adaptation. Primary metric: routing_quality gap widening (mu+K minus paired C2 K-only), percentage points.
Copilots: SOC and S2P. Seeds: 42, 123, 7. eta and eta_neg scaled together; the streams, held-out sets, decay and convergence runner are fixed.

## Eta × copilot widening

| Copilot | η multiplier | η / η-neg | Widening mean ± SD (pp) | Seeds >2pp | Per-seed widening (pp) |
|---|---:|---:|---:|---:|---|
| soc | 0.5× | 0.025 / 0.025 | +9.70 ± 1.53 | 3/3 | +8.19, +9.67, +11.25 |
| soc | 1.0× | 0.050 / 0.050 | +15.94 ± 3.71 | 3/3 | +11.67, +18.33, +17.81 |
| soc | 2.0× | 0.100 / 0.100 | +14.08 ± 6.76 | 3/3 | +7.06, +14.67, +20.53 |
| soc | 4.0× | 0.200 / 0.200 | +13.35 ± 4.95 | 3/3 | +7.64, +16.08, +16.33 |
| s2p | 0.5× | 0.025 / 0.025 | -6.30 ± 4.78 | 0/3 | -1.17, -10.64, -7.08 |
| s2p | 1.0× | 0.050 / 0.050 | -5.32 ± 2.85 | 0/3 | -2.14, -6.19, -7.64 |
| s2p | 2.0× | 0.100 / 0.100 | -2.69 ± 2.65 | 0/3 | -1.56, -0.81, -5.72 |
| s2p | 4.0× | 0.200 / 0.200 | -1.68 ± 3.73 | 0/3 | +1.44, -0.67, -5.81 |

## Verdict

Read 2: real domain property

SOC stability uses the pre-registered >2pp widening in at least two of three seeds at each eta. S2P sign is assessed from the three-seed mean at each eta. At S2P 4×, one seed is slightly positive (+1.44pp) while the other two are negative; the negative result is therefore a mean pattern, not a universal per-seed sign.

## C2 implication

The result scopes C2's μ-learning claim to the measured eta settings and these simulated streams. Eta and eta_neg were swept jointly, so this does not isolate their separate effects.
