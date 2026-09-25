# A2-EXT — Dose response and governance catch

Tier: GEOMETRY-DERIVED + SIMULATED.

## Dose response

| Fraction | soc saves:hurts | dataops saves:hurts | trading saves:hurts | purchasing saves:hurts | s2p saves:hurts |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 607:0 | 396:0 | 396:0 | 492:0 | 733:0 |
| 0.10 | 514:1 | 361:10 | 351:5 | 426:14 | 640:0 |
| 0.20 | 424:7 | 327:20 | 310:19 | 376:37 | 579:2 |
| 0.30 | 338:15 | 286:36 | 257:39 | 303:45 | 517:1 |
| 0.50 | 197:38 | 214:79 | 195:59 | 208:76 | 338:1 |
| 0.75 | 79:83 | 165:143 | 84:147 | 87:114 | 172:5 |
| 1.00 | 2:138 | 112:228 | 0:229 | 2:151 | 11:16 |

## Crossover

- soc: first hurts>=saves fraction = 0.75
- dataops: first hurts>=saves fraction = 1.0
- trading: first hurts>=saves fraction = 0.75
- purchasing: first hurts>=saves fraction = 0.75
- s2p: first hurts>=saves fraction = 1.0

## Governance catch

| Copilot | Hurts | Gate caught | Abstention caught | Either caught | Slipped | Combined rate |
|---|---:|---:|---:|---:|---:|---:|
| soc | 553 | 478 | 140 | 498 | 55 | 90.1% |
| dataops | 677 | 602 | 39 | 605 | 72 | 89.4% |
| trading | 612 | 537 | 146 | 549 | 63 | 89.7% |
| purchasing | 750 | 675 | 3 | 675 | 75 | 90.0% |
| s2p | 739 | 664 | 0 | 664 | 75 | 89.9% |

The gate column is the standalone 75%/last-100 Check-A proxy; Check-B volume inputs were not available in this experiment. Abstention is the post-investigation margin < 0.05 proxy.

Paper sentence: At misleading fractions below the reported crossover points, VLD maintains positive saves:hurts; of the adversarial hurts, the combined standalone gate or post-investigation abstention proxy caught the reported fraction, while the remainder slipped through.
