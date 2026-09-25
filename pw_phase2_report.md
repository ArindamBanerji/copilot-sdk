# PW Phase 2 — Final Demo Spec Status

Date: 2026-09-18

## Summary

- Total source specs: 47
- Changed in this phase: PLAT-02 unskipped for the live B7 cross-signal contract.
- Fixtures placed: 6, all tagged `planted: true`.
- Focused fixture-script verification: mypy clean; six JSON files created.
- Live B2/B7 route checks: all three SDK copilots returned 200.
- Playwright execution: blocked before test reporting by `EPERM` writing
  `C:\Users\baner\test-results\.last-run.json`; no application assertion
  result is inferred from that run.

## Spec matrix

| Spec | Status | Dependency / note |
|---|---|---|
| FORK-01 | PASS baseline | Trading fingerprint |
| FORK-02 | PASS baseline | Fingerprint parity |
| MACH-01 | SKIP | Fixture placed, but SOC does not expose a stable analyze/write path |
| MACH-02 | SKIP | Fixture placed, but SOC no-precedent path is not loaded by the live service |
| MACH-04 | SKIP | SOC fingerprint and trajectory endpoints return 404 |
| PILOT-01 | PASS baseline | Purchasing readiness |
| PILOT-02 | PASS baseline | Purchasing readiness evidence |
| PILOT-03 | SKIP | Centroid-history requests time out on SDK services |
| PLAT-01 | SKIP | Shared trace panel not shipped |
| PLAT-02 | READY / unskipped | B7 cross-signal route verified on SDK services |
| PLAT-03 | SKIP | SOC has no fingerprint endpoint at either tested path |
| PLAT-04 | SKIP | SOC has no trajectory endpoint at either tested path |
| PLAT-05 | PASS baseline | Five health checks |
| PUR-01 | PASS baseline | Purchasing fingerprint |
| PUR-02 | PASS baseline | Sigma field |
| PUR-03 | SKIP | Fixture placed; no verified write path for live vendor cascade |
| PUR-04 | PASS baseline | Proof/competence summary |
| PUR-05 | SKIP | Proof-ledger export not shipped |
| PUR-06 | SKIP | Roadmap multi-unit transfer |
| S2P-01 | PASS baseline | Score payload |
| S2P-02 | PASS baseline | Factor vector |
| S2P-03 | SKIP | Promotion ladder not shipped |
| S2P-04 | PASS baseline | Conservation fields |
| S2P-05 | SKIP | Supplier enrichment fixture/UI not verified |
| S2P-06 | SKIP | Roadmap OTIF provenance |
| SOC-01 | PASS baseline | Learning state |
| SOC-02 | SKIP | Fixture placed; SOC alert fixture is not loaded |
| SOC-03 | SKIP | Recent-events exists, but rejection-summary counts are absent |
| SOC-04 | SKIP | Authority-ladder/simulate-failure surface not available |
| SOC-05 | SKIP | Frozen-twin surface not shipped |
| SOC-06 | SKIP | Roadmap investigation trace |
| SOC-07 | PASS baseline | Audit verification |
| SOC-08 | SKIP | Conceptual routing-accuracy claim |
| SOC-09 | SKIP | Both tested analyze paths return 404 |
| SOC-10 | SKIP | Campaign fixture/path not verified |
| TRD-01 | PASS baseline | Ten-factor fingerprint |
| TRD-02 | SKIP | Fixture placed; regime analytics write/read contract unavailable |
| TRD-03 | PASS baseline | Category accuracy |
| TRD-04 | SKIP | Revenge-trade fixture absent |
| TRD-05 | SKIP | Conceptual real-money gate |
| TRD-06 | PASS baseline | Earned weights |
| DO-01 | PASS baseline | Source trust |
| DO-02 | SKIP | Differentiated-source fixture absent |
| DO-03 | PASS baseline | Profile/checkpoints |
| DO-04 | SKIP | Rule-lifecycle endpoint is 404 |
| DO-05 | SKIP | Fixture placed; K14 UI/API contract not present |
| DO-06 | PASS baseline | Trust distribution |

## Fixture inventory

| Fixture | Copilot | Scenario | Verified |
|---|---|---|---|
| `purchasing_drift_pause.json` | Purchasing | PUR-03 | File placed; live mutation not verified |
| `purchasing_twin_init.json` | Purchasing | PUR-05 | File placed; endpoint/UI not verified |
| `trading_regime_break.json` | Trading | TRD-02 | File placed; regime endpoint not verified |
| `soc_decision_trace.json` | SOC | MACH-01 | File placed; analyze path unavailable |
| `soc_recursion_k_delta.json` | SOC | MACH-03 | File placed; live K-routing mutation not verified |
| `dataops_k14_divergence.json` | DataOps | DO-05 | File placed; K14 UI/API contract not present |

## Remaining blocks

SOC-03 has `/api/evolution/recent-events`, but the requested promoted/rejected
summary fields are not present. SOC-09 has no working `/api/alert/analyze` or
`/api/soc/analyze` route. PILOT-03 centroid-history timed out on the SDK
services. MACH-04 has no SOC fingerprint or trajectory route.

## Reproduction note

Run `python scripts/plant_remaining_fixtures.py` to recreate the six JSON
artifacts. The script uses file placement only; it does not claim to mutate
running services without a supported endpoint. Restarted SDK services expose
the B2/B7 routes at `/api/platform/domain-applicability` and
`/api/platform/cross-signals`.
