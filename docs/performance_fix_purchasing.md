# Purchasing Performance Fix

## Accumulation Bug

Root cause: the waste endpoints repeatedly performed uncached full `get_all_decisions` scans. Recreated `WasteTracker` instances then rebuilt the same grouped profiles on every request, so repeated dashboard calls showed rising latency under AGE load rather than reusing a bounded read snapshot.

Fix: added an app-scoped five-second shared decision snapshot and routed both waste endpoints through it. The snapshot is replaced on expiry, so it cannot grow across requests.

## Shared Cache

Conservation status now reuses a five-second payload snapshot, avoiding repeated scorer/graph-wide recomputation during parallel dashboard loads.

## Limit Pushdown

Purchasing mounts the shared self-computation router, whose decisions endpoint now calls `get_decisions(domain, limit=N)` and uses `count_decisions` for the unfiltered total instead of materializing all decisions and slicing in Python.

## Validation

- Purchasing waste/conservation/self-decisions tests: **4 passed**.
- Full Purchasing suite reached 453 passed before an unrelated existing health-contract failure (`phase` missing under the test environment).
- `python -m mypy apps/purchasing/backend/app/main.py --config-file pyproject.toml`: clean.
- Live port 8020 timing was not available in this environment; no unverified under-two-second claim is made.
