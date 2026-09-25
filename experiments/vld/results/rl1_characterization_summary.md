# RL-1 characterization — linear fit, FQI, OOD, and data efficiency

| Copilot | A routing / action | B routing / action | C routing / action | B-A pp | C-A pp | C-B pp | B/C recovery |
|---|---:|---:|---:|---:|---:|---:|---:|
| soc | 78.93% +/- 1.48% / 92.13% +/- 1.44% | 76.00% +/- 1.99% / 85.13% +/- 1.94% | 88.03% +/- 1.00% / 99.80% +/- 0.27% | -2.93 | +9.10 | +12.03 | -32% |
| dataops | 57.77% +/- 1.11% / 81.33% +/- 1.92% | 53.03% +/- 1.54% / 59.20% +/- 2.45% | 75.73% +/- 1.23% / 95.93% +/- 1.47% | -4.73 | +17.97 | +22.70 | -26% |
| trading | 71.60% +/- 1.58% / 92.53% +/- 1.57% | 70.97% +/- 1.85% / 86.47% +/- 2.36% | 81.73% +/- 2.22% / 96.00% +/- 1.98% | -0.63 | +10.13 | +10.77 | -6% |
| purchasing | 68.93% +/- 3.30% / 77.00% +/- 2.84% | 52.27% +/- 3.85% / 57.73% +/- 5.11% | 86.63% +/- 2.01% / 97.33% +/- 2.62% | -16.67 | +17.70 | +34.37 | -94% |
| s2p | 65.87% +/- 1.99% / 84.80% +/- 2.12% | 62.07% +/- 1.87% / 76.87% +/- 1.63% | 85.77% +/- 0.57% / 99.53% +/- 0.78% | -3.80 | +19.90 | +23.70 | -19% |

## Learned linear weights

| Copilot | precision | leverage | discriminative |
|---|---:|---:|---:|
| soc | -0.3027 | 9.9504 | -3.6624 |
| dataops | -0.7743 | 7.2896 | -3.3918 |
| trading | -1.1953 | 6.4292 | 0.4753 |
| purchasing | -0.9827 | 5.6802 | -0.5962 |
| s2p | -1.4666 | 9.0547 | -2.4998 |

## OOD and data efficiency

| Copilot | S1 in-distribution | S1 S_B | OOD gap | S2 crossover |
|---|---:|---:|---:|---:|
| soc | 88.03% | 37.63% | +50.40pp | 250 |
| dataops | 75.73% | 60.63% | +15.10pp | 250 |
| trading | not available | not available | B2 profile unsupported | 500 |
| purchasing | not available | not available | B2 profile unsupported | 250 |
| s2p | not available | not available | B2 profile unsupported | 100 |

Verdict: **(c)** — At least one supported B2 shifted-firm OOD profile loses >=5pp routing_quality.

§7 framing: §7 should not present the observed FQI gain as portable beyond the measured geometry-derived stream; retain closed-form Q as the day-zero reference, while treating its cross-firm OOD performance as unmeasured here.

Leakage: all checked FQI inputs exclude verified labels; shuffling evaluation label-side fields left policy outputs identical.
