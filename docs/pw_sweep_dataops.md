# DataOps PW Sweep Report — 2026-09-24

## Endpoint Changes That Caused Failures

| Endpoint | Old shape | New shape | Specs affected |
|---|---|---|---|
| `/api/context/pipelines` | Fixture-backed pipeline payload | Graph-backed pipeline payload | Dashboard/Insight UI consumers; no direct stale assertion found |
| `/api/context/transformations/*` | Fixture-backed transformation payload | Graph-backed transformation payload | Insight/flow UI consumers; no direct stale assertion found |
| `/api/context/process-timeline` | Fixture-backed timeline payload | `{ activities, source, total }` graph-backed payload | Insight/flow UI consumers; no direct stale assertion found |
| `/api/conservation/status` | Earlier conservation response | Unified fields including `engine`, `g_abs`, `g_rel`, `g_rate`, category coverage, and `reason` | `graph-status.spec.ts`, `new-surfaces.spec.ts`, `sweep.spec.ts`; existing assertions already match |
| `/health` | Older health payload | Unified `ready`, `status`, graph identity, cache telemetry, and product-claim fields | `hot-path-cache.spec.ts`, health checks; existing assertions already match |
| `/api/learn` | Learning result only | Learning result plus structured persistence status | Flow tests only wait for successful response; no stale shape assertion found |

## Failures Found

| Spec:line | Test name | Old assertion | New assertion | Root cause |
|---|---|---|---|---|
| `dataops/acquisition.spec.ts:10` | acquisition panel visible / recommendations | 15-second heading wait | 30-second heading wait | Graph-backed page load can exceed the former fixture-backed latency; heading text remains current |
| `dataops/curve.spec.ts:7` | disruption annotation visible | 10-second `expectAnyText` default | 20-second default | Graph-backed curve requests take longer to settle |
| `dataops/centroid-quality.spec.ts:7,24,41,61` | centroid-history contract tests | Playwright request default timeout | Explicit 30-second request timeout | Graph-backed history/counterfactual queries exceed the former 10-second request timeout |
| `dataops/compounding-panels.spec.ts`, `cohort-status.spec.ts`, others | UI panel tests | Existing assertions | Not changed | Full-run failures were frontend/backend startup or AGE connection timeouts, not response-shape mismatches |

## Files Modified

| File | Lines changed | What changed |
|---|---:|---|
| `e2e/helpers/ui.ts` | 3 | Increased default DataOps navigation/readiness/text waits for graph-backed responses; added explanatory comment |
| `e2e/dataops/acquisition.spec.ts` | 1 | Increased the explicit acquisition-heading wait to 30 seconds |
| `e2e/dataops/centroid-quality.spec.ts` | 5 | Added 30-second timeouts to graph-backed history/counterfactual requests |

## Summary

Total specs: 265. Initial live attempt: 27 passed, 2 flaky, 1 failed before interruption because the DataOps services were not running. After starting the local backend/frontend, affected targeted specs passed: acquisition/curve 8/8 and centroid-quality 5/5. The subsequent full run was interrupted after AGE/backend saturation produced startup and connection-timeout failures; therefore the required full-suite after-count is not claimed as zero in this environment.
