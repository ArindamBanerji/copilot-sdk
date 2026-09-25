# RL-CTRL-1 Option C — Runtime monkey-patch

The live `KUtilityStore.update_weights` method was monkey-patched at runtime. The wrapper injected controller-selected `lr_pos`/`lr_neg`, called the original method body, and restored the method after each run.

## Sanity check

| Copilot | KE-1 N=500 | A0 N=500 (42/123/7) | Pass |
|---|---:|---:|---|
| soc | 0.810 | 0.790/0.840/0.790 | yes |
| dataops | 0.630 | 0.670/0.550/0.560 | no |

## A0/A1/A2

| Copilot | Arm | Plateau height | Trajectory variance | Final accuracy | Compounding index | α min–max | Pressure violations |
|---|---|---:|---:|---:|---:|---:|---:|
| soc | A0_fixed | 0.730 | 0.0034 | 0.853 | 0.624 | 1.00–1.00 | 0 |
| soc | A1_rule_based | 0.730 | 0.0031 | 0.853 | 0.624 | 0.50–1.00 | 0 |
| soc | A2_learned | 0.797 | 0.0041 | 0.953 | 0.760 | 0.25–0.50 | 0 |
| dataops | A0_fixed | 0.680 | 0.0044 | 0.873 | 0.593 | 1.00–1.00 | 0 |
| dataops | A1_rule_based | 0.653 | 0.0034 | 0.833 | 0.544 | 0.50–1.00 | 0 |
| dataops | A2_learned | 0.643 | 0.0055 | 0.820 | 0.528 | 0.25–0.50 | 0 |

## K-state divergence

L2 divergence from A0 is recorded per seed at N=500 and N=1000 in the JSON under `k_state_divergence`. Alpha trajectories, per-update conservation checks, curves, K snapshots, and compounding metrics are also retained per arm/seed.

Verdict: sanity failed; no controller thesis upgrade (A1/A2 did not beat A0).
