# ResponseMaterializer Verification Report v3

Date: 2026-09-25 (America/Los_Angeles). Live probes: 2026-09-26 01:27:23-01:28:31 UTC.

**Verdict: SHIP.** All four code checks and the requested live timing, mutation-visibility, and R1 warmth gates passed after fixer v2.

This was a read-only source audit plus the authorized live probes. No code changes or process restarts were performed. SHA-256 checks confirmed that the seven audited SDK/Trading/Purchasing/DataOps source files were unchanged during verification. One Trading decision was created by the successful mutation probe; no learn or cleanup mutation was issued. This report is the only file written for this verification.

## Phase 1: Code Audit

| Check | Status | Finding |
|---|---|---|
| 1A SDK generation guard | PASS | `copilot_sdk/backend/response_materializer.py:32` creates a `threading.Condition(threading.RLock())`; generation starts at zero at line 36. Refresh captures the generation before building and publishes only when it still matches. Its finally block clears the active flag and notifies all waiters. Invalidation advances the generation and clears published data without rebuilding. |
| 1B Mutation callbacks | PASS | Trading `main.py:172`, Purchasing `main.py:179`, and DataOps `main.py:150` call `materializer.invalidate()`. AST inspection found no refresh call in these callbacks. Startup and background refresh calls remain in place. |
| 1C Trading TabStateCache | PASS | All nine overlapping entries use the materializer helper in both the compute map and service-function map. The helper calls `materializer_provider().get_or_refresh(key)` and rejects absent/unavailable results. Builders reside in `services/trading_materialization.py`. |
| 1D Score/learn ordering | PASS | In `copilot_sdk/backend/scoring_router.py`, score calls `query_cache_invalidator()` at line 246 before tab-state invalidation at line 247. Learn does the same at lines 381 and 382. App wiring connects the callback to materializer invalidation. |

The nine Trading aliases are analytics, measurement_state, accuracy_by_category, fingerprint, vol_sharpe, vrp_attribution, dispersion_follow, trajectory, and conservation. Their registrations delegate to materialized responses rather than independently rebuilding those computations. TabStateCache still holds its response envelopes; this passes the requested deduplication rule, which explicitly permits materializer-backed entries.

Concurrent `get_or_refresh()` joins the active refresh through the Condition, rechecks freshness, and retries up to three times if invalidated builds were discarded. It returns None under sustained invalidation rather than manufacturing an empty dictionary. Ordinary `get()` can serve the previous publication during refresh, but invalidation clears that publication immediately. The live probe below confirms mutation visibility; it does not deliberately force an in-flight publication race.

## Phase 2: Live Probes

### Port gate

All five required localhost ports were UP: Trading 8010, Purchasing 8020, DataOps 8030, S2P 8002, and supporting service 8001. Port 8001 was checked for connectivity only, as requested.

### 2A: Full-body parallel endpoint timing

Each burst used six worker threads and a 30-second HTTP timeout per request. Every response body was fully read and decoded as JSON. Validation required HTTP 200 and rejected error/unavailable status payloads and nonempty top-level errors. Three rounds ran with a one-second pause between rounds.

| Copilot | Endpoints per round | R1 | R2 | R3 | R2 gate | Result |
|---|---:|---:|---:|---:|---:|---|
| Trading | 6 | 0.0790 s | 0.0470 s | 0.1250 s | <1.5 s | PASS |
| Purchasing | 3 | <0.016 s* | 0.0150 s | 0.1720 s | <1.5 s | PASS |
| DataOps | 3 | 0.0310 s | <0.016 s* | 0.0150 s | <1.5 s | PASS |
| S2P | 4 | 0.0620 s | 0.0320 s | 0.0470 s | <2.0 s | PASS |

*The supplied timing method uses `time.monotonic()`, backed here by Windows GetTickCount64 with 0.015625-second resolution. Purchasing R1 and DataOps R2 measured 0.0000 seconds because no clock tick elapsed; these are below clock resolution, not zero-duration requests. Other timings are also quantized at approximately 16 ms.*

**All 48 timing responses passed:** complete bodies, HTTP 200, valid JSON, and no detected error payloads. There were no connection resets or HTTP timeouts. All R3 bursts also met the corresponding R2 limits.

| Copilot | Endpoints checked in every round |
|---|---|
| Trading | `/api/context/analytics`, `/api/conservation/status`, `/api/self/accuracy-by-category`, `/api/fingerprint`, `/api/trading/regime/detail`, `/api/trading/analytics/vol-sharpe` |
| Purchasing | `/api/conservation/status`, `/api/purchasing/waste/summary`, `/api/self/accuracy-by-category` |
| DataOps | `/api/conservation/status`, `/api/context/pipelines`, `/api/self/accuracy-by-category` |
| S2P | `/api/s2p/preview/queue`, `/api/s2p/preview/suppliers`, `/api/s2p/performance/summary`, `/api/s2p/evidence/compliance` |

Round starts, UTC on 2026-09-26: R1 01:27:23.419; R2 01:27:24.603; R3 01:27:25.708.

### 2B: Mutation invalidation

**PASS — visible at the first 0.5-second check.** Trading analytics increased from 3,751 to 3,752 and included the new decision ID `d037fc576ae8` in its contrast-card trade IDs. Both the count and decision identity remained visible at the 2-second and 6-second checks.

The supplied score payload was rejected with HTTP 400 because these factors are absent from the current Trading preset: conviction_level, portfolio_heat, risk_reward_ratio, thesis_alignment, and time_horizon. That request returned no decision ID. The probe then used current factors from `copilot_sdk/scoring/presets/trading.py`; this was a probe-fixture correction, not a source change.

The successful request was:

```json
{
  "category": "trend_following",
  "metadata": {
    "ticker": "MUTATION_TEST",
    "source": "materializer_verification_v3"
  },
  "factors": {
    "signal_alignment": 0.8,
    "market_regime": 0.6,
    "position_sizing": 0.6,
    "timing_quality": 0.6,
    "risk_reward_actual": 0.7,
    "emotional_indicator": 0.5,
    "signal_confidence": 0.7,
    "options_delta_exposure": 0.5,
    "options_iv_percentile": 0.5,
    "options_gamma_risk": 0.5
  }
}
```

All timestamps below are UTC on 2026-09-26.

| Step | Request started | Response completed | HTTP | Request duration | total_trades | New decision visible |
|---|---|---|---:|---:|---:|---|
| Baseline analytics | 01:28:21.260 | 01:28:21.353 | 200 | 0.0966 s | 3,751 | N/A |
| Supplied score payload | 01:28:21.353 | 01:28:21.378 | 400 | 0.0254 s | N/A | No decision created |
| Corrected score payload | 01:28:21.378 | 01:28:24.837 | 200 | 3.4549 s | N/A | ID returned |
| Analytics at +0.5 s | 01:28:25.338 | 01:28:25.399 | 200 | 0.0648 s | 3,752 | Yes |
| Analytics at +2.0 s | 01:28:26.838 | 01:28:26.894 | 200 | 0.0618 s | 3,752 | Yes |
| Analytics at +6.0 s | 01:28:30.838 | 01:28:30.903 | 200 | 0.0672 s | 3,752 | Yes |

Offsets are measured from the successful score response, consistent with the requested probe. The first analytics request began at +0.5005 seconds and its complete validated response arrived at +0.5654 seconds. The successful score itself took 3.4549 seconds; that POST latency is separate from the post-acknowledgment visibility gate. Mutation durations use the high-resolution `time.perf_counter()` clock, so minor differences from wall-clock timestamp subtraction are expected.

### 2C: Prewarm assessment

**PASS for the requested R1 gate:** every copilot's R1 burst was below 3 seconds; the slowest was Trading at 0.0790 seconds. SDK source also retains awaited startup refresh before starting periodic refresh.

These results are consistent with successful prewarming after the user-reported restarts. This audit did not restart the processes or instrument their first request after boot, so fast R1 responses alone do not independently prove startup ordering.

## Comparison to v2 Findings

| Prior P1 | v3 status | Evidence |
|---|---|---|
| P1-1: SDK mutation refresh lost during an active build | RESOLVED for this re-verification | Generation guard and Condition waiting are present; invalidation clears data lazily; score/learn ordering is correct. Live analytics showed the new decision at the first 0.5-second check. The live probe confirms visibility, without deliberately scheduling the original race. |
| P1-2: Trading R2 took 18.98 seconds with a connection reset | RETEST PASSED | Trading R2 now took 0.0470 seconds, with all six responses valid. All 18 Trading timing responses across three rounds passed without resets. This establishes that the failure did not recur in this run, rather than identifying the historical reset's cause. |
| P1-3: Trading TabStateCache independently duplicated materializer computations | RESOLVED | All nine overlapping entries delegate to materializer responses in both registration maps. Nonoverlapping entries remain. |

## Final Verdict

**SHIP.** Phase 1 passed 4/4 checks. All requested live timing and response-validity gates passed, mutation visibility was confirmed at 0.5 seconds after score acknowledgment, and every R1 burst passed the prewarm timing gate. No new P1 issue was found within this re-verification scope.

The full backend test suites were not rerun for this read-only live audit. The prior fixer report records their results; this verdict relies on the source inspection and fresh live measurements above.
