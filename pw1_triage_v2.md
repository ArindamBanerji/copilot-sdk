# PW-1 Demo Specs — Status After Fix Round 2

Date: 2026-09-17

## Status

| Spec | Status | Notes |
|---|---|---|
| FORK-01 | PASS | Trading fingerprint, ten factors |
| FORK-02 | PASS | Replay fingerprint parity; timeout hardened |
| MACH-01 | SKIP | PLANT: SOC alert fixture absent |
| MACH-02 | SKIP | PLANT: SOC no-precedent fixture absent |
| MACH-04 | SKIP | BUILD: SOC fingerprint/trajectory contract unavailable |
| PILOT-01 | PASS | Purchasing readiness |
| PILOT-02 | PASS | Purchasing readiness evidence |
| PILOT-03 | SKIP | BUILD: Trading centroid-history endpoint unavailable |
| PLAT-01 | SKIP | BUILD: shared trace panel |
| PLAT-02 | SKIP | ROADMAP: routing badge |
| PLAT-03 | SKIP | BUILD: SOC lacks shared fingerprint route |
| PLAT-04 | SKIP | BUILD: SOC lacks shared trajectory route |
| PLAT-05 | PASS | Five health checks |
| SOC-01 | PASS | Trust-scores response shape corrected |
| SOC-02 | SKIP | PLANT: no-precedent alert |
| SOC-03 | SKIP | BUILD: rejection-summary endpoint |
| SOC-04 | SKIP | BUILD: authority ladder |
| SOC-05 | SKIP | BUILD: frozen twin |
| SOC-06 | SKIP | ROADMAP: investigation trace |
| SOC-07 | PASS | Audit verification |
| SOC-08 | SKIP | CONCEPTUAL: routing accuracy |
| SOC-09 | SKIP | PLANT: alert/analyze fixture returns 404 |
| SOC-10 | SKIP | PLANT: campaign investigation |
| S2P-01 | PASS | Required score payload and live shape |
| S2P-02 | PASS | Required score payload and factor vector |
| S2P-03 | SKIP | BUILD: promotion ladder |
| S2P-04 | PASS | Conservation fields corrected |
| S2P-05 | SKIP | PLANT: supplier enrichment |
| S2P-06 | SKIP | ROADMAP: OTIF provenance |
| PUR-01 | PASS | Fingerprint factors and decision count |
| PUR-02 | PASS | Sigma field assertion corrected |
| PUR-03 | SKIP | PLANT: vendor cascade |
| PUR-04 | PASS | Proof/competence summary-object shape corrected |
| PUR-05 | SKIP | BUILD: proof-ledger export |
| PUR-06 | SKIP | ROADMAP: multi-unit transfer |
| TRD-01 | PASS | Ten factors and sigma values |
| TRD-02 | SKIP | PLANT: Friday regime |
| TRD-03 | PASS | Category accuracy endpoint |
| TRD-04 | SKIP | PLANT: revenge trade |
| TRD-05 | SKIP | CONCEPTUAL: real-money gate |
| TRD-06 | PASS | Earned nonzero weights |
| DO-01 | PASS | `/api/dataops/trust` factors/ranks |
| DO-02 | SKIP | PLANT: differentiated source-score fixture |
| DO-03 | PASS | Six-factor profile/checkpoints |
| DO-04 | SKIP | BUILD: rule-lifecycle is 404 / SC-PORT |
| DO-05 | SKIP | PLANT: K14 misleading-evidence fixture |
| DO-06 | PASS | Trust distribution from `/api/dataops/trust` |

## Summary

- Four of the six requested specs were successfully un-skipped: DO-01, DO-06, PUR-01, and TRD-03.
- DO-04 remains skipped because `/api/self/rule-lifecycle` returns 404.
- SOC-09 remains skipped because `/api/alert/analyze` returns 404 for the available replay fixture; a real alert fixture is required.
- Targeted six-spec verification: **4 passed, 2 skipped, 0 failed**.
- Full-suite expected status after this round: **19 passed, 28 skipped, 0 failed** across the 47 source specs. Playwright’s configured discovery summary may report fewer executable tests because top-level skipped declarations are excluded from execution totals.

## Remaining skips and prerequisites

PLANT work is needed for the scenario-specific stories: SOC no-precedent/fixed-alert/campaign, Trading regime/revenge, Purchasing vendor cascade, DataOps source-lost/K14/Jan-vs-now variants, and S2P supplier enrichment.

BUILD work is needed for shared trace, authority/frozen-twin surfaces, rejection summary, centroid history, claim/rule lifecycle, proof-ledger export, and OTIF provenance. ROADMAP/CONCEPTUAL skips remain intentionally outside this fix round.
