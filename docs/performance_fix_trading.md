# Trading Performance Fix

## Changes

- Trading tab state now uses a five-second TTL and a shared graph-store decision wrapper, so materialized computations reuse the same `get_all_decisions` result.
- Live clustering-adjusted Sharpe uses `n_boot=50` by default; callers can pass a larger value for batch precision.
- The shared tab-state cache supports opt-in TTL expiry; S2P enables the same five-second policy.

| Endpoint | Before | After R1 | After R2 | Method |
|---|---:|---:|---:|---|
| `/api/context/analytics` | 28s tab load | unavailable | unavailable | Port 8010 not serving; probe timed out after 5.18s / 5.04s |
| `/api/trading/measurement-state` | 28s tab load | unavailable | unavailable | Port 8010 not serving; probe timed out after 5.02s / 5.02s |
| `/api/trading/regime/detail` | 28s tab load | unavailable | unavailable | Port 8010 not serving; probe timed out after 5.03s / 5.02s |
| `/api/trading/analytics/vol-sharpe` | 28s tab load | unavailable | unavailable | Port 8010 not serving; probes timed out after 5.02s and 12.31s |
| `/api/self/decisions` | 28s tab load | unavailable | unavailable | Port 8010 not serving; probes timed out after 5.02s and 11.28s |

## Validation

- `python -m pytest apps/trading/backend/tests/ -q --timeout=120 -x`: **1471 passed**.
- `python -m mypy apps/trading/backend/app/ --config-file pyproject.toml`: pre-existing repository import/stub and typing errors (337 errors); the command also reports the new cache value as `Any` only before the explicit cast was added.
- Endpoint timing gate: blocked by unavailable local service on port 8010; no endpoint result is reported as under two seconds.
