# Oracle-ceiling diagnostic

Tier: REAL_COMPONENT geometry + SIMULATED streams/actions. Metric: action_accuracy. Values are fractions; gaps are percentage points in the table.
READOUT-PROBLEM requires evidence-oracle minus VLD(B=2) ≥5pp in at least2/3 seeds and action-oracle headroom ≥10pp. UPSTREAM-CEILING requires action-oracle headroom <5pp; otherwise MIXED.

| Copilot | Geometry | Single-pass | VLD B=2 | Evidence oracle | Action oracle | Readout gap (pp) | Architecture gap (pp) | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| soc | default | 0.209 | 0.790 | 1.000 | 1.000 | +21.00 | +0.00 | READOUT-PROBLEM |
| soc | trained | 0.000 | 1.000 | 1.000 | 1.000 | +0.00 | +0.00 | MIXED |
| soc | bootstrapped | 0.149 | 0.530 | 0.998 | 1.000 | +46.78 | +0.22 | READOUT-PROBLEM |
| dataops | default | 0.133 | 0.444 | 1.000 | 1.000 | +55.61 | +0.00 | READOUT-PROBLEM |
| trading | default | 0.211 | 0.519 | 0.992 | 1.000 | +47.33 | +0.78 | READOUT-PROBLEM |
| purchasing | default | 0.097 | 0.307 | 0.988 | 1.000 | +68.11 | +1.22 | READOUT-PROBLEM |
| s2p | default | 0.111 | 0.838 | 1.000 | 1.000 | +16.22 | +0.00 | READOUT-PROBLEM |

## Best-available geometry fork

| Copilot | Geometry used | Readout gap (pp) | Architecture gap (pp) | Ceiling headroom (pp) | Fork verdict |
|---|---|---:|---:|---:|---|
| soc | trained | +0.00 | +0.00 | +100.00 | MIXED |
| dataops | default | +55.61 | +0.00 | +86.67 | READOUT-PROBLEM |
| trading | default | +47.33 | +0.78 | +78.89 | READOUT-PROBLEM |
| purchasing | default | +68.11 | +1.22 | +90.28 | READOUT-PROBLEM |
| s2p | default | +16.22 | +0.00 | +88.94 | READOUT-PROBLEM |

## Cross-campaign interpretation

C7 found SOC action_accuracy +4pp at depth-3 with approximately flat routing_quality. The default-geometry oracle ladder has +21pp readout headroom, while trained SOC is already at action_accuracy 1.0 with zero readout gap. This is only directionally compatible with C7; the protocols and geometry states differ.
C8's existing SOC Strategy E verdicts were ARCHITECTURE ISSUE on default and bootstrapped geometry and SELECTIVE ENRICHMENT on trained geometry. That pattern is NOT consistent with this geometry-generated ladder's READOUT-PROBLEM on default/bootstrapped and no readout gap on trained. The protocols and evaluation labels differ (C8's 543-alert labels versus generated nearest-centroid labels); report the discrepancy, not a replication or reconciliation.

## Paper sentence

The action-accuracy ceiling is geometry- and readout-dependent: report READOUT-PROBLEM only where full-factor evidence improves on B=2 by at least5pp in two of three seeds with at least10pp action-oracle headroom; otherwise distinguish UPSTREAM-CEILING from mixed cases. The action oracle is geometry-derived and does not establish independent-label performance.

Evidence oracle reveals all generated factor values; action oracle alone receives the true category. Geometry labels remain nearest-centroid derived.
