# PW-REGEN — Demo Specification Mapping

Generated 2026-09-18 from the embedded catalog table. The table is authoritative: 56 rows produce 56 specs.

## Summary

- Total specs: 56
- Directory counts: SOC 10, S2P 9, Purchasing 6, Trading 6, DataOps 8, Platform 7, Machine 5, Pilot 4, Fork 1
- Passed in verification run: 18
- Skipped: 38
- PLANT/BUILD/ROADMAP/CONCEPTUAL rows are explicitly skipped pending runtime or product prerequisites.
- PLAT-03 and PLAT-04 are also skipped because the current S2P service does not expose the required fingerprint/trajectory equivalent paths.

## Catalog mapping

| Catalog ID | Title | Class | Spec file | Status | Notes |
|---|---|---|---|---|---|
| SOC-01 | analyst-left | LIVE | e2e/demo/soc/soc-01-analyst-left.spec.ts | GENERATED | generated |
| SOC-02 | no-precedent | PLANT | e2e/demo/soc/soc-02-no-precedent.spec.ts | SKIPPED | skipped pending PL-SOC-1 fixture verification |
| SOC-03 | rejected-35 | LIVE | e2e/demo/soc/soc-03-rejected-35.spec.ts | GENERATED | generated |
| SOC-04 | paused-itself | PLANT | e2e/demo/soc/soc-04-paused-itself.spec.ts | SKIPPED | skipped pending PL-SOC-2 fixture verification |
| SOC-05 | two-alerts | ROADMAP | e2e/demo/soc/soc-05-two-alerts.spec.ts | SKIPPED | skipped: cross-graph discovery not built |
| SOC-06 | policy-wins | PLANT | e2e/demo/soc/soc-06-policy-wins.spec.ts | SKIPPED | skipped pending PL-SOC-3 fixture verification |
| SOC-07 | chained | LIVE | e2e/demo/soc/soc-07-chained.spec.ts | GENERATED | generated |
| SOC-08 | frozen-twin | PLANT | e2e/demo/soc/soc-08-frozen-twin.spec.ts | SKIPPED | skipped pending PL-SOC-4 fixture verification |
| SOC-09 | same-alert | LIVE | e2e/demo/soc/soc-09-same-alert.spec.ts | GENERATED | generated |
| SOC-10 | rollback | PLANT | e2e/demo/soc/soc-10-rollback.spec.ts | SKIPPED | skipped pending PL-SOC-5 fixture verification |
| S2P-01 | rule-said-no | LIVE | e2e/demo/s2p/s2p-01-rule-said-no.spec.ts | GENERATED | generated |
| S2P-02 | day-zero | LIVE | e2e/demo/s2p/s2p-02-day-zero.spec.ts | GENERATED | generated |
| S2P-03 | paying-more | PLANT | e2e/demo/s2p/s2p-03-paying-more.spec.ts | SKIPPED | skipped pending PL-S2P-1 fixture verification |
| S2P-04 | earned-autonomy | LIVE | e2e/demo/s2p/s2p-04-earned-autonomy.spec.ts | GENERATED | generated |
| S2P-05 | queue-shrank | PLANT | e2e/demo/s2p/s2p-05-queue-shrank.spec.ts | SKIPPED | skipped pending PL-S2P-2 fixture verification |
| S2P-06 | kept-manual | PLANT | e2e/demo/s2p/s2p-06-kept-manual.spec.ts | SKIPPED | skipped pending PL-S2P-3 fixture verification |
| S2P-07 | budget-strip | ROADMAP | e2e/demo/s2p/s2p-07-budget-strip.spec.ts | SKIPPED | skipped: RL-CTRL not in production path |
| S2P-08 | confidence-band | BUILD | e2e/demo/s2p/s2p-08-confidence-band.spec.ts | SKIPPED | skipped pending endpoint verification |
| S2P-09 | frozen-twin | PLANT | e2e/demo/s2p/s2p-09-frozen-twin.spec.ts | SKIPPED | skipped pending PL-S2P-4 fixture verification |
| PUR-01 | new-gm | LIVE | e2e/demo/purchasing/pur-01-new-gm.spec.ts | GENERATED | generated |
| PUR-02 | trust-trap | LIVE | e2e/demo/purchasing/pur-02-trust-trap.spec.ts | GENERATED | generated |
| PUR-03 | gave-up-authority | PLANT | e2e/demo/purchasing/pur-03-gave-up-authority.spec.ts | SKIPPED | skipped pending PL-PUR-1 fixture verification |
| PUR-04 | quiet-week | LIVE | e2e/demo/purchasing/pur-04-quiet-week.spec.ts | GENERATED | generated |
| PUR-05 | two-stores | PLANT | e2e/demo/purchasing/pur-05-two-stores.spec.ts | SKIPPED | skipped pending PL-PUR-2 fixture verification |
| PUR-06 | demand-limit | ROADMAP | e2e/demo/purchasing/pur-06-demand-limit.spec.ts | SKIPPED | skipped: investigation trace not built |
| TRD-01 | favorite-setup | LIVE | e2e/demo/trading/trd-01-favorite-setup.spec.ts | GENERATED | generated |
| TRD-02 | throttle | PLANT | e2e/demo/trading/trd-02-throttle.spec.ts | SKIPPED | skipped pending PL-TRD-1 fixture verification |
| TRD-03 | certificate | LIVE | e2e/demo/trading/trd-03-certificate.spec.ts | GENERATED | generated |
| TRD-04 | position-alone | ROADMAP | e2e/demo/trading/trd-04-position-alone.spec.ts | SKIPPED | skipped: investigation trace not built |
| TRD-05 | cold-warm | ROADMAP | e2e/demo/trading/trd-05-cold-warm.spec.ts | SKIPPED | skipped: entrant comparison not built |
| TRD-06 | code-free | LIVE | e2e/demo/trading/trd-06-code-free.spec.ts | GENERATED | generated |
| DO-01 | which-data | BUILD | e2e/demo/dataops/do-01-which-data.spec.ts | SKIPPED | skipped pending perturbation verification |
| DO-02 | source-lost-trust | LIVE | e2e/demo/dataops/do-02-source-lost-trust.spec.ts | GENERATED | generated |
| DO-03 | twelve-years | LIVE | e2e/demo/dataops/do-03-twelve-years.spec.ts | GENERATED | generated |
| DO-04 | rule-wrong | BUILD | e2e/demo/dataops/do-04-rule-wrong.spec.ts | SKIPPED | skipped pending SC-PORT endpoint |
| DO-05 | llm-wrong | PLANT | e2e/demo/dataops/do-05-llm-wrong.spec.ts | SKIPPED | skipped pending PL-DO-5 fixture verification |
| DO-06 | jan-vs-now | LIVE | e2e/demo/dataops/do-06-jan-vs-now.spec.ts | GENERATED | generated |
| DO-07 | what-to-buy | ROADMAP | e2e/demo/dataops/do-07-what-to-buy.spec.ts | SKIPPED | skipped: acquisition advisor not built |
| DO-08 | ask-person | ROADMAP | e2e/demo/dataops/do-08-ask-person.spec.ts | SKIPPED | skipped: NL query engine not built |
| PLAT-01 | clocks | CONCEPTUAL | e2e/demo/platform/plat-01-clocks.spec.ts | SKIPPED | skipped: positioning overlay |
| PLAT-02 | cross-signal | BUILD | e2e/demo/platform/plat-02-cross-signal.spec.ts | SKIPPED | skipped pending B7 live verification |
| PLAT-03 | five-corrections | LIVE | e2e/demo/platform/plat-03-five-corrections.spec.ts | SKIPPED | S2P fingerprint equivalent path not exposed |
| PLAT-04 | five-curves | LIVE | e2e/demo/platform/plat-04-five-curves.spec.ts | SKIPPED | S2P trajectory equivalent path not exposed |
| PLAT-05 | two-questions | CONCEPTUAL | e2e/demo/platform/plat-05-two-questions.spec.ts | SKIPPED | skipped: caption card |
| PLAT-06 | where-not | BUILD | e2e/demo/platform/plat-06-where-not.spec.ts | SKIPPED | skipped pending B2 live verification |
| PLAT-07 | whose-moat | BUILD | e2e/demo/platform/plat-07-whose-moat.spec.ts | SKIPPED | skipped pending B1 live verification |
| MACH-01 | through-machine | PLANT | e2e/demo/machine/mach-01-through-machine.spec.ts | SKIPPED | skipped pending PL-MACH-1 fixture verification |
| MACH-02 | reshape | PLANT | e2e/demo/machine/mach-02-reshape.spec.ts | SKIPPED | skipped pending PL-SOC-1 fixture verification |
| MACH-03 | parameter-moved | PLANT | e2e/demo/machine/mach-03-parameter-moved.spec.ts | SKIPPED | skipped pending PL-MACH-3 fixture verification |
| MACH-04 | 500-not-5m | LIVE | e2e/demo/machine/mach-04-500-not-5m.spec.ts | GENERATED | generated |
| MACH-05 | retraction | CONCEPTUAL | e2e/demo/machine/mach-05-retraction.spec.ts | SKIPPED | skipped: retraction table |
| PILOT-01 | first-90 | LIVE | e2e/demo/pilot/pilot-01-first-90.spec.ts | GENERATED | generated |
| PILOT-02 | verifications-stopped | BUILD | e2e/demo/pilot/pilot-02-verifications-stopped.spec.ts | SKIPPED | skipped pending B6 fixture verification |
| PILOT-03 | three-artifacts | LIVE | e2e/demo/pilot/pilot-03-three-artifacts.spec.ts | GENERATED | generated |
| PILOT-04 | bring-numbers | LIVE | e2e/demo/pilot/pilot-04-bring-numbers.spec.ts | GENERATED | generated |
| FORK-01 | clone-run | LIVE | e2e/demo/fork/fork-01-clone-run.spec.ts | GENERATED | generated |
