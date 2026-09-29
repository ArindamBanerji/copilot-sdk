# ResponseMaterializer Verification Report

Date: 2026-09-25. Version 2. Fresh verification of the current working trees; supersedes the earlier unversioned report.

Scope: Trading, Purchasing, DataOps, and S2P. Port 8001 was checked for availability only. No implementation changes, restarts, or persistent test files were made. Only this report and the session log were intentionally edited. Live scoring created one confirmed Trading decision, `a604ca0c0eaf`; no learn request was issued. Existing application behavior may also write observations on GETs.

## Phase 1: Code Audit

| Check | Status | Finding |
|---|---|---|
| 1A Materializer class | FAIL | Required constructor arguments, default TTL 5, refresh guard, TTL check, and refresh-on-miss exist. However, concurrent refresh/invalidation can publish obsolete data as fresh, and a concurrent cold get_or_refresh returns an empty dictionary before the active build completes. Both reproduced with isolated in-memory stores. |
| 1B S2P materializer | PASS | Same core API, default TTL 30, condition-based refresh coordination, lazy nonblocking invalidation, and a generation check that discards invalidated builds. The same in-flight invalidation probe correctly discarded the old result and rebuilt the new value. |
| 1C Old caches removed | FAIL | Named decision/conservation/waste/preview caches are removed. The exact case-insensitive search still matches S2P's clear_summary_cache compatibility no-op, which is not cache storage. Separately, Trading and S2P retain overlapping TabStateCache response caches; S2P explicitly caches materializer-backed responses. The broader no-stacked-caches requirement is unmet. |
| 1D Endpoints wired | PASS | All 16 requested endpoints have materializer-first reads and live fallbacks for absent/stale results. DataOps pipelines is now wired, correcting the earlier report. SDK handlers do not consistently reject materialized error payloads; see additional observations. |
| 1E Background refresh | PASS | Trading, Purchasing, and DataOps await prewarm after seeding and launch loops that sleep 5 seconds between builds. S2P awaits prewarm and launches a 30-second loop, with cancellation/join on shutdown. These are sleep-plus-build intervals. |
| 1F Mutation invalidation | PASS | Wiring exists: SDK score/learn call query_cache_invalidator, connected to synchronous refresh in all three apps; DataOps also invalidates its DI cache. S2P score/learn/outcome call lazy invalidate_materializer. This wiring-only PASS does not establish concurrency correctness: the SDK callback can be dropped during a refresh, and the live immediate mutation check failed. |

Code audit: **4/6 checks passed**.

### Source evidence

Paths are relative to `copilot-sdk` unless prefixed with `../s2p-copilot`.

- SDK class: `copilot_sdk/backend/response_materializer.py`: constructor at line 19, refresh guard at 38, publication at 59, invalidation at 65, reads at 70, refresh-on-miss at 83.
- S2P class: `../s2p-copilot/backend/app/services/response_materializer.py`: refresh captures/checks the generation; invalidation advances it; the route helper rejects error/unavailable responses before live fallback.
- Trading: `apps/trading/backend/app/main.py:642` registers computations with TTL 5; `:172` background loop; `:184` mutation callback; `:669` hook registration; `:838` startup prewarm. Analytics reads the materializer at `apps/trading/backend/app/context_router.py:494`; regime and analytics routers also consult it.
- Purchasing: `apps/purchasing/backend/app/main.py:671` registration with TTL 5; `:764` waste routes; `:895` mutation hook; `:1031` startup prewarm.
- DataOps: `apps/dataops/backend/app/main.py:845` combined invalidation; `:849` registration with TTL 5; `:1093` prewarm. `apps/dataops/backend/app/context_router.py:787` serves materialized pipelines with graph fallback.
- Shared routes: `copilot_sdk/backend/conservation_router.py:46`, `self_computation_router.py:466`, and `scoring_router.py:387` serve conservation, accuracy, and fingerprint responses. Score/learn hooks execute at `scoring_router.py:246` and `:381`.
- S2P: `../s2p-copilot/backend/app/services/s2p_materialization.py:76` creates six responses with TTL 30 using a build-local SnapshotStore. Startup/loop/shutdown are in `backend/app/main.py:585`; queue/suppliers consult the materializer at `backend/app/routers/s2p_preview.py:259` and `:379`; performance/compliance at `s2p_performance.py:242` and `s2p_evidence.py:489`. Mutation invalidations occur at `s2p.py:2432`, `:2727`, and `:2905`.

### Exact old-cache searches

| File | Requested pattern | Result |
|---|---|---|
| Trading state/trading_registry.py | _decisions_cache, _cache[, shared_decisions | No matches. Also no decision_cache or _SharedDecisionStore. |
| Purchasing main.py | _conservation_cache, _waste_cache, _snapshot | No matches. |
| S2P s2p_preview.py | _scored_invoices, _supplier_cache, _SCORED_CACHE | No matches. |
| S2P s2p_performance.py | _SUMMARY_CACHE, SUMMARY_CACHE_TTL | clear_summary_cache() at line 30 matches case-insensitively. Its body is only a compatibility docstring; no response dictionary or TTL remains. |

The S2P symbol match is flagged under P1-3 as requested by the literal search rule, but is not evidence of actual double caching. Concrete overlapping caches are documented separately there.

## Phase 2: Live Probes

Ports 8010, 8020, 8030, 8002, and 8001 were UP. Three rounds used the requested endpoint lists, six worker threads per burst, and a 30-second HTTP timeout. Unlike the supplied timer, this audit closed responses, read complete bodies, decoded JSON, and recorded HTTP/errors: header-only success can hide a failed response. Burst timings include those operations. No retries were included in the timing rounds.

| Check | Status | Measurement |
|---|---|---|
| 2A Trading parallel burst R2 | FAIL | **18.9798s**, gate <1.5s. Analytics connection reset; the other five endpoints returned HTTP 200 in 0.0250–0.0284s. |
| 2A Purchasing parallel burst R2 | PASS | **0.0189s**, gate <1.5s. All 3 endpoints HTTP 200 with valid JSON. |
| 2A DataOps parallel burst R2 | PASS | **0.0168s**, gate <1.5s. All 3 endpoints HTTP 200 with valid JSON. |
| 2A S2P parallel burst R2 | PASS | **0.0404s**, gate <2.0s. All 4 endpoints HTTP 200 with valid JSON. |
| 2B Mutation invalidation | FAIL | Valid score returned HTTP 200; analytics after 0.5s still reported 3,750 and omitted the new decision. Later reads reported 3,751 and included it. |
| 2C Prewarm (R1 fast?) | PASS, limited | R1 was fast for all four apps. Startup code awaits prewarm, but these were already-running services: actual first-request-after-restart behavior was not tested. |

### Timing details

| Round | Trading, 6 endpoints | Purchasing, 3 endpoints | DataOps, 3 endpoints | S2P, 4 endpoints |
|---|---:|---:|---:|---:|
| R1 | 0.0776s | 0.0233s | 0.0121s | 0.0273s |
| R2 | 18.9798s — failed response | 0.0189s | 0.0168s | 0.0404s |
| R3 | 0.0449s | 0.0903s | 0.0162s | 0.0379s |

Trading R2 analytics failed with ConnectionResetError 10054: an existing connection was forcibly closed by the remote host. All other timing requests completed with HTTP 200, valid JSON, and no top-level error payload. Successful Trading analytics bodies were 132,126 bytes. Subsequent urllib baseline reads also timed out; a direct http.client connection completed the mutation experiment. The reset's server/network cause was not established; no attribution to materializer code is claimed.

### Mutation probe details

The supplied probe needs two corrections for the current contract:

1. Analytics exposes `total_trades`, not `total`; defaulting an absent total to zero cannot validate a mutation.
2. `momentum` is not a Trading category. The supplied payload returned HTTP 400. The current preset lists trend_following, mean_reversion, event_driven, income_strategy, and scalp_intraday (`copilot_sdk/scoring/presets/trading.py:38`).

The completed experiment used http.client, category trend_following, the six supplied factor values, and 0.5 for each of the four additional current factors: signal_confidence, options_delta_exposure, options_iv_percentile, and options_gamma_risk.

| Step | Result |
|---|---|
| Before | HTTP 200; 0.0684s; total_trades=3750. |
| Score | HTTP 200; 0.9241s; decision a604ca0c0eaf. |
| After 0.5-second wait | HTTP 200; 0.0172s; total_trades=3750; decision absent from analytics trade IDs. |
| Subsequent read-only checks | total_trades=3751; decision present in all three checks, taking 0.0521s, 0.0567s, and 0.1180s. Exact first-visibility delay was not measured. |

This proves eventual visibility but fails the immediate check. The isolated SDK race below is consistent with the result; the live process was not instrumented to prove that exact interleaving. S2P mutation behavior was audited in code and with an isolated class probe, not by issuing a live S2P mutation.

## P1 Issues Found

1. **SDK mutation refresh can be lost during an active build.** Refresh returns immediately when another refresh is active; all three SDK app mutation callbacks call only refresh. They neither invalidate the active generation nor request a subsequent build. Separately, invalidate only resets the timestamp, so an old in-flight build can overwrite that invalidation with a new freshness timestamp. In an event-coordinated in-memory probe, a build captured value 1, the store changed to 2, and the mutation callback returned early: get returned 1 as fresh. Calling invalidate during the build likewise left both get and get_or_refresh returning 1 afterward. The S2P control discarded the old build (get returned None) and returned 2 on get_or_refresh. Live Trading also failed the 0.5-second visibility gate.
2. **Trading fails the R2 live burst gate.** One of six responses reset after approximately 19 seconds. R3 recovery does not erase the failed round. Retain full-body validation when investigating and retesting; the original header-only timer can miss partial-response failures.
3. **Overlapping response caches remain.** Trading creates a 5-second TabStateCache at `apps/trading/backend/app/state/trading_registry.py:53`, registering independently computed vol-Sharpe, trajectory, and conservation at lines 147–155. S2P creates a 5-second TabStateCache at `../s2p-copilot/backend/app/state/s2p_registry.py:40`; conservation reads the response materializer, and preview-queue/evidence-compliance registrations call materializer-backed handlers. The tab-state path therefore retains another response copy despite removal of the named local caches. This differs from the earlier Trading decision-cache finding, which is resolved. The requested literal pattern also flags clear_summary_cache(); that specific match is a harmless no-op, not storage. Direct endpoint timing does not establish freshness of tab-state copies.

### Additional architecture observations

- **SDK computations do not consistently use one shared snapshot.** Trading fingerprint, trajectory, measurement, and conservation builders call the live scorer instead of consuming only shared rows (`apps/trading/backend/app/main.py:598` through the registration at line 642). For example, trajectory reads verified decisions again at `copilot_sdk/scoring/scorer.py:1897`; measurement/composite-gate helpers also read verified history. Purchasing and DataOps conservation builders similarly use live scorer state. Atomic publication does not guarantee a single underlying graph snapshot. S2P's build-local SnapshotStore is closer to the validated design.
- **Trading refresh is not strictly read-only.** Its fingerprint builder calls scorer_proxy.fingerprint with the default persist=True; the scorer can call write_fingerprint (`scorer.py:1316`, `:1767`, `:1817`). A signature guard skips unchanged writes, so this is not a claim of a write every five seconds. It remains a side-effecting computation inside display refresh.
- **SDK cold misses and error fallback are incomplete.** An isolated concurrent cold get_or_refresh returned an empty dictionary while the active build later produced value 2. Failed computations become an error/unavailable dictionary, but SDK route helpers generally accept any dictionary as a hit instead of falling back. S2P explicitly filters this sentinel. Live graph failures were not injected.
- **TTL semantics permit stale reads during refresh.** Both classes serve a prior published result while refreshing before applying the ordinary TTL check. This permits stale data during refresh rather than imposing a strict maximum age. S2P invalidation clears prior payloads and guards publication by generation; the SDK does neither effectively across an in-flight invalidation.
- **Startup confidence is limited.** No service was restarted; no in-process build/version or cache-hit instrumentation was used. Current source wiring and observed live behavior are reported separately. The prior slow R1 was not reproduced; a fast warm-stack R1 cannot alone prove startup prewarm.

## Verdict

**NEEDS FIXER**

Purchasing, DataOps, and S2P pass the measured timing gates; all requested endpoint paths are wired. Trading fails one complete-response burst and immediate post-score visibility. The shared SDK refresh race is independently reproducible, and overlapping tab-state response caches remain. Fix and retest these gaps; the results do not establish that the overall materialization design needs replacement. The supplied 1,835x experiment was context, not a benchmark reproduced by this HTTP audit.
