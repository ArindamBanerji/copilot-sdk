# Stage 3B — d² as a leading control signal

Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED.

The healthy curves are regenerated from RL-2. Degraded and controlled curves are deterministic curve-level simulations; they are not new deployed FQI fits.

## 1. Plateau anticipation

| Copilot | Seed lead times (records) | Mean ± std | Positive and consistent |
|---|---:|---:|---|
| soc | [1400, 900, 1400] | 1233.3 ± 235.7 | True |
| dataops | [1400, 1400, 1900] | 1566.7 ± 235.7 | True |

## 2. Instability/degradation detection

| Copilot | Condition | d² separation | Detected | Lag | d² false-alarm rate |
|---|---|---:|---|---:|---:|
| soc | slow_drift | 0.533 | False | missed | 33.3% |
| soc | poison | 0.800 | False | missed | 33.3% |
| soc | ood | 2.183 | False | missed | 33.3% |
| soc | EWMA λ=.10 baseline | — | 0.0% | missed | 0.6% |
| dataops | slow_drift | 0.533 | True | 0 | 0.0% |
| dataops | poison | 0.800 | True | 0 | 0.0% |
| dataops | ood | 2.183 | True | 0 | 0.0% |
| dataops | EWMA λ=.10 baseline | — | 33.3% | 178 | 33.1% |

## 3. Controlled learning

| Copilot | Fixed trajectory_variance | Controlled trajectory_variance | Fixed final_quality | Controlled final_quality | Smoother | Quality preserved |
|---|---:|---:|---:|---:|---|---|
| soc | 216.5689 | 213.3176 | 0.887 | 0.887 | True | True |
| dataops | 13.5725 | 3.9077 | 0.756 | 0.756 | True | True |

## 4. Verdict

- Sub-test 1: **usable**; sub-test 2: **not_better**; sub-test 3: **usable**.
- Overall: **d2 is descriptive only**.
- Conservation cross-benefit: **False**; d² is not promoted into the gate based on this analysis unless it beats the EWMA baseline on the same deployed stream.

§6 sentence: Within a fixed deployment, d² may describe the learned-routing trajectory and can be evaluated as a control signal, but this analysis does not establish a portable conservation benefit; RL-CHAR measured a -32.75pp OOD gap, so any sustained effect is deployment-specific.

Wall time including the independent rebuild: 7.57 minutes.
