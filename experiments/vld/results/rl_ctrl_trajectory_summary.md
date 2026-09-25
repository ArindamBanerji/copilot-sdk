# RL-CTRL-1 — Trajectory-loop controller

Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED; in-distribution only.

Important scope: ProfileScorer.update() has no per-update eta argument. A1/A2 are deterministic curve-level controller emulations over recorded RL-2 FQI curves, not live scorer fits.

| Copilot | Arm | time_to_plateau | plateau_height | trajectory_variance | final_quality | clean_pause_rate | poison detection |
|---|---|---:|---:|---:|---:|---:|---:|
| soc | A0_fixed | 1000 | 0.887 | 216.569 | 0.887 | 0.6% | 100.0% |
| soc | A1_rule_based | 1000 | 0.887 | 216.569 | 0.887 | 0.6% | 100.0% |
| soc | A2_learned | 2000 | 0.887 | 212.555 | 0.887 | 0.6% | 100.0% |
| dataops | A0_fixed | 1500 | 0.756 | 13.573 | 0.756 | 33.1% | 100.0% |
| dataops | A1_rule_based | 1500 | 0.756 | 13.986 | 0.756 | 33.1% | 100.0% |
| dataops | A2_learned | 1500 | 0.756 | 6.865 | 0.756 | 33.1% | 100.0% |

A1 η trajectory: rule-based d² damping/sustain/conserve policy; A2 η trajectory: nearest discrete action with conservation pressure. Both preserve the fixed-rate endpoint in this emulation.

Verdict: the thesis does not have legs from this constrained run. The controllers smooth the recorded trajectory, but no true per-update η control was testable without modifying source. RL-CHAR's -32.75pp OOD gap remains applicable.

§6 sentence: A d²-informed controller can smooth an in-distribution routing trajectory in curve-level emulation, but a live RL-controlled η loop is not established and any effect remains deployment-specific.
