# RL-1 — Offline-RL router versus closed-form Q

Method: fitted-Q iteration (five iterations) with `ExtraTreesRegressor`; a lightweight deterministic offline-RL baseline available through sklearn.

Training used 800 B=2 cases per seed from the existing K-learning case generator, with a fixed 50% closed-form / 50% random behavior policy. Rewards were verified-action-derived routing gains. Evaluation used the same frozen 300 B=2 cases per seed for both policies.

| Copilot | Q-closed routing quality | RL-offline routing quality | Delta (pp) | Q std | RL std | Action accuracy (Q / RL) |
|---|---:|---:|---:|---:|---:|---:|
| soc | 78.50% +/- 1.55% | 88.72% +/- 0.67% | +10.22 | 1.55% | 0.67% | 91.33% / 99.89% |
| dataops | 58.44% +/- 0.93% | 76.17% +/- 1.43% | +17.72 | 0.93% | 1.43% | 82.11% / 95.89% |
| trading | 72.28% +/- 1.62% | 82.17% +/- 2.68% | +9.89 | 1.62% | 2.68% | 93.11% / 97.33% |
| purchasing | 68.39% +/- 1.14% | 87.00% +/- 1.16% | +18.61 | 1.14% | 1.16% | 77.00% / 97.67% |
| s2p | 65.22% +/- 1.83% | 85.89% +/- 0.68% | +20.67 | 1.83% | 0.68% | 83.22% / 100.00% |

Pre-registered verdict: materially better = True; qualifying copilots: ['soc', 'dataops', 'trading', 'purchasing', 's2p'].

Leakage guard: passed for every copilot and seed. The policy input consists only of surface evidence, read mask, category identifier, and geometric Q features; shuffling label-side fields left selected actions identical.

§7 paper sentence: Offline fitted-Q routing trained on the same verified-outcome stream met the pre-registered material-improvement rule against closed-form geometric Q at matched B=2; §7 must be revised to present closed-form Q as the inspectable day-zero baseline rather than the routing-performance ceiling under this protocol.
