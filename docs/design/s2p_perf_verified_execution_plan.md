# S2P backend variance — verified execution plan

Date: 2026-08-10  
Scope: diagnostic review plus the narrowly safe PERF-2 fail-fast guard. No git operations were used.

## 1. Gate resolutions

| Gate | Finding | Status | Evidence |
|---|---|---|---|
| V1 — lock span | The score route acquires the `s2p` mutation lock before `scorer.score()`, then holds it through the conservation snapshot, centroid snapshot, and cache invalidation. The authoritative decision write is inside `scorer.score()`. | VERIFIED | `s2p-copilot/backend/app/routers/s2p.py:1992-2028`; `copilot-sdk/copilot_sdk/scoring/scorer.py:357-413` |
| V2 — pool reality | S2P is live on the AGE product graph. The demo requests pooling at max five and `psycopg_pool` is installed in the active venv, so the code path is eligible for `pooled`; however S2P health/graph status does not expose `connection_mode` or `pool_available`, and pool construction can silently change the mode to `warm_fallback`. Effective live mode is therefore **unverified**, not a production-safe pooled claim. | PARTIAL / PERF-1 REQUIRED | `s2p-copilot/backend/app/s2p_graph_status.py:414-429`; `copilot-sdk/demo.py:119-127`; `ci-platform/ci_platform/graph/age_client.py:51,132-145,184-208` |
| V3 — atomicity | S2P does not call `run_transaction`. The score path has one decision write under its lock; learn/outcome paths perform several receipt, outcome, centroid, conservation, DK, and cache operations under the lock. AGE exposes a transaction facade, but S2P would need adaptation to pass one transaction through the scorer and all persistence helpers. | NO / NEEDS ADAPTATION | `s2p-copilot/backend/app/routers/s2p.py:2186-2237,2303-2361`; `ci-platform/ci_platform/graph/age_graph_store.py:53-67,585-592` |
| V4 — §12b | The authoritative outcome write is direct and not queued. Receipt persistence has a separate outbox fallback, but that is not the outcome/learn write. A score-lock timeout returns before mutation and is §12b-compatible. | VERIFIED; PERF-2 SAFE | `copilot-sdk/copilot_sdk/scoring/scorer.py:1045-1055`; `s2p-copilot/backend/app/routers/s2p.py:1434-1462` |
| V5 — instrumentation | `[S2P-PERF]` logs total, context, combined score+persist, response, snapshot, cache, and enrichment durations. It does not separately log lock acquisition, connection acquisition, or query time; `score+persist` is combined. The stalled sub-step cannot be identified without additional instrumentation. | INSUFFICIENT | `s2p-copilot/backend/app/routers/s2p.py:2058-2070`; `ci-platform/ci_platform/graph/age_client.py:451-487` |
| V6 — true-scale baseline | The live diagnostics response reported 191 verified decisions and the live preview queue returned 200 in 0.024s. That is not the 25,892-decision target scale, and it is not the memo's 0.51s sequential / 1.7s concurrent baseline. Re-measurement at target scale is required. | VERIFIED; RE-MEASURE REQUIRED | `s2p-copilot/backend/app/routers/s2p.py:69-87`; `copilot-sdk/docs/design/c_s2p_perf_lock_design_review_memo_v1.md:44-47` |

## 2. Corrected premises

| Original premise | Corrected premise | Evidence |
|---|---|---|
| The stall is WSL2-only and will not occur on real PostgreSQL. | Unproven. Pool fallback is silent, a five-connection cap is configured, and the same acquisition contention can occur on real PostgreSQL. | `copilot-sdk/docs/design/c_s2p_perf_lock_design_review_memo_v1.md:12,37,44` |
| `AGE_USE_POOL=true` proves S2P has a real pool. | It only requests pooling. The client reports pooled mode before lazy pool construction, then switches to `warm_fallback` if initialization fails. | `ci-platform/ci_platform/graph/age_client.py:132-145,184-208` |
| The current timing is a full-scale baseline. | Current live depth is 191 verified decisions; the 25,892-scale load test has not been reproduced. | `copilot-sdk/docs/design/c_s2p_perf_lock_design_review_memo_v1.md:44`; live `/api/self/diagnostics` response; `s2p-copilot/backend/app/routers/s2p.py:69-87` |
| A write queue is an acceptable latency fix. | Outcome/learn writes remain authoritative and must fail closed; only non-authoritative receipt fallback is currently queued. | `copilot-sdk/docs/design/judgment_memory_v2_9.md:123-135`; `copilot-sdk/copilot_sdk/scoring/scorer.py:1045-1055`; `s2p-copilot/backend/app/routers/s2p.py:1434-1456` |

## 3. PERF-1..4 implementation plan

### PERF-1: Pool activation verification (~0.5d)

- Add `connection_mode`, `pool_available`, configured min/max, and pool initialization failure to the S2P health/diagnostics contract.
- Log the same fields on the `[S2P-PERF]` path.
- Exercise one cold request and concurrent requests after startup; assert the runtime is actually `pooled`, not merely pool-requested.
- If `warm_fallback`, fail the deployment gate and fix the dependency/runtime configuration rather than accepting pooled performance claims.
- The current configured maximum is five, with lazy construction and silent fallback; this is a verification gap, not evidence that S2P is currently warm-fallback. `ci-platform/ci_platform/graph/age_client.py:132-145,184-208`.

### PERF-2: Fail-fast timeout (~0.5d)

Implemented in this review for the score route:

- `S2P_SCORE_TIMEOUT` defaults to `3.0` seconds.
- Score lock acquisition now returns HTTP 503 (`Score path busy — retry`) when the per-domain lock is held too long.
- The existing locked region is released in `finally`; no score, learn, outcome, or queue operation is introduced by the timeout.
- This is §12b-compatible because the rejection happens before the authoritative decision write.

Evidence: `s2p-copilot/backend/app/routers/s2p.py:15-18,61-65,1992-2035`; `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:46-59`.

The timeout bounds lock wait, not an already-running database statement. A separate database statement timeout and per-step connection telemetry belong in PERF-1/V5 follow-up.

### PERF-3: Demo staging (~0d)

- Use a single-worker S2P demo profile for deterministic presentation.
- Warm the AGE pool before the first measured request.
- Pin the preseed dataset and record its decision count, graph mode, and pool mode with the result.
- Do not describe demo latency as production-scale evidence. The current live service is AGE-active but exposes no pool-mode telemetry. `s2p-copilot/backend/app/s2p_graph_status.py:414-429`.

### PERF-4: Pool sizing + PgBouncer (~0.5d)

- After PERF-1 confirms real pooling, benchmark max sizes above the current five-connection cap against the actual worker/concurrency matrix.
- Add PgBouncer only as an operations/deployment change, in transaction mode, after validating AGE session setup and transaction boundaries.
- Re-test PostgreSQL connection limits, p95/p99 latency, error rate, and pool acquisition timeout under concurrent all-AGE traffic.
- No PgBouncer configuration was found in the scanned repository; B8 remains open. `copilot-sdk/docs/design/scan_ce_surfaces_ops_results.md:151`; `copilot-sdk/docs/design/judgment_memory_v2_9.md:1315-1321`.

### PERF-5: Atomic writes (post-raise; deferred)

Coordinate with Commit 3 + WP-1. Adapt S2P's learn/outcome persistence to `AGEGraphStore.run_transaction`, pass the transaction facade through outcome, receipt, centroid checkpoint, conservation, and DK persistence, then narrow or remove the process lock after atomicity is proven. This is not implemented here. `ci-platform/ci_platform/graph/age_graph_store.py:53-67,585-592`.

## 4. Risk register

| Risk | Mitigation |
|---|---|
| Pool silently falls back to one warm connection. | Surface runtime mode and fail the PERF-1 gate on `warm_fallback`. |
| A 503 is mistaken for a successful score. | Client retry with idempotency/event identity; never queue the authoritative score. |
| Timeout does not stop a database call already holding the lock. | Add AGE statement/query timing and a bounded database statement policy in the next pass. |
| Narrowing the lock before atomic writes creates partial learning state. | Keep the lock until PERF-5 transaction coverage and rollback tests pass. |
| Small current graph makes latency look healthy. | Repeat the load test at 25,892 decisions with concurrent workers and report p95/p99. |

## 5. Honesty caveat

“WSL2-only” is unverified. The pool may be in production-real `warm_fallback` mode, and the current S2P status surface cannot prove otherwise. The first pilot load test at 25,892 decisions on real PostgreSQL under concurrency is the gate for any production-safe latency claim. `copilot-sdk/docs/design/c_s2p_perf_lock_design_review_memo_v1.md:12,44-47`; `ci-platform/ci_platform/graph/age_client.py:201-208`.

## 6. Test requirements

| PERF item | Required tests |
|---|---|
| PERF-1 | Unit-test mode selection; startup integration asserts `connection_mode=pooled`; forced pool-construction failure asserts surfaced `warm_fallback`; concurrent smoke test records acquisition and query timings. |
| PERF-2 | Held-lock score request returns 503 within five seconds; normal score returns 200 within three seconds; lock is released after both success and exception. The first two checks are covered by `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:46-59` and the existing 200-path tests. |
| PERF-3 | Repeatable single-worker demo run; warm-up request; pinned preseed count and mode recorded in the run artifact. |
| PERF-4 | Matrix benchmark for pool sizes and worker counts; PgBouncer transaction-mode integration test; p95/p99 and connection exhaustion thresholds. |
| PERF-5 | Transaction rollback on outcome/centroid/checkpoint failure; no partial authoritative outcome; lock narrowing only after conformance passes. |

## Verification notes

- Focused PERF-2 test: 1 passed.
- Normal score-path checks: 2 passed, including HTTP 200.
- Full `test_s2p_score_endpoint.py`: 52 passed, 3 failed; the failures are existing AGE-context/fixture assumptions under the currently live AGE product adapter, not caused by the timeout guard. They concern directed context support and fixture-factor fallback at `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:731,811,853`.
- Full S2P backend suite: 1,668 passed, 31 failed. The failures are distributed across existing factor/context and active-AGE integration assumptions; the focused PERF-2 regression remains green. No failure was attributed to the new timeout lines.
- Live checks: `/health` returned 200; `/api/s2p/graph/status` reported AGE product active; `/api/self/diagnostics` reported 191 verified decisions; `/api/s2p/preview/queue` returned 200 in 0.024s.
