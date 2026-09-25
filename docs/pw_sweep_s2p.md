# S2P PW Sweep Report — 2026-09-24

## Endpoint Changes That Caused Failures

| Endpoint | Old shape | New shape | Specs affected |
|---|---|---|---|
| `/api/s2p/preview/queue` | Fixture-sized queue | Graph-backed queue with 313 pending records | `active-age-smoke.spec.ts`, `flows.spec.ts`, `sweep.spec.ts`, triage flows |
| `/api/s2p/preview/suppliers` | Fixture supplier collection | Graph-backed collection with 79 suppliers | Supplier/profile UI consumers; no stale direct shape assertion found |
| `/api/conservation/status` | Prior conservation payload | Unified status with engine, G-rate layers, coverage, and reason | `sweep.spec.ts`, governance/status consumers; existing assertions are compatible |
| `/health` | Prior health contract | Unified readiness, graph identity, and service fields | Fixture health checks; no stale assertion found |
| `/api/learn` | Learning result only | Learning result plus structured persistence status | Learn-flow tests wait for successful responses; no stale shape assertion found |
| `/api/s2p/performance/summary` | Fixture performance data | Graph-backed performance summary | Performance UI consumers; no stale direct shape assertion found |

## Failures Found

| Spec:line | Test name | Old assertion | New assertion | Root cause |
|---|---|---|---|---|
| `s2p/active-age-smoke.spec.ts:67` | active AGE smoke triage queue | 10-second queue-content wait | 60-second graph-backed queue-content wait | Queue query loads 313 pending graph records and exceeded fixture-era latency |
| `s2p/cohort-status.spec.ts:36` | cohort-status endpoint contract | Playwright request default timeout | Endpoint assertion retained; service request requires a healthy live backend | AGE/backend saturation caused a 10-second request timeout, not a response-shape mismatch |
| `s2p/cross-copilot-signal.spec.ts:124` | signal banner shows supplier | Existing supplier text assertion | Assertion retained | S2P frontend was unavailable; failure occurred during page/API startup, not signal payload shape |

## Files Modified

| File | Lines changed | What changed |
|---|---:|---|
| `e2e/s2p/helpers.ts` | 3 | Increased triage queue wait to 60 seconds for graph-backed queue loading |
| `e2e/s2p/active-age-smoke.spec.ts` | 1 | Increased queue-content assertion timeout to 60 seconds |
| `e2e/s2p/sweep.spec.ts` | 1 | Increased direct preview-queue request timeout to 30 seconds |

## Summary

Total specs: 218. Initial run reached 24 passed and 3 failed before interruption; 191 did not run. The failures were service latency/startup failures. The changed assertions could not be revalidated end-to-end because the S2P frontend’s Vite config could not start in the restricted environment and the AGE backend saturated on graph queries. No stale response-shape assertion was identified.
