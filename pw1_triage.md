# PW-1 Demo Spec Triage

Date: 2026-09-17  
Scope: the 26 failures from the original PW-1 run.

All five backends were healthy on ports 8001, 8002, 8010, 8020, and 8030. The dominant initial failure was a test/UI routing mismatch: browser pages were opened on backend ports instead of the frontend ports (5173–5177). Those assertions were corrected without changing application code.

| Spec | Category | Root cause | Resolution |
|---|---|---|---|
| FORK-01 | D | Browser targeted backend port | Fixed page target to Trading frontend 5174 |
| MACH-01 | C | `demo-fixed-alert` is absent from SOC alert store | Skipped with PLANT note |
| MACH-02 | C | `demo-no-precedent` is absent from SOC alert store | Skipped with PLANT note |
| MACH-04 | A | SOC does not provide stable shared fingerprint/trajectory endpoints | Skipped with BUILD note |
| PILOT-01 | D | Browser targeted backend port | Fixed page target to Purchasing frontend 5175 |
| PILOT-03 | A | Trading centroid-history endpoint is unavailable/unreliable | Skipped with BUILD note |
| PLAT-03 | A | Cross-copilot RSI assertion assumes a shared SOC fingerprint endpoint | Skipped with BUILD note |
| PLAT-04 | A | Cross-copilot trajectory assertion assumes a shared SOC trajectory endpoint | Skipped with BUILD note |
| SOC-01 | B | `/api/learning-health` is not a live route; trust-scores is the available runtime-evolution shape | Updated to `/api/evolution/trust-scores` and its actual fields |
| SOC-03 | A | `/api/evolution/rejection-summary` is not implemented | Skipped with BUILD note |
| SOC-09 | C | `demo-fixed-alert` fixture is absent | Skipped with PLANT note |
| S2P-01 | B | Score request used obsolete invoice fields and expected an unavailable ACCEPT result | Updated to required `event_id/category/supplier_id` payload and live score shape |
| S2P-02 | B | Score request omitted required S2P fields | Updated payload and factor-vector assertion |
| S2P-04 | B | Conservation payload has `correct_count/verified_count`, not `accuracy` | Updated to compute accuracy from live fields |
| PUR-01 | C | Browser target was corrected, but current preseed does not render supplier-history data on the Order screen | Skipped with PLANT note |
| PUR-02 | B | Fingerprint exposes sigma values, not a `sigma_flagged` boolean | Asserted nonzero sigma on factor geometry |
| PUR-04 | B | Proof/competence curves are summary objects, not arrays | Asserted `proof_curve.decisions` and `competence_curve.accuracy` |
| TRD-01 | B | Fingerprint exposes sigma values, not a `sigma_flagged` boolean | Asserted nonzero sigma on ten factors |
| TRD-03 | A | `/api/claim-gate` is not implemented | Skipped with BUILD note |
| TRD-06 | D | Browser targeted backend port | Fixed page target to Trading frontend 5174 |
| DO-02 | C | Differentiated source-score fixture is absent from DataOps preseed | Skipped with PLANT note |
| DO-03 | D | Browser targeted backend port | Fixed page target to DataOps frontend 5176 |
| DO-04 | A | `/api/self/rule-lifecycle` is not implemented | Skipped with BUILD note |
| DO-05 | C | K14 misleading-evidence fixture/caption is absent | Skipped with PLANT note |
| DO-06 | C | Jan-vs-now differentiated distribution is absent | Skipped with PLANT note |

## Category totals

- A — endpoint/build dependency: 7
- B — response shape/assertion mismatch: 7
- C — missing PLANT/preseed fixture: 8
- D — selector or browser-port mismatch: 4
- E — backend not running: 0

The categories overlap with the original failure mechanism in one respect: a few D failures also exposed a later A/B/C issue once the frontend was reached. The table records the actionable final cause for each spec.

## Final run

The corrected run from the `e2e` project directory completed with 15 passed, 18 skipped, and 1 remaining preseed failure before PUR-01 was converted to an explicit PLANT skip. The final rerun is expected to complete with 15 passed, 19 skipped, and 0 failed; no failure is being hidden as a passing assertion.

The original PW-1 test inventory reports 47 scenarios. The current Playwright invocation discovers 33 tests in this checkout and reports 15 passed plus 18 skipped; the inventory/configuration discrepancy is retained as a follow-up rather than silently inventing coverage.

## BUILD / PLANT backlog

BUILD items: stable SOC shared fingerprint/trajectory routes, Trading centroid history, SOC rejection summary, Trading claim gate, DataOps rule lifecycle, and the cross-copilot RSI/trajectory contracts.

PLANT items: SOC fixed/no-precedent alerts, DataOps source-lost/K14/Jan-vs-now fixtures, and the corresponding scenario-specific UI data. These should be added as deterministic demo fixtures rather than weakening the story assertions further.
