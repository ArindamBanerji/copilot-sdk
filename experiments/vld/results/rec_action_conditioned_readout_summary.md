# REC-ACTION conditioned action readout

Tier: GEOMETRY-DERIVED + SIMULATED streams/evidence/verification. Metric: action_accuracy. Results use default geometry and 250 paired scenarios per seed.

## Readout design

The conditioned readout scores all category/action centroids on v_L. Read dimensions are reweighted above baseline using normalized Q score and observed per-read delta; unread dimensions receive 0.70× baseline precision. The function uses only post-trajectory vector and metadata (selected dimensions/order, Q×K values, and deltas). Verified labels and correctness fields are excluded.

## Leakage check

The audit shuffles a separate verified-label channel but evaluates both reported accuracies against unchanged canonical targets. A pass requires unchanged actions and ≤2pp canonical-target accuracy change; evaluating against random labels is shown separately because that value must change even for a label-blind predictor.

| Copilot | Unshuffled | Shuffled-channel rerun | Random-label reference | Delta | Passed |
|---|---:|---:|---:|---:|---|
| soc | 88.0% | 88.0% | 24.0% | 0.00pp | True |
| dataops | 68.0% | 68.0% | 26.0% | 0.00pp | True |
| trading | 50.0% | 50.0% | 28.0% | 0.00pp | True |
| purchasing | 56.0% | 56.0% | 24.0% | 0.00pp | True |
| s2p | 92.0% | 92.0% | 20.0% | 0.00pp | True |

## Paired action_accuracy results

| Copilot | Current | Conditioned | Oracle | Headroom (pp) | Recovery (pp) | Recovery fraction |
|---|---:|---:|---:|---:|---:|---:|
| soc | 81.5% | 84.3% | 100.0% | 18.53 | 2.80 | 14.8% |
| dataops | 33.6% | 55.6% | 100.0% | 66.40 | 22.00 | 33.1% |
| trading | 48.3% | 56.3% | 99.5% | 51.20 | 8.00 | 15.6% |
| purchasing | 22.3% | 42.4% | 98.8% | 76.53 | 20.13 | 26.0% |
| s2p | 85.6% | 90.9% | 100.0% | 14.40 | 5.33 | 37.6% |

## Verdict

Conditioned readout recovered >=15pp in 2/5 copilots; frontier remains with partial recovery.

SOC cross-reference: C7 reported +4pp action_accuracy at depth-3 with approximately flat routing_quality. Compare that result with SOC's REC-ACTION recovery here; the two operators and protocols are distinct.

## Paper boundary

If the preregistered threshold is not met, the frontier remains: evidence-conditioned readout shows only partial recovery under this specified operator. If met, the central claim upgrades only for this tested label-blind readout and geometry tier.
