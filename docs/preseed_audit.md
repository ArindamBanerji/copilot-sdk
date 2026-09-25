# Preseed Sufficiency Audit — Demo Scenarios

**Date:** 2026-09-17  
**Preseed script:** `scripts/preseed_all_copilots.py`  
**Backends tested:** 8001, 8002, 8010, 8020, 8030

## Scope note

The session-state claim says “29 LIVE” and “18 skipped”, but the current
`e2e/demo` inventory contains 47 scenario files, 19 executable `test(...)`
cases, and 28 `test.skip(...)` cases. This audit therefore reports the 19
currently executable cases, the explicit scenario-specific checks from the
audit request, and the skipped PLANT gaps separately. No scenario was counted
as passing solely because it was skipped.

## Per-Copilot State Summary

| Copilot | Port | Verified decisions | Centroid checkpoints | Fingerprint factors | Conservation |
|---|---:|---:|---:|---:|---|
| Trading | 8010 | 360 | 50 | 10 | GREEN; 360 verified, 359 correct |
| Purchasing | 8020 | 485 | N/A for required check | 7 | GREEN; 485 verified, 450 correct |
| DataOps | 8030 | 417 | 50 | 6 | GREEN; 417 verified, 310 correct |
| S2P | 8002 | 196 | N/A | N/A | GREEN; 196 verified, 173 correct |
| SOC | 8001 | 4,862 | N/A | N/A | Learning state populated; audit chain verified |

Additional live state: Trading and DataOps switching endpoints report 800 and
1,418 accumulated decisions respectively; Purchasing reports 800. S2P reports
812 scored, 196 verified, and a queue total of 50. All five `/health` endpoints
returned HTTP 200.

## Scenario-by-Scenario Results

### Executable scenarios currently present

| Scenario | Requirement | Status | Fix needed |
|---|---|---|---|
| DO-01 | Ranked source-trust factors with differentiated weights | PASS | None |
| DO-03 | Six-factor profile and non-empty centroid history | PASS | None; 6 factors, 50 checkpoints |
| DO-06 | Differentiated DataOps trust distribution | PASS | None; six factors with distinct weights |
| FORK-01 | Trading fingerprint has ten factors | PASS | None |
| FORK-02 | Repeated fingerprint reads preserve ten-factor geometry | PASS at endpoint level | None |
| PILOT-01 | Readiness has ready, coverage, and not-yet fields | PASS | None; ready=true, coverage=800/485, not_yet=false |
| PILOT-02 | Readiness contains coverage/evidence detail | PASS | None |
| PLAT-05 | All five copilot health endpoints return 200 | PASS | None |
| PUR-01 | Supplier fingerprint is non-empty and analyzed | PASS | None; 7 factors, 485 analyzed |
| PUR-02 | Fingerprint has a highest-sigma factor | PASS | None; max sigma=0.157 |
| PUR-04 | Proof and competence curves are non-empty | PASS | None; 800 proof decisions, 92.78% competence accuracy |
| S2P-01 | Score endpoint returns action, confidence, and factors | PASS at endpoint contract level | None indicated by current state |
| S2P-02 | Cold-start score returns confidence and contributions | PASS at endpoint contract level | None indicated by current state |
| S2P-04 | Conservation is GREEN with verified outcomes | PASS | None; 196 verified, GREEN |
| SOC-01 | Trust-score evidence is populated | PASS | None; 12 updates and one trust-score situation |
| SOC-07 | Audit verification succeeds | PASS | None; 4,862-record chain verified |
| TRD-01 | Ten-factor fingerprint has non-zero sigma | PASS | None; 10 factors, all sigma-positive |
| TRD-03 | Category accuracy has verified evidence | PASS | None; 360 overall verified |
| TRD-06 | Ten-factor fingerprint has non-zero learned weights | PASS | None; 10 non-zero weights |

### Explicit audit-request checks

| Scenario | Requirement | Status | Fix needed |
|---|---|---|---|
| SOC-03 rejected-35 | Promoted and rejected runtime evolution evidence | GAP — endpoint returns events, but no verified promoted/rejected summary contract | Narrative adjustment or separate SOC fixture/API; generic preseed inflation is insufficient |
| TRD-01 favorite-setup | Ten factors with non-zero sigma | PASS | None |
| TRD-06 code-free | Ten factors with non-zero learned weights | PASS | None |
| DO-03 twelve-years | Non-empty centroid checkpoints | PASS | None |
| PUR-02 trust-trap | At least one high-sigma factor | PASS | None |
| PUR-04 quiet-week | Non-empty proof-ledger decisions and competence curve | PASS | None |
| S2P-04 earned-autonomy | Verified count greater than zero | PASS | None |
| PLAT-05 five-health | Five health endpoints return 200 | PASS | None |

## Skipped PLANT gaps

These are not failures of the current generic decision count. They require
scenario-specific records or a narrative change:

| Scenario | Current state | Required action |
|---|---|---|
| DO-02 source-lost-trust | Differentiated generic trust exists, but the named source-score fixture is absent | Add a named source-score fixture or keep skipped |
| DO-05 llm-wrong | K14 misleading-evidence fixture/caption absent | Add fixture and UI evidence; do not inflate generic count |
| MACH-01 through-machine | Fixed alert fixture absent | Add `demo-fixed-alert` fixture |
| MACH-02 reshape | No-precedent fixture absent | Add `demo-no-precedent` fixture |
| PUR-03 vendor-cascade | Vendor-cascade order fixture absent | Add named order fixture |
| S2P-05 supplier-enrichment | Supplier-enrichment fixture absent | Add named supplier fixture |
| SOC-02 no-precedent | PL-SOC-1 fixture absent | Add named SOC alert fixture |
| SOC-09 same-alert | Fixed-alert replay fixture absent | Add deterministic replay fixture |
| SOC-10 campaign-path | Linked campaign fixture absent | Add linked campaign fixture |
| TRD-02 Friday-regime | Friday regime fixture absent | Add Friday/regime-tagged fixture |
| TRD-04 revenge-trade | Revenge-trade fixture absent | Add VIX/revenge fixture |

Build, roadmap, and conceptual skips were not treated as preseed gaps:
DO-04, PILOT-03, PLAT-01/02/03/04, PUR-05/06, S2P-03/06, and SOC-04/05/06/08.

## Gaps Found

| Gap | Scenario | Current state | Fix |
|---|---|---|---|
| Inventory mismatch | Audit scope | Repository has 19 executable cases and 28 skipped cases, not 29/18 | Reconcile the catalog/session-state count |
| Named fixture missing | DO-02, DO-05, MACH-01/02, PUR-03, S2P-05, SOC-02/09/10, TRD-02/04 | Generic preseed is populated but does not create these identities or behaviors | Add scenario-specific PLANT fixtures; generic inflation will not close them |
| Unsupported runtime contract | SOC-03 | `/api/evolution/recent-events` is populated, but the rejection-summary contract is not implemented | Narrative adjustment or future endpoint work |
| Count wording risk | Demo narratives that claim a fixed historical volume | Current totals vary: Trading 360, Purchasing 800, DataOps 417, S2P 196 verified, SOC 4,862 | Use live endpoint counts or label quantities as illustrative |

## Recommendations

- No changes were made to `scripts/preseed_all_copilots.py`; the current
  generic preseed is sufficient for the active endpoint-backed scenarios.
- Do not inflate generic decision counts to claim coverage for named PLANT
  scenarios. Add deterministic, scenario-specific fixtures instead.
- Reconcile the “29 LIVE / 18 skipped” session-state statement with the
  current 19 executable / 28 skipped test inventory before using it as a
  coverage metric.
- Adjust narrative claims to the observed counts unless the demo explicitly
  labels them as illustrative.

## Audit conclusion

The current preseed state is sufficient for the currently executable endpoint
checks: all 19 active demo assertions have populated backend evidence at the
required endpoints, and the eight explicit data checks pass except SOC-03's
unsupported promoted/rejected summary contract. It is not sufficient for the
named PLANT scenarios because those require distinct fixtures, not merely more
repeated decisions. No preseed inflation was justified by the observed state.
