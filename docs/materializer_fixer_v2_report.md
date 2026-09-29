# ResponseMaterializer Fixer v2 Report

Date: 2026-09-25.

Status: **PASS — targeted fixes implemented and validated.** All four final suites completed successfully, with pass counts above the stated baselines. Purchasing retains one existing environment-guarded AGE skip.

## What changed

- `copilot_sdk/backend/response_materializer.py`: ported generation-based invalidation and condition-coordinated refresh from S2P, retaining the SDK shared-input computation API and default TTL of 5 seconds.
- Replaced the existing optional dynamic lookup of verified decisions with the explicit domain-scoped `store.get_verified_decisions(self._domain)` graph protocol call, matching S2P and satisfying the repository's Rule #72 enforcement. Test stores now implement this required graph method.
- Trading, Purchasing, and DataOps `app/main.py`: replaced the mutation refresh helpers with `_invalidate_materializer()`. They call `materializer.invalidate()` only. Startup prewarm and background refresh remain intact.
- `copilot_sdk/backend/scoring_router.py`: invalidate the materializer before applying tab-state invalidation for both score and learn. Otherwise, eager tab-state recomputation could copy the old materializer response before it was invalidated.
- `apps/trading/backend/app/state/trading_registry.py`: replaced nine independent computation registrations with reads from the app materializer. All 43 static keys, URLs, schemas, invalidation metadata, dynamic keys, and non-overlapping computations remain.
- `apps/trading/backend/app/services/trading_materialization.py`: moved the existing Trading builders from main into one factory. The app and registry tests use that factory, keeping the response computations in one place.
- Added deterministic concurrency, lazy-callback, deduplication, and score/learn ordering regression coverage. Updated the two existing registry test factories to supply the shared materializer. No existing tests were removed.
- Renamed the earlier audit to [materializer_verification_v2.md](materializer_verification_v2.md), as requested.

## Generation guard design

Refresh acquires the condition, captures the current generation, then builds outside the lock. Publication reacquires the condition and compares the captured generation with the current one. Matching builds publish atomically and receive a completion timestamp; mismatched builds are discarded.

Invalidation increments the generation, clears published payloads, and clears the timestamp. It does not wait for graph I/O or start a refresh. An in-flight old build therefore cannot republish an invalidated response.

Concurrent refresh callers wait on a threading.Condition. Completion and source failures notify all waiters. get_or_refresh rechecks freshness after joining; if invalidation discarded the build, it can rebuild the new generation. Retries are bounded at three under continuous writes, returning None rather than stale data or an invented empty response. Valid empty dictionaries, lists, zero, and false values remain intact.

The nonblocking get method retains prior payloads while an ordinary background refresh is running, as requested. Once invalidate clears those payloads, get returns None. Existing HTTP handlers using get can take their live fallback; get_or_refresh consumers lazily rebuild the materializer.

## Mutation callbacks

All three app callbacks now call invalidate rather than refresh. DataOps still invalidates its separate DI query cache. The background loops still refresh every 5 seconds plus build time, and startup still awaits prewarm.

The shared score/learn router invalidates the authoritative snapshot before tab-state recomputation. The callback itself remains lazy. Existing critical tab-state reads during mutation processing may then request a rebuild through get_or_refresh; this does not introduce a direct refresh call in the mutation callback.

## Trading tab-state deduplication

| Tab-state key | Materializer key |
|---|---|
| analytics | analytics |
| measurement-state | measurement_state |
| accuracy | accuracy_by_category |
| fingerprint | fingerprint |
| vol-sharpe | vol_sharpe |
| vrp-attribution | vrp_attribution |
| dispersion-follow | dispersion_follow |
| trajectory | trajectory |
| conservation | conservation |

Both compute_fn and service_fn for these entries call the materializer-backed helper. It rejects unavailable/error payloads instead of treating them as valid tab-state responses. It does not independently recompute on a miss.

Regime-VRP, journal projections, market data, and other non-overlapping entries keep their existing computations. The tab-state envelope cache remains, as allowed by the clarified task; duplicate domain computations have been removed, not the frontend's key contract or every stored response copy. S2P implementation files were not edited.

## Validation

Pre-implementation source inspection confirmed the SDK had no generation counter, and all three mutation helpers called refresh through a local callable alias. Consequently, the prompt's literal materializer.refresh() grep did not itself identify the mutation calls. AST-based post-checks confirmed all three mutation helpers call invalidate and contain no refresh call; startup and background refresh remain.

| Check | Result |
|---|---|
| SDK full suite: python -m pytest tests/ -q --timeout=120 -x | 3,725 passed; 1026.72s; baseline stated as 3,715 |
| Trading full suite | 1,473 passed; 348.02s; baseline stated as 1,471 |
| Purchasing full suite | 833 passed, 1 skipped; 409.85s; baseline stated as 453 |
| DataOps full suite | 434 passed; 150.60s; baseline stated as 433 |
| Focused materializer regression tests | 9 passed |
| Focused Trading registry/equivalence/callback tests | 15 passed |
| Score/learn materializer-to-tab-state ordering regression | 1 passed |
| Requested materializer mypy command | PASS |
| Materializer mypy without the repository's backend ignore_errors override | PASS |
| Trading factory and registry mypy from the backend import root | PASS |
| Generation/Condition and callback AST checks | PASS |
| Registration inspection | All 9 overlapping entries use materializer reads |
| Diff whitespace and new-file syntax checks | PASS |

The Purchasing skip is its existing live AGE test, guarded by AGE availability. No new skips were introduced. The first SDK run stopped after 3,099 passes on Rule #72's rejection of the existing dynamic verified-decision lookup. The source was corrected without weakening the enforcement test. The enforcement, concurrency, and score/learn ordering checks then passed together (13 tests), and all four full suites were restarted. The final SDK run includes the new ordering regression.

Full-suite logs: [SDK](../.codex_tmp/materializer_v2_sdk.log), [Trading](../.codex_tmp/materializer_v2_trading.log), [Purchasing](../.codex_tmp/materializer_v2_purchasing.log), [DataOps](../.codex_tmp/materializer_v2_dataops.log).

### Concurrency reproduction

The prompt's sample was adapted to the real SDK API: the fake store implements get_all_decisions and get_verified_decisions with a domain argument, and computations receive the shared dictionary. Threading events replace timing-dependent sleeps so the old snapshot is definitely captured before invalidation.

1. Publish value 1.
2. Start another build capturing value 1 and hold it at a barrier.
3. Change the store to 2 and invalidate without waiting for the build.
4. Confirm get returns None while the invalidated build remains active.
5. Release the build and confirm its result was discarded.
6. Confirm get_or_refresh rebuilds and returns value 2.

Standalone result:

```text
PASS: Generation guard works. Old build discarded, rebuilt with new value.
```

Additional regression tests cover concurrent cold reads joining a build, invalidation while a reader is waiting, independent ownership of returned data, source failure notification/recovery, TTL boundaries, valid falsey payloads, and bounded repeated invalidation.

## Scope and remaining verification

No live-stack restart or live score mutation was performed for this coding task. The earlier Trading connection reset was not diagnosed here, so this report does not claim a new live latency gate result. The audit's other observations about snapshot input reads and fingerprint persistence remain outside these targeted fixes.
