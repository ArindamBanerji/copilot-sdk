# A2 — Adversarial saves:hurts

Tier: GEOMETRY-DERIVED + SIMULATED.

## Construction

Boundary uses closest action-pair midpoints with a small truth-side perturbation and one wrong partial dimension. Misleading cases make the initial Q top-2 acquired values align with a wrong action while the latent truth remains geometry-derived. Adversarial-Q cases align all acquired values with the wrong action so Q cannot recover through a second read. Truth and acquired evidence are separate by design.

## Results

| Copilot | Tier | Saves | Hurts | Ratio | Pre action_accuracy | Post action_accuracy |
|---|---|---:|---:|---|---:|---:|
| soc | boundary | 240 | 0 | 240:0 | 0.0% | 100.0% |
| soc | misleading | 0 | 217 | 0:217 | 100.0% | 27.7% |
| soc | adversarial_q | 0 | 149 | 0:149 | 100.0% | 29.0% |
| **soc** | **all tiers** | **240** | **366** | **240:366** | 68.0% | 51.2% |
| dataops | boundary | 224 | 0 | 224:0 | 0.0% | 93.3% |
| dataops | misleading | 0 | 276 | 0:276 | 100.0% | 8.0% |
| dataops | adversarial_q | 0 | 197 | 0:197 | 100.0% | 6.2% |
| **dataops** | **all tiers** | **224** | **473** | **224:473** | 68.0% | 34.8% |
| trading | boundary | 240 | 0 | 240:0 | 0.0% | 100.0% |
| trading | misleading | 0 | 245 | 0:245 | 100.0% | 18.3% |
| trading | adversarial_q | 0 | 182 | 0:182 | 100.0% | 13.3% |
| **trading** | **all tiers** | **240** | **427** | **240:427** | 68.0% | 43.1% |
| purchasing | boundary | 240 | 0 | 240:0 | 0.0% | 100.0% |
| purchasing | misleading | 0 | 300 | 0:300 | 100.0% | 0.0% |
| purchasing | adversarial_q | 0 | 210 | 0:210 | 100.0% | 0.0% |
| **purchasing** | **all tiers** | **240** | **510** | **240:510** | 68.0% | 32.0% |
| s2p | boundary | 240 | 0 | 240:0 | 0.0% | 100.0% |
| s2p | misleading | 0 | 299 | 0:299 | 100.0% | 0.3% |
| s2p | adversarial_q | 0 | 207 | 0:207 | 100.0% | 1.4% |
| **s2p** | **all tiers** | **240** | **506** | **240:506** | 68.0% | 32.5% |

## Interpretation

Across all 5 copilots × 3 seeds, adversarial construction produced 1184:2282 saves:hurts; Astra's favorable paper-sourced reference is 57:0. The tier with the most hurts is **misleading**.

Paper sentence: On favorable scenarios, VLD achieved 57:0 saves:hurts. On adversarial-constructed scenarios with misleading evidence, the ratio was 1184:2282 — the favorable result does not establish robustness to actively incorrect evidence.

No labels or verified outcomes are used by the action/read pipeline; they are used only for post hoc geometry-derived scoring.
