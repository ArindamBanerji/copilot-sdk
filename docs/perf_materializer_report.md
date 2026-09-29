# Performance Materializer Report - 2026-09-25

## Summary

Implemented an app-scoped `ResponseMaterializer` for read-only Performance/display endpoints. The materializer fetches all decisions and verified decisions once per refresh, computes registered response payloads, and serves fresh prepared responses directly from `app.state.materializer`.

S2P and SOC were intentionally not wired in this pass.

## Files Changed

| File | Change |
|---|---|
| `copilot_sdk/backend/response_materializer.py` | Added shared `ResponseMaterializer` with non-overlapping refresh, TTL freshness, deep-copy reads, lazy refresh, and invalidation. |
| `copilot_sdk/backend/conservation_router.py` | Extracted `build_conservation_status()` and made `/api/conservation/status` consult the materializer first. |
| `copilot_sdk/backend/self_computation_router.py` | Added materializer first-read hooks for default `accuracy-by-category`, `centroid-history`, and `evolution/summary`. |
| `copilot_sdk/backend/scoring_router.py` | Added materializer first-read hooks for `fingerprint`, `trajectory`, and both measurement-state routes. |
| `apps/trading/backend/app/main.py` | Installed Trading materializer, startup prewarm, 5s background refresh, and score/learn refresh callback. |
| `apps/trading/backend/app/context_router.py` | Split analytics into a decisions-based builder and wired `/api/context/analytics` to the materializer. |
| `apps/trading/backend/app/routers/analytics.py` | Wired vol-sharpe, VRP attribution, and dispersion follow analytics to the materializer. |
| `apps/trading/backend/app/routers/regime.py` | Wired default `/api/trading/regime/detail` to the materializer with live fallback for parameterized requests. |
| `apps/purchasing/backend/app/main.py` | Replaced local decision/conservation TTL snapshots with the materializer; wired waste responses, conservation, startup/background refresh, and score/learn refresh. |
| `apps/dataops/backend/app/main.py` | Installed DataOps materializer and combined its refresh with existing DI query invalidation. |
| `apps/dataops/backend/app/context_router.py` | Wired `/api/context/accuracy-by-category` to the materializer. |

## Cache Replacement

| App | Previous cache | Replacement |
|---|---|---|
| Trading | HTTP handlers bypassed the tab-state registry cache; selected Performance endpoints independently fetched graph rows. | One `ResponseMaterializer` on `app.state.materializer` builds selected display payloads from one shared refresh. |
| Purchasing | `decision_snapshot` and `conservation_snapshot` local 5s TTL dictionaries in `main.py`. | Removed those local TTL dictionaries; waste/par helpers and conservation helpers read the app materializer first. |
| DataOps | No Performance-wide materializer; DI query cache remained separate for DI-specific work. | Added materializer for shared graph-backed display responses; preserved DI cache and invalidated both after score/learn. |

## Trading Materialized Keys

| Key | Served routes |
|---|---|
| `analytics` | `/api/context/analytics` |
| `conservation` | `/api/conservation/status` |
| `accuracy_by_category` | `/api/self/accuracy-by-category` |
| `fingerprint` | `/api/fingerprint` |
| `trajectory` | `/api/trajectory` |
| `measurement_state` | `/api/measurement-state`, `/api/trading/measurement-state` |
| `regime_detail` | `/api/trading/regime/detail` default query |
| `vol_sharpe` | `/api/trading/analytics/vol-sharpe` |
| `vrp_attribution` | `/api/trading/analytics/vrp-attribution` |
| `dispersion_follow` | `/api/trading/analytics/dispersion-follow` |

## Performance Measurement

Measured after restarting the Trading backend on port `8010` from this checkout.

| Round | 6 parallel endpoints |
|---|---:|
| Round 1 | 0.08s |
| Round 2 | 0.06s |
| Round 3 | 0.14s |

Endpoints measured:

```text
/api/context/analytics
/api/conservation/status
/api/self/accuracy-by-category
/api/fingerprint
/api/trading/regime/detail
/api/trading/analytics/vol-sharpe
```

Gate met: Round 2+ under 1.5s.

## Validation

| Command | Result |
|---|---|
| `python -m pytest tests/ -q --timeout=120 -x -k "analytics or conservation or fingerprint"` | 246 passed, 3469 deselected |
| `python -m pytest apps/trading/backend/tests/ -q --timeout=120 -x` | 1471 passed |
| `python -m pytest apps/purchasing/backend/tests/ -q --timeout=120 -x` | 832 passed, 1 skipped |
| `python -m pytest apps/dataops/backend/tests/ -q --timeout=120 -x` | 433 passed |
| `python -m mypy copilot_sdk/backend/response_materializer.py --config-file pyproject.toml` | Success |
| `python -m py_compile ...` on changed Python files | Success |

## Notes

- The materializer is optional at route level. If it is absent, stale, or missing a key, routes fall back to their live computation.
- Mutation invalidation is implemented via the existing `query_cache_invalidator` hook in `create_scoring_router`; score/learn refresh the app materializer after successful mutations.
- Trading `regime_detail` materialization preserves the live route's journal overlay by using `_journal_records()` with the materialized graph rows.
- Purchasing `/api/health` now preserves graph-health fields and also includes scorer health fields expected by existing backend tests.
