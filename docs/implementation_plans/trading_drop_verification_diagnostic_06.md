# Trading DROP Verification Diagnostic 06

Date: 2026-06-05
Model: gpt-5.5
Task Type: Read-only diagnostic / code review document creation only. No source code changes.
Repo: copilot-sdk
Diagnostic Scope: Trading DROP-candidate verification across domain config, broker/data connectors, factors, journal, regime, prescore, promotion, evolution, correlation, earnings subcategory, and VIX timing.
Prior Diagnostics Read: `trading_backend_filetree_diagnostic.md`, `trading_deep_chase_diagnostic_01b.md`, `sdk_backend_endpoint_map_diagnostic_02.md`, and `trading_completeness_diagnostic_03.md` were found.

## Executive Summary

* Number of DROP candidates reviewed: 13
* DROP-confirmed count: 1
* Reclassified to SUPPLEMENT count: 12
* Reclassified to FULL count: 0
* Highest-risk false DROP: P49 TRD-ALPACA-CONNECTOR. The Alpaca import connector exists, but the wired `/api/broker/sync` endpoint explicitly reports sync unsupported, so a DROP label would be unsafe.
* Recommended next prompt: targeted SUPPLEMENT implementation queue for P49/P50/P51/P54/P57/P81/P82/P83/P84/#171/#172/#173, plus MAP queue update that keeps only P48 as DROP-confirmed.

## Path Resolution

* CLAUDE_SDK value: `C:\Users\baner\CopyFolder\IOT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Repo path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Trading app path: `apps\trading\backend\app`
* main.py path: `apps\trading\backend\app\main.py`
* Report path: `docs\implementation_plans\trading_drop_verification_diagnostic_06.md`
* Prior Diag 01 found: YES
* Prior Diag 01b found: YES
* Prior Diag 02 found: YES
* Prior Diag 03 found: YES

## CLAUDE.md Relevant Notes

* Docs are aspirational until proven in code.
* Cite file and line for every behavioral claim.
* Code and tests beat docs.
* Do not use git directly.
* Normal verification guidance says run tests, but this diagnostic explicitly forbids tests.

## Review Standard

A prompt is DROP-confirmed only if implementation is complete, has no TODO/stub/hardcoded production returns, matches PD fields/thresholds/semantics, is wired at the correct endpoint where applicable, and fails explicitly and safely. Any missing endpoint, silent default/empty fallback, unsupported route, or semantic mismatch reclassifies the item to SUPPLEMENT or FULL.

## File Location Summary

| Area | Expected File(s) | Actual File(s) Found | Missing? | Notes |
| ---- | ---------------- | -------------------- | -------: | ----- |
| Domain config | `copilot_sdk\scoring\presets\trading.py` | Same | NO | Contains 5x4x10 shape and migration. |
| Alpaca | `connectors\alpaca_connector.py`, `brokers\alpaca.py`, `models\trade.py`, `routers\broker_router.py` | Same | NO | Connector and broker exist; sync endpoint is unsupported. |
| yfinance | `connectors\yfinance_provider.py`, `routers\data_import.py`, regime/correlation services | Same | NO | Market endpoints exist; provider silently returns empty on failures. |
| Factors | `factors\*.py` | Same | NO | Registry exists but several factor class names/indices and semantics mismatch. |
| Journal | `routers\journal.py` | Same | NO | Endpoint wired; graph-store read exceptions are swallowed. |
| Regime | `services\regime.py`, `factors\market_regime.py`, `routers\regime.py` | Same | NO | Thresholds exist; default fallback masks market-data failures. |
| Prescore | `routers\prescore.py` | Same | NO | Endpoint wired and read-only. |
| Promotion | `services\promotion.py`, `routers\promotion.py` | Same | NO | Stage/threshold names mismatch spec. |
| Evolution | `evolution\dimensions.py`, `evolver_config.py`, `variant_provider.py`, `__init__.py` | Same | NO | Real but narrow dimensions. |
| Correlation | `services\correlation.py`, `routers\correlation.py` | Same | NO | No effective multiplier or concentrated accuracy. |
| Earnings subcategory | `services\subcategory.py` | Same | NO | Names differ from expected event subcategory names. |
| VIX timing | `services\vix_timing.py`, `routers\vix_timing.py` | Same | NO | No entry timing accuracy / peak-trough analysis. |

## Per-Prompt Line-by-Line Verification

### P48 TRD-DOMAIN-CONFIG

Files read: `copilot_sdk\scoring\presets\trading.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| 5 categories, 4 actions, 10 factors | PASS | `trading.py` lines 25-28 | Matches shape. |
| `skip_recommended` action index 3 | PASS | `trading.py` line 36 | Fourth action is skip. |
| Factor order indices 6-9 | PASS | `trading.py` lines 37-48 | `signal_confidence`, delta, IV, gamma are indices 6-9. |
| penalty/eta/q/temp | PASS | `trading.py` lines 51-72 | `penalty_ratio=3.0`, `eta_override=0.01`, `temperature=0.1`, `q_window=400`. |
| legacy migration | PASS | `trading.py` lines 94-110 | Migrates `(5,3,6)` to `(5,4,10)`. |
| no TODO/stub around config | PASS | Full file read | No TODO/pass/NotImplementedError found. |
| Verdict:        | DROP-CONFIRMED | All config checks pass | Bootstrap catch-all returns neutral centroids at lines 99-100, but domain config itself matches the MAP checks. |
| Reclassify to:  | N/A |  |  |
| Gaps:           | None for implementation queue |  | Runtime validation still not run. |
| Endpoint wired: | N/A | Domain preset imported by `main.py` line 54 | Config is not an endpoint. |

### P49 TRD-ALPACA-CONNECTOR

Files read: `apps\trading\backend\app\connectors\alpaca_connector.py`, `brokers\alpaca.py`, `models\trade.py`, `routers\broker_router.py`, `main.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| Uses alpaca-py SDK for import | PASS | `alpaca_connector.py` lines 23-27 and 42-48 | Uses `alpaca.trading.*`. |
| Supports paper and live modes | PARTIAL | `brokers/alpaca.py` lines 13, 29 | Default paper URL; live can be supplied via `APCA_API_BASE_URL`, but no explicit mode field. |
| import returns `NormalizedTrade` | PASS | `alpaca_connector.py` lines 38, 52-73; `models/trade.py` lines 10-26 | Normalized model has requested core fields. |
| multi-year import | PARTIAL | `alpaca_connector.py` lines 38-45 | `days` parameter can exceed 365, but router sync does not expose import. |
| safe auth/connection failure | PARTIAL | `alpaca_connector.py` lines 21-27 raise; `broker_router.py` lines 128-203 return disconnected payloads | Read endpoints return empty payloads with errors rather than HTTP errors; order placement uses 503. |
| `/api/broker/sync` imports trades | FAIL | `broker_router.py` lines 259-268 | Wired endpoint returns `status: unsupported` and `synced: 0`. |
| Verdict:        | SUPPLEMENT | Sync endpoint is fake/unsupported | Connector exists but MAP import/sync path is not complete. |
| Reclassify to:  | SUPPLEMENT(broker sync/import wiring) |  |  |
| Gaps:           | Wire Alpaca import through `/api/broker/sync`; decide explicit paper/live mode semantics. |  |  |
| Endpoint wired: | YES but unsupported | `main.py` line 307 includes broker router with prefix `/api/broker`; `broker_router.py` line 259 defines `/sync`. |  |

### P50 TRD-YFINANCE

Files read: `connectors\yfinance_provider.py`, `routers\data_import.py`, `services\regime.py`, `services\correlation.py`, `main.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| Uses `import yfinance as yf` | PASS | `yfinance_provider.py` line 12; `regime.py` line 10; `correlation.py` line 19 | Uses yfinance. |
| Downloads VIX via `^VIX` | PASS | `yfinance_provider.py` line 32; `regime.py` line 73 | VIX symbol used. |
| OHLCV endpoints wired | PASS | `data_import.py` lines 45-59; `main.py` line 309 | `/api/trading/market/ohlcv` and `/market/vix`. |
| no API key required | PASS | Full provider read | No key required. |
| automatic OHLCV on import | FAIL | `data_import.py` lines 19-28 | CSV import only stores trades in memory; no OHLCV fetch per ticker. |
| safe failures | FAIL | `yfinance_provider.py` lines 11-16; `regime.py` lines 67-78 and 96-99 | Exceptions return `[]` or default regime without surfacing failure. |
| persistent accessible market data | FAIL | `data_import.py` lines 16-28 | In-memory `trade_store`; market data is fetched per request only. |
| Verdict:        | SUPPLEMENT | Live endpoints exist but production safety/persistence/import hooks fail. |  |
| Reclassify to:  | SUPPLEMENT(yfinance persistence/import error handling) |  |  |
| Gaps:           | Make failures explicit, fetch/store OHLCV on trade import, avoid silent empty/default production paths. |  |  |
| Endpoint wired: | YES | `main.py` line 309 includes `data_import_router`. |  |

### P51 TRD-SIGNAL-FACTORS

Files read: `factors\registry.py`, `signal_confidence.py`, `market_regime.py`, `technical_signal.py`, `base.py`, supporting grep across app.

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| signal_alignment uses tagged signals ratio | PASS | `conviction.py` lines 10-27 | Registry maps `signal_alignment` to `ConvictionFactor` at `registry.py` line 43. |
| market_regime reads current regime/accuracy | PASS/PARTIAL | `market_regime.py` lines 28-42 | Logic exists, but class metadata says `factor_name="emotional_indicator"` and index 5 at lines 20-22. |
| emotional indicator uses required context | FAIL | `registry.py` lines 48 and 61 map `emotional_indicator` to `ResearchDepthFactor`; `research_depth.py` lines 10-35 compute sources/minutes/thesis/checklist | Revenge/FOMO/overconfidence context is not the actual factor implementation. |
| penalties -0.4/-0.3/-0.2 | FAIL | Factor files read; no such penalty logic in registered emotional factor | Pattern detector finds patterns, but not as the factor. |
| all factors clipped [0,1] | PASS | `base.py` lines 10-15; registry clamps at lines 81-84 | Exceptions collapse to neutral 0.5. |
| registry names match tensor | PARTIAL | `registry.py` lines 42-53 | Mapping keys match names, but class `factor_name`/`factor_index` metadata are inconsistent across files. |
| Decision Context label | PASS | `evidence.py` lines 24-29 and 264-268 | Display label uses Decision context. |
| Verdict:        | SUPPLEMENT | Key factor semantics are present only partially and emotional indicator is miswired. |  |
| Reclassify to:  | SUPPLEMENT(factor registry/semantic repair) |  |  |
| Gaps:           | Implement/route true emotional indicator factor; fix class metadata mismatches; avoid silent neutral on compute errors where unsafe. |  |  |
| Endpoint wired: | N/A | Used by prescore and scoring flows; not a standalone endpoint. |  |

### P54 TRD-REMAINING-FACTORS

Files read: `position_size.py`, `time_horizon.py`, `conviction.py`, `research_depth.py`, `options_scored.py`, `registry.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| position_sizing penalizes oversized and deviation from rolling average | PARTIAL | `position_size.py` lines 21-33 and 36-79; `conviction.py` lines 34-49 | Position factor uses max/concentration/correlation/kelly, while rolling average appears in conviction. |
| timing_quality entry delay / hold-time penalties | FAIL | `technical_signal.py` lines 10-39 is mapped to `timing_quality` in registry line 46 | It scores RSI/MACD/SMA/tagged signals, not entry delay or hold time. |
| risk_reward_actual planned RR / R-multiple | FAIL | `time_horizon.py` lines 19-65 is mapped to `risk_reward_actual` in registry line 47 | Computes plan adherence/exit/session, not planned RR or R-multiple. |
| signal_confidence uses DK weights | FAIL | `signal_confidence.py` lines 19-33 | Uses data availability/category accuracy/similar count/novelty; no `dk_weights_by_category`. |
| factor names match tensor indices 2/3/4/6 | PARTIAL | `registry.py` lines 42-53; class metadata in `position_size.py` lines 10-12 and `time_horizon.py` lines 19-21 | Registry keys match; class metadata mismatches names/indices. |
| Verdict:        | SUPPLEMENT | Core modules exist but several PD semantics are not implemented. |  |
| Reclassify to:  | SUPPLEMENT(remaining factor semantics) |  |  |
| Gaps:           | Implement timing, risk/reward, DK-weighted confidence, and clean factor metadata. |  |  |
| Endpoint wired: | N/A | Factor computation used indirectly. |  |

### P57 TRD-JOURNAL

Files read: `routers\journal.py`, `main.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| returns factor scores per trade | PASS | `journal.py` lines 157-195 | Normalized trade includes `factors`. |
| filter category/regime/date/strategy | PASS | `journal.py` lines 29-50 and 211-239 | Filters implemented. |
| returns NL evidence per trade | FAIL | `journal.py` lines 181-204 | Trade response includes raw fields/factors/metadata, no rendered evidence string. |
| safe graph-store failure | FAIL | `journal.py` lines 127-140 | Graph store exceptions are swallowed with `pass`. |
| endpoint wired | PASS | `main.py` line 293 | Journal router included. |
| Verdict:        | SUPPLEMENT | Journal mostly exists but lacks NL evidence and has silent failure. |  |
| Reclassify to:  | SUPPLEMENT(journal evidence + explicit failures) |  |  |
| Gaps:           | Add per-trade NL evidence and replace silent `pass` with explicit safe status. |  |  |
| Endpoint wired: | YES | `/api/trading/trades`, `/api/trading/analytics`. |  |

### P81 TRD-REGIME-CLASSIFIER

Files read: `services\regime.py`, `factors\market_regime.py`, `routers\regime.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| exact regime thresholds | PASS | `regime.py` lines 18-32; `market_regime.py` lines 10-17 | VIX/ADX thresholds match. |
| returns trending/ranging/volatile | PASS | Same lines | Values match. |
| real VIX from yfinance | PASS/PARTIAL | `regime.py` lines 72-91 | Uses yfinance but silently defaults on failure. |
| real ADX from pandas-ta | PASS/PARTIAL | `regime.py` lines 35-50 | Uses pandas-ta; defaults to 20 on insufficient/errors. |
| `/regime` fields match PD | FAIL | `regime.py` lines 86-93; `regime_router.py` lines 27-37 | Response nests `current` with `regime` and `adx`, not explicit `current_regime` and `trend_strength`. |
| `/regime/detail` breakdown | PARTIAL | `regime_router.py` lines 39-50 | Returns recommender output, not a simple per-regime detail payload. |
| Verdict:        | SUPPLEMENT | Classifier exists; output shape and failure behavior need correction. |  |
| Reclassify to:  | SUPPLEMENT(regime response/failure semantics) |  |  |
| Gaps:           | Explicit market-data failure, field names, and detail response alignment. |  |  |
| Endpoint wired: | YES | `main.py` line 304. |  |

### P82 TRD-REALTIME-SCORE

Files read: `routers\prescore.py`, `main.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| POST `/prescore` accepts hypothetical trade | PARTIAL | `prescore.py` lines 23-30 and 41-45 | Accepts ticker/direction/category/strategy/notes/size_pct; no explicit `signals` field. |
| same factor computers | PASS | `prescore.py` lines 13 and 70 | Uses `compute_factors`. |
| historical accuracy from verified history | PARTIAL | `prescore.py` lines 47-59 | Uses journal records/regime accuracy; not explicitly setup/category verified accuracy beyond regime. |
| current regime context | PASS/PARTIAL | `prescore.py` lines 48-50 | Uses `RegimeService`, inheriting its default fallback risks. |
| recommendation with score/action/reason | PARTIAL | `prescore.py` lines 94-104 and 131-140 | Has recommendation/action/confidence/evidence; no separate reason field except evidence. |
| no ledger mutation | PASS | `prescore.py` lines 115-118 | Comment states it avoids `scorer.score()` persistence. |
| Verdict:        | SUPPLEMENT | Useful prescore exists but request/response and regime fallback do not fully match. |  |
| Reclassify to:  | SUPPLEMENT(prescore schema/accuracy/reason) |  |  |
| Gaps:           | Add signals schema, explicit reason, setup/category accuracy, and explicit market-data failure semantics. |  |  |
| Endpoint wired: | YES | `main.py` line 295. |  |

### P83 TRD-PROMOTION-ENGINE

Files read: `services\promotion.py`, `routers\promotion.py`, `main.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| paper -> live_small -> live_full state machine | FAIL | `promotion.py` line 11 | Uses `paper`, `small_live`, `full_live`, not specified names. |
| paper gate: 50 trades, accuracy >= 58%, sigma <= 0.15, conservation GREEN | FAIL | `promotion.py` lines 12-15 and 96-103 | Paper threshold is win_rate 0.55; no sigma check. |
| live_small gate: 100 trades accuracy maintained | PARTIAL | `promotion.py` lines 177-181 | Uses 100 verified and 0.58 win rate; no separate live-small evidence window. |
| audit trail timestamp/reason | PASS | `promotion.py` lines 108-122 | History event has timestamp and reason. |
| GET/POST endpoints | PASS | `routers/promotion.py` lines 32-52 | Both endpoints exist. |
| unsafe default | FAIL | `routers/promotion.py` lines 84-87 | If no graph-store factory, conservation defaults to GREEN. |
| Verdict:        | SUPPLEMENT | Engine exists but thresholds/stage names/sigma/default safety mismatch. |  |
| Reclassify to:  | SUPPLEMENT(promotion gate spec alignment) |  |  |
| Gaps:           | Rename/alias stages, enforce 58% and sigma <= 0.15, remove GREEN default, define live-small evidence window. |  |  |
| Endpoint wired: | YES | `main.py` lines 296-303. |  |

### P84 TRD-AGENT-EVOLVER-FULL

Files read: `evolution\dimensions.py`, `evolver_config.py`, `variant_provider.py`, `__init__.py`, `main.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| revenge window 30 -> 45 | PASS | `evolver_config.py` lines 49-72 | Baseline/conservative cooldown values present. |
| sizing anomaly threshold | PARTIAL | `evolver_config.py` lines 57-70 | `max_size_ratio` exists only within revenge cooldown. |
| regime boundary sensitivity | FAIL | `dimensions.py` lines 10-23; `evolver_config.py` lines 24-73 | Only execution threshold and revenge cooldown dimensions. |
| provider wired to evolution router | PASS | `variant_provider.py` lines 5-11; `main.py` lines 273-280 | `variant_provider=get_trading_variants`. |
| conservation-gated promotion | PARTIAL | SDK evolution is registered; config line 76-81 has promotion thresholds | Direct conservation gating not visible in these app files. |
| no fake provider | PASS | Provider reads real variant specs | No TODO/stub found in targeted files. |
| Verdict:        | SUPPLEMENT | Real but not full Trading evolution dimension coverage. |  |
| Reclassify to:  | SUPPLEMENT(evolution dimension expansion) |  |  |
| Gaps:           | Add regime sensitivity and broader sizing/risk/timing/signal-confidence dimensions tied to verified outcomes. |  |  |
| Endpoint wired: | YES | `main.py` lines 273-280. |  |

### #171 TRD-CORRELATION-MONITOR

Files read: `services\correlation.py`, `routers\correlation.py`, `main.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| pairwise Pearson from 20-day returns | PASS | `correlation.py` lines 27-29, 70-123 | Uses yfinance download and `np.corrcoef`. |
| threshold 0.6 configurable | PARTIAL | `correlation.py` line 27; router line 24 | Window configurable; alert threshold constant is not endpoint-configurable. |
| effective_multiplier | FAIL | Full file read/search | Not present. |
| concentrated_accuracy from trade history | FAIL | Full file read/search | Not present. |
| recommendations[] action strings | FAIL | `correlation.py` lines 58-68 and 166-190 | Returns `alerts`, not `recommendations`. |
| endpoint wired | PASS | `routers/correlation.py` lines 23-26; `main.py` line 294 | `/api/trading/correlation`. |
| Verdict:        | SUPPLEMENT | Core correlation exists; product payload incomplete. |  |
| Reclassify to:  | SUPPLEMENT(correlation payload completion) |  |  |
| Gaps:           | Add effective multiplier, concentrated accuracy, configurable threshold, and recommendations. |  |  |
| Endpoint wired: | YES | `main.py` line 294. |  |

### #172 TRD-EARNINGS-SUBCAT

Files read: `services\subcategory.py`, `routers\journal.py`, `routers\prescore.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| classify earnings trade exists | PARTIAL | `subcategory.py` lines 53-67 | Function is `classify_event_subcategory`, not `classify_earnings_trade`. |
| event_volatility for straddle/strangle/iron_condor | FAIL/PARTIAL | `subcategory.py` lines 29-42 and 61-64 | Returns `volatility`, not `event_volatility`; includes iron condor tag. |
| event_directional for directional trades | FAIL/PARTIAL | `subcategory.py` lines 9-27 and 65-67 | Returns `directional`, not `event_directional`. |
| only event_driven | PASS | `subcategory.py` lines 70-74 | Non-event categories return None. |
| per-subcategory accuracy | PASS/PARTIAL | `journal.py` lines 83-107 and 260-267 | Analytics can group by `subcategory`; no separate endpoint. |
| used in analytics/journal/scoring/import | PARTIAL | `journal.py` lines 13 and 203; `prescore.py` lines 16 and 52-57 | Used in journal/prescore, not import/scoring persistence. |
| Verdict:        | SUPPLEMENT | Helper exists but names/usage do not fully match spec. |  |
| Reclassify to:  | SUPPLEMENT(subcategory naming/integration) |  |  |
| Gaps:           | Add expected function/output names and ensure import/scoring persistence if required. |  |  |
| Endpoint wired: | N/A | Exposed through journal analytics and prescore, not standalone. |  |

### #173 TRD-VIX-TIMING

Files read: `services\vix_timing.py`, `routers\vix_timing.py`, `services\regime.py`, `main.py`

Spec checks:

| Check           | Pass/Fail | Evidence | Notes |
| --------------- | --------- | -------- | ----- |
| hold-period segments | PASS/PARTIAL | `vix_timing.py` lines 9-16 and 24-38 | Uses intraday/1-3 days/1-2 weeks/2+ weeks, not exact 1d/3d/5d labels. |
| accuracy per hold period from verified history | PARTIAL | `vix_timing.py` lines 61-102; `routers/vix_timing.py` lines 24-28 | Uses journal records and pnl wins; no explicit verified-only filter. |
| entry timing peak/trough accuracy | FAIL | Full file read/search | No peak/trough proximity or `entry_accuracy`. |
| real trade history/static data | PASS/PARTIAL | `routers/vix_timing.py` lines 26-28 | Uses journal records and RegimeService historical VIX; inherits yfinance empty fallback. |
| payload includes hold_period_analysis[] and entry_accuracy | FAIL | `vix_timing.py` lines 93-102 | Returns `matrix`, best/worst, labels, recommendations; no required fields. |
| actionable recommendation | PASS | `vix_timing.py` lines 105-137 | Recommendations exist. |
| Verdict:        | SUPPLEMENT | Core analysis exists; required entry accuracy and payload shape missing. |  |
| Reclassify to:  | SUPPLEMENT(VIX timing payload/entry accuracy) |  |  |
| Gaps:           | Add peak/trough timing, verified-only filtering, expected response fields, and explicit VIX-data failure state. |  |  |
| Endpoint wired: | YES | `main.py` line 306. |  |

## Silent Failure / Hardcoded Return Audit

| File | Line | Issue Type | Production Impact | Related Prompt | Evidence |
| ---- | ---: | ---------- | ----------------- | -------------- | -------- |
| `connectors/yfinance_provider.py` | 15-16 | SILENT_EMPTY_FALLBACK | Market-data errors produce empty rows with no error. | P50 | `except Exception: return []`. |
| `services/regime.py` | 67-78, 96-99 | HARDCODED_PRODUCTION_RETURN | Missing yfinance/empty data/error returns default regime. | P81/P82/#173 | `_default()` returns ranging/VIX 20/ADX 20. |
| `routers/broker_router.py` | 259-268 | HARDCODED_PRODUCTION_RETURN | `/api/broker/sync` always reports unsupported and `synced: 0`. | P49 | Sync endpoint does not call connector import. |
| `routers/journal.py` | 127-140 | PASS | Graph-store failures are swallowed, causing partial journal results. | P57/P82/#171/#173 | `except Exception: pass`. |
| `services/correlation.py` | 40-48, 101-102 | SILENT_EMPTY_FALLBACK | Correlation becomes insufficient-data payload on dependency/data failures. | #171 | `_insufficient(...)`, `_fetch_returns` returns None. |
| `routers/promotion.py` | 84-87 | HARDCODED_PRODUCTION_RETURN | Missing graph-store factory is treated as GREEN. | P83 | Returns `{"status": "GREEN", "passed": True}`. |
| `factors/registry.py` | 81-84 | SILENT_EMPTY_FALLBACK | Factor compute exceptions become neutral 0.5. | P51/P54 | Broad `except Exception`. |
| `factors/registry.py` | 43-49 | SPEC_MISMATCH | Tensor names mapped to classes whose metadata/semantics mismatch. | P51/P54 | `emotional_indicator` maps to `ResearchDepthFactor`. |
| `services/promotion.py` | 11-15 | SPEC_MISMATCH | Stage names and paper threshold differ from spec. | P83 | Uses `small_live`/`full_live`, paper win rate 0.55. |
| `services/subcategory.py` | 61-67 | SPEC_MISMATCH | Outputs `volatility`/`directional`, not `event_volatility`/`event_directional`. | #172 | Return values shown. |
| `services/vix_timing.py` | 93-102 | SPEC_MISMATCH | Missing required `hold_period_analysis[]` and `entry_accuracy`. | #173 | Response shape differs. |

## Final Verdict Table

| Prompt                       | Verdict | Gaps Found If Any | Reclassify To | Endpoint Wired | Next Action |
| ---------------------------- | ------- | ----------------- | ------------- | -------------- | ----------- |
| P48 TRD-DOMAIN-CONFIG        | DROP-CONFIRMED | None for implementation queue | N/A | N/A | MAP queue update only. |
| P49 TRD-ALPACA-CONNECTOR     | SUPPLEMENT | `/api/broker/sync` unsupported; live/paper mode implicit | SUPPLEMENT | YES but unsupported | Targeted sync/import wiring. |
| P50 TRD-YFINANCE             | SUPPLEMENT | Silent empty/default fallbacks; no auto OHLCV on import; no persistence | SUPPLEMENT | YES | Targeted market-data hardening. |
| P51 TRD-SIGNAL-FACTORS       | SUPPLEMENT | Emotional indicator miswired; factor metadata mismatches | SUPPLEMENT | N/A | Factor semantic repair. |
| P54 TRD-REMAINING-FACTORS    | SUPPLEMENT | Timing/RR/DK-weight semantics missing or miswired | SUPPLEMENT | N/A | Factor semantic repair. |
| P57 TRD-JOURNAL              | SUPPLEMENT | No NL evidence per trade; graph-store exception swallowed | SUPPLEMENT | YES | Journal evidence/error handling. |
| P81 TRD-REGIME-CLASSIFIER    | SUPPLEMENT | Default fallbacks and response field mismatch | SUPPLEMENT | YES | Regime response/failure hardening. |
| P82 TRD-REALTIME-SCORE       | SUPPLEMENT | No explicit signals schema/reason; setup accuracy incomplete | SUPPLEMENT | YES | Prescore schema/response supplement. |
| P83 TRD-PROMOTION-ENGINE     | SUPPLEMENT | Threshold/stage/sigma/default GREEN mismatches | SUPPLEMENT | YES | Promotion gate spec alignment. |
| P84 TRD-AGENT-EVOLVER-FULL   | SUPPLEMENT | Narrow dimensions; missing regime/sizing breadth | SUPPLEMENT | YES | Evolution dimension supplement. |
| #171 TRD-CORRELATION-MONITOR | SUPPLEMENT | Missing effective multiplier, concentrated accuracy, recommendations | SUPPLEMENT | YES | Correlation payload supplement. |
| #172 TRD-EARNINGS-SUBCAT     | SUPPLEMENT | Output names and integration gaps | SUPPLEMENT | PARTIAL | Subcategory naming/integration supplement. |
| #173 TRD-VIX-TIMING          | SUPPLEMENT | Missing entry accuracy and required payload shape | SUPPLEMENT | YES | VIX timing supplement. |

Verdict key:

* DROP-CONFIRMED: all checks pass, implementation complete, endpoint wired where applicable, safe failures.
* SUPPLEMENT([gap]): core logic present, specific gap identified.
* FULL: major functionality missing or file absent.
* UNCLEAR: more targeted diagnostic needed.

## Diagnostic Limitations

* This diagnostic does not run tests.
* This diagnostic does not validate live broker/API behavior.
* This diagnostic does not validate frontend UI wiring.
* This diagnostic does not prove package installability or live yfinance/alpaca connectivity.
* DROP-CONFIRMED means line-by-line source inspection supports dropping the implementation prompt, not that E2E validation passed.

## Recommended Next Step

Run a MAP queue update only for P48 as DROP-CONFIRMED. Create targeted SUPPLEMENT implementation prompts for P49/P50/P51/P54/P57/P81/P82/P83/P84/#171/#172/#173, prioritizing P49 broker sync, P51/P54 factor semantic repair, and P83 promotion gate alignment because those have the highest false-DROP risk.
