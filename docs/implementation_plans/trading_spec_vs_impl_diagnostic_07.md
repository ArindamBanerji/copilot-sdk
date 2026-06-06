# Trading Spec-vs-Implementation Diagnostic 07

Date: 2026-06-05  
Model: gpt-5.5  
Task Type: Read-only diagnostic / code review document creation only  
Repo: copilot-sdk  
Diagnostic Scope: Trading spec-vs-implementation verification for P84, P55, P82, P53, P83, and P81  
Prior Diagnostics Read: trading_backend_filetree_diagnostic.md, trading_deep_chase_diagnostic_01b.md, sdk_backend_endpoint_map_diagnostic_02.md, trading_completeness_diagnostic_03.md, trading_drop_verification_diagnostic_06.md

## Executive Summary

* Items reviewed: 6
* CONFIRMED count: 0
* INCOMPLETE-DESIGN count: 1
* INCOMPLETE-IMPL count: 3
* PARTIAL-RESPONSE count: 2
* DROP items reclassified: 6
* Highest-risk false DROP: P53 TRD-TRUST-RADAR. The endpoint exists, but inspected code computes variance/sigma trust rather than PD-required DK actual importance, expected usage, expected/actual trust trap ratio, overuse ratio, and per-factor response fields.
* Recommended next prompt: targeted SUPPLEMENT implementation for P53 and P82 first, followed by P84/P83/P81/P55 supplements.

## Path Resolution

* CLAUDE_SDK value: `C:\Users\baner\CopyFolder\IOT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Repo path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
* Trading app path: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\trading\backend\app`
* context_router.py path: `apps/trading/backend/app/context_router.py`
* services path: `apps/trading/backend/app/services`
* routers path: `apps/trading/backend/app/routers`
* evolution path: `apps/trading/backend/app/evolution`
* SDK evolution router path: `copilot_sdk/backend/evolution_router.py`
* Report path: `docs/implementation_plans/trading_spec_vs_impl_diagnostic_07.md`
* Prior Diag 01 found: YES
* Prior Diag 01b found: YES
* Prior Diag 02 found: YES
* Prior Diag 03 found: YES
* Prior Diag 06 found: YES

## CLAUDE.md Relevant Notes

CLAUDE.md says docs are aspirational until verified against code, code/tests are the source of truth, and implementation claims must cite file and line evidence. This diagnostic follows the local rule by using source inspection only, no git, and no tests.

## Review Standard

Existence is not completion. Clean code is not spec compliance. Every R checkpoint must pass for DROP to remain DROP. Missing response fields mean PARTIAL-RESPONSE. Wrong constants, formulas, data sources, persistence, or algorithms mean INCOMPLETE-IMPL. Missing scenario coverage means INCOMPLETE-DESIGN.

## Files Read

| Item | Expected Files | Actual Files Read | Missing Files | Notes |
| ---- | -------------- | ----------------- | ------------- | ----- |
| P84 | `evolution/dimensions.py`, `evolver_config.py`, `variant_provider.py`, `copilot_sdk/backend/evolution_router.py` | All expected files read | None | Main wiring also found in `main.py:35`, `main.py:46`, `main.py:275-278`. |
| P55 | `services/pattern_detector.py` | Expected file read | None | Detectors present but several thresholds/scenarios do not match spec. |
| P82 | `routers/prescore.py` and related searches | Expected file read | None | Endpoint exists but request/response shape and conservation behavior are incomplete. |
| P53 | `context_router.py` trust-analysis section and helpers | Expected file read | None | Endpoint exists but computes variance/sigma, not DK-vs-usage radar. |
| P83 | `services/promotion.py`, `routers/promotion.py` | Expected files read | None | Logic exists but stage names, thresholds, response fields, and audit naming differ. |
| P81 | `services/regime.py`, `factors/market_regime.py`, `routers/regime.py` | Expected files read | None | Core classifier thresholds pass; endpoint response and verified-history accuracy do not. |

## Item 1 - P84 TRD-AGENT-EVOLVER-FULL

| Requirement | Status | Evidence | Classification |
| ------------------------------------------------ | ------ | -------- | -------------- |
| R1 revenge window tunable 30 to 45 | PASS | `evolver_config.py:49-72` defines `REVENGE_COOLDOWN_v1` cooldown 30 and `REVENGE_COOLDOWN_v2` cooldown 45. | CONFIRMED |
| R2 sizing anomaly threshold tunable 1.3x to 1.5x | FAIL | `evolver_config.py:55` uses `max_size_ratio: 1.3`; `evolver_config.py:67` changes it to `1.2`, not 1.5. | INCOMPLETE-IMPL |
| R3 regime boundary sensitivity tunable | FAIL | `dimensions.py:11-22` contains only `execution_threshold` and `revenge_cooldown`; no regime boundary dimension. | INCOMPLETE-DESIGN |
| R4 pattern detection sensitivity tunable | FAIL | `dimensions.py:11-22` has no pattern/tilt/FOMO sensitivity dimension. | INCOMPLETE-DESIGN |
| R5 conservation gate governs promotions | PARTIAL | `evolution_router.py:36-48` uses `DefaultPromotionGate`; Trading wires `create_evolution_router` in `main.py:275-278`, but no Trading-specific GREEN gate was found in app evolution files. | INCOMPLETE-IMPL |
| R6 baseline and variant tested against outcomes | PARTIAL | `evolver_config.py:25-72` defines baseline/variant payloads; `evolution_router.py:65-84` exposes history/promoted endpoints, but app variant files do not show verified outcome evaluation. | INCOMPLETE-IMPL |
| R7 connected to verified trade outcomes | PARTIAL | Search found `get_trading_variants` wiring in `main.py:275-278`; outcome references were in `trader_profiles.py:208-209`, not tied to variant promotion. | INCOMPLETE-IMPL |

Verdict: INCOMPLETE-DESIGN  
Reclassify: SUPPLEMENT  
Exact gap: only two variant dimensions exist; missing regime boundary and pattern sensitivity dimensions, sizing variant moves 1.3 to 1.2 instead of 1.5, and verified-outcome/conservation promotion linkage is not explicit in Trading evolution code.  
Likely next prompt: targeted P84 supplement for dimensions, outcome linkage, and conservation-gated promotion evidence.

## Item 2 - P55 TRD-PATTERN-DETECTOR

| Requirement | Status | Evidence | Classification |
| ------------------------------------------- | ------ | -------- | -------------- |
| R1 revenge threshold 30 minutes | PASS | `pattern_detector.py:141-143` excludes revenge candidates with minutes greater than 30. | CONFIRMED |
| R2 overconfidence >=3 wins and size >1.3x | PASS | `pattern_detector.py:170-176` requires `win_streak >= 3`; `pattern_detector.py:190-198` checks size ratio `> 1.3`. | CONFIRMED |
| R3 FOMO within 1 percent day high or low | PARTIAL | `pattern_detector.py:201-213` checks boolean `entry_at_day_extreme`, not a computed 1 percent high/low threshold. | INCOMPLETE-IMPL |
| R4 tilt 3+ trades in 1 hour | PASS | `pattern_detector.py:229-234` flags hourly buckets with `len(bucket) >= 3`. | CONFIRMED |
| R5 Friday 2-4pm with <40 percent accuracy | FAIL | `pattern_detector.py:277-336` finds a generic worst day/hour bucket and worst_gap; it does not specifically implement Friday 2-4pm below 40 percent accuracy. | INCOMPLETE-IMPL |
| R6 sorted by severity descending | PASS | `pattern_detector.py:29` sorts with `reverse=True` on severity. | CONFIRMED |
| R7 required pattern dict fields | PASS | `pattern_detector.py:122-130` returns `name`, `display_name`, `description`, `frequency`, `severity`, `affected_trade_count`, `affected_trades`, `recommendation`. | CONFIRMED |
| R8 label is Decision Context, not emotional | FAIL | `pattern_detector.py` display names are Revenge Trading, Overconfidence, FOMO, Tilt, Drawdown Chase, and Time-of-Day Degradation; no Decision Context label was found. | PARTIAL-RESPONSE |

Verdict: INCOMPLETE-IMPL  
Reclassify: SUPPLEMENT  
Exact gap: FOMO and Friday degradation definitions do not match the numbered spec, and the display taxonomy does not surface Decision Context.  
Likely next prompt: P55 supplement for exact FOMO, Friday 2-4pm degradation, and display labeling.

## Item 3 - P82 TRD-REALTIME-SCORE / Prescore

| Requirement | Status | Evidence | Classification |
| -------------------------------------------------------------------- | ------ | -------- | -------------- |
| R1 accepts ticker, direction, category, tagged_signals, planned_size | PARTIAL | `prescore.py:23-30` defines `ticker`, `direction`, `strategy_tag`, `category`, `notes`, `size_pct`; no request-level `tagged_signals` or `planned_size`. | INCOMPLETE-IMPL |
| R2 uses same 7 factor computers as live triage | PARTIAL | `prescore.py:70-71` calls `compute_factors(context)` and `compute_options_factors(context)`, but response returns a dict and not the required per-factor array. | PARTIAL-RESPONSE |
| R3 uses real VIX/ADX from yfinance/regime service | PARTIAL | `prescore.py:48-50` calls `RegimeService.get_current_regime`; `regime.py:73` fetches `^VIX`, but `regime.py:149-156` silently falls back to defaults. | INCOMPLETE-IMPL |
| R4 historical accuracy from verified trade history | PARTIAL | `prescore.py:58-59` uses `service.get_regime_accuracy(trades)`, not explicit setup-level verified trade history. | INCOMPLETE-IMPL |
| R5 returns all required response fields | FAIL | `prescore.py:94-104` returns `recommendation`, `confidence`, `action`, `factors`, `regime`, `regime_accuracy`, `warnings`, `evidence`, `category`; missing `recommended_action`, `per_factor_scores`, `historical_accuracy`, `current_regime`, `regime_accuracy_for_trader`, `sizing_note`. | PARTIAL-RESPONSE |
| R6 does not write to ledger or learn | PASS | `prescore.py:116-117` comments that pre-score deliberately avoids `scorer.score()` and persistence; search found no `learn`, `score_and_learn`, `record_decision`, or `write_decision` calls in `prescore.py`. | CONFIRMED |
| R7 notes AMBER/RED conservation | FAIL | `prescore.py:143-164` builds warnings for regime accuracy, emotional indicator, confidence, and revenge risk; no conservation AMBER/RED warning was found. | PARTIAL-RESPONSE |

Verdict: PARTIAL-RESPONSE  
Reclassify: SUPPLEMENT  
Exact gap: endpoint exists and computes factors, but request fields, response fields, setup historical accuracy, conservation warning, and hard-failure semantics do not match spec.  
Likely next prompt: P82 supplement focused on request/response schema and conservation-aware prescore behavior.

## Item 4 - P53 TRD-TRUST-RADAR

| Requirement | Status | Evidence | Classification |
| -------------------------------------------------- | ------ | -------- | -------------- |
| R1 actual_importance from DK weights | FAIL | `context_router.py:124-140` computes factor mean/variance/sigma from `compute_factors`; no DK actual importance field was found. | INCOMPLETE-IMPL |
| R2 expected_importance from signal usage frequency | FAIL | `context_router.py:124-140` does not count tagged signal usage; response search found no `expected_importance`. | INCOMPLETE-IMPL |
| R3 identifies trust trap by expected/actual ratio | FAIL | `_hero_insight` in `context_router.py:143-166` compares highest/lowest sigma, not expected/actual ratio. | INCOMPLETE-IMPL |
| R4 includes overuse_ratio | FAIL | Response field search found no `overuse_ratio`; trust response at `context_router.py:295-306` omits it. | PARTIAL-RESPONSE |
| R5 per_factor fields complete | FAIL | `context_router.py:295-306` returns `factors`, `implemented`, `trust_scores`, `total_trades`, `hero_insight`; no required per-factor entries with DK/usage fields. | PARTIAL-RESPONSE |
| R6 plain-language trust_label | PARTIAL | `_trust_label` in `context_router.py:108-121` returns labels like `highly_trusted`, `trusted`, `moderate`, `noisy`, not plain-language strings like Very reliable. | PARTIAL-RESPONSE |
| R7 hero insight string matches PD template | FAIL | `context_router.py:162-165` says one signal is varying most and another is steadiest; it does not match the PD expected/actual trust trap template. | PARTIAL-RESPONSE |

Verdict: PARTIAL-RESPONSE  
Reclassify: SUPPLEMENT  
Exact gap: current endpoint is a variance/sigma trust endpoint, not a DK-weighted expected-vs-actual trust radar.  
Likely next prompt: P53 supplement or focused rewrite of trust-analysis response and computation.

## Item 5 - P83 TRD-PROMOTION-ENGINE

| Requirement | Status | Evidence | Classification |
| ----------------------------------------------------- | ------ | -------- | -------------- |
| R1 explicit stages paper, live_small 2%, live_full 5% | FAIL | `promotion.py:11` uses `paper`, `small_live`, `full_live`; no 2 percent / 5 percent sizing fields were found. | INCOMPLETE-IMPL |
| R2 paper to live_small gate thresholds | FAIL | `promotion.py:12-15` requires paper win_rate `0.55` and count `50`, not accuracy `0.58` plus sigma `<=0.15`. | INCOMPLETE-IMPL |
| R3 live_small to live_full gate thresholds | PARTIAL | `promotion.py:12-15` has `small_live` to `full_live` win_rate `0.58` and verified_count `100`; stage naming and maintained-accuracy semantics are incomplete. | INCOMPLETE-IMPL |
| R4 conservation GREEN at each gate | PASS | `promotion.py:80` computes conservation_green and `promotion.py:96-103` blocks promotion unless GREEN. `promotion.py:129-143` checks status/phase. | CONFIRMED |
| R5 persistent stage across restarts | PARTIAL | `promotion.py:31-56` reads/writes `promotion_tiers.json`; persistence exists when `config_dir` is passed, but it is file-based and skipped if config_dir is None. | INCOMPLETE-IMPL |
| R6 audit trail fields | PARTIAL | `promotion.py:108-122` records `timestamp`, `from_tier`, `to_tier`, `reason`; spec names are `stage_from`, `stage_to`. | PARTIAL-RESPONSE |
| R7 per-strategy state | PASS | `promotion.py:20-23` builds strategy keys and `promotion.py:150-158` groups trades by strategy. | CONFIRMED |
| R8 GET response fields | FAIL | `promotion.py` router rows at `promotion.py:57-81` return `tier`, `win_rate`, `verified`; no `trades_in_stage`, `accuracy`, or `next_gate_requirement`. | PARTIAL-RESPONSE |
| R9 POST evaluate response fields | FAIL | `promotion.py` router `POST /promotion/evaluate` at `routers/promotion.py:41-52` returns events/status/strategies/history, not top-level `promoted`, `reason`, `new_stage`. | PARTIAL-RESPONSE |

Verdict: INCOMPLETE-IMPL  
Reclassify: SUPPLEMENT  
Exact gap: promotion exists, but stage names/sizing, paper threshold, sigma gate, response shape, and audit field names do not match spec.  
Likely next prompt: P83 supplement for exact stage model, thresholds, response fields, and persistence contract.

## Item 6 - P81 TRD-REGIME-CLASSIFIER

| Requirement | Status | Evidence | Classification |
| ------------------------------------------------ | ------ | -------- | -------------- |
| R1 classify_regime signature | PASS | `regime.py:25` defines `classify_regime(vix: float, trend_strength: float)`. | CONFIRMED |
| R2 vix > 30 returns volatile | PASS | `regime.py:26-27`. | CONFIRMED |
| R3 vix > 20 returns ranging | PASS | `regime.py:28-29`, after volatile check. | CONFIRMED |
| R4 trend_strength > 25 returns trending | PASS | `regime.py:30-31`, after VIX checks. | CONFIRMED |
| R5 default fallback ranging | PASS | `regime.py:32`; `_default` at `regime.py:152-159` also returns ranging. | CONFIRMED |
| R6 exact three strings | PASS | `regime.py:26-32` returns `volatile`, `ranging`, or `trending`. | CONFIRMED |
| R7 VIX from live yfinance ^VIX | PARTIAL | `regime.py:73` calls `yf.Ticker("^VIX")`, but `regime.py:149-156` falls back to default VIX/ADX on exception. | INCOMPLETE-IMPL |
| R8 trend_strength as ADX(14) | PASS | `regime.py:35-50` computes ADX with default period 14 via `pandas_ta.adx`. | CONFIRMED |
| R9 /regime response fields from verified history | FAIL | `routers/regime.py:27-37` returns `current`, `accuracy_by_category`, `recommendations`; missing required `current_regime`, `vix_value`, `adx_value`, `regime_accuracy_by_regime`. `regime.py:101-122` buckets provided trades without verified-only filtering. | PARTIAL-RESPONSE |

Verdict: INCOMPLETE-IMPL  
Reclassify: SUPPLEMENT  
Exact gap: classifier thresholds are correct, but fallback behavior, verified-history accuracy, and `/regime` response fields do not match spec.  
Likely next prompt: P81 supplement for strict response shape and verified-history regime accuracy.

## Cross-Cutting Audit

### Hardcoded VIX / Regime Defaults

| File | Line | Finding | Related Item | Impact |
| ---- | ---: | ------- | ------------ | ------ |
| `context_router.py` | 77 | `_default_market_snapshot` returns `{"regime": "ranging", "vix": 20.0, "adx": 25.0, "source": "default"}`. | P82/P81 | Hardcoded fallback can mask missing live market data. |
| `services/regime.py` | 18-22 | Default VIX/ADX constants are defined. | P81/P82 | Constants are valid thresholds but also used for fallbacks. |
| `services/regime.py` | 38, 45, 50 | ADX computation falls back to `DEFAULT_ADX`. | P81/P82 | Failure can silently produce default trend strength. |
| `services/regime.py` | 155-156 | `_default` returns default VIX and ADX. | P81/P82 | Endpoint can respond with defaults rather than explicit failure. |
| `services/regime.py` | 169 | Historical regime uses `DEFAULT_ADX` with VIX history. | P81 | Historical regime classification lacks ADX history. |

### Silent Exception Fallbacks

| File | Line | Fallback | Related Item | Impact |
| ---- | ---: | -------- | ------------ | ------ |
| `services/regime.py` | 149 | `except Exception: return {}` before default regime response. | P81/P82 | Live market failures can become default `ranging` responses. |
| `connectors/yfinance_provider.py` | 15 | `except Exception: return []`. | P81/P82 | Market data failures can become empty data. |
| `routers/promotion.py` | 100 | `except Exception: return {"status": "RED", "passed": False}`. | P83 | Safe block, but loses error detail in response. |
| `copilot_sdk/backend/evolution_router.py` | 89-95 | Variant provider exceptions return `[]`. | P84 | Variant provider failure silently removes variants. |
| `routers/regime.py` | 100 | Conservation status exception returns None. | P81 | Regime recommendation may omit conservation state. |

### In-Memory State

| File | Line | State | Related Item | Impact |
| ---- | ---: | ----- | ------------ | ------ |
| `services/regime.py` | 56 | `self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}`. | P81/P82 | Runtime cache only; acceptable for market snapshot caching, not persistence. |
| `services/promotion.py` | 31-56 | Promotion state uses JSON file when `config_dir` is set. | P83 | Not in-memory only, but persistence depends on config_dir. |
| `copilot_sdk/backend/evolution_router.py` | 36-48 | Uses `InMemoryEvolutionLedger` unless graph store path is supplied. | P84 | Evolution history may be process-local depending on router construction. |

### Response Field Coverage

| Field | Found? | File / Evidence | Related Item |
| ----- | -----: | --------------- | ------------ |
| `expected_importance` | NO | Cross-app search found no matches. | P53 |
| `actual_importance` | NO | Cross-app search found no matches. | P53 |
| `overuse_ratio` | NO | Cross-app search found no matches. | P53 |
| `hero_insight` | YES | `context_router.py:143`, `context_router.py:305`. | P53 |
| `regime_accuracy_by_regime` | NO | Cross-app search found no matches. | P81/P82 |
| `sizing_note` | NO | Cross-app search found no matches. | P82 |
| `next_gate_requirement` | NO | Cross-app search found no matches. | P83 |
| `dk_weight` | NO in Trading app response fields | Cross-app search found no Trading response use. | P53 |
| `expected_usage_pct` | NO | Cross-app search found no matches. | P53 |
| `actual_weight` | NO | Cross-app search found no matches. | P53 |
| `recommended_action` | YES elsewhere | `graph_contract.py:13`, `graph_status.py:203`, `seed_graph.py:191`; not in `prescore.py` response. | P82 |

## Final Verdict Table

| Prompt | Design Complete? | Impl Correct? | Response Complete? | Failed Requirements | Reclassify |
| ------------------------- | ---------------- | ------------- | ------------------ | ------------------- | ---------- |
| P84 TRD-AGENT-EVOLVER | NO | NO | PARTIAL | R2, R3, R4, R5, R6, R7 | SUPPLEMENT |
| P55 TRD-PATTERN-DETECTOR | PARTIAL | NO | PARTIAL | R3, R5, R8 | SUPPLEMENT |
| P82 TRD-REALTIME-SCORE | PARTIAL | NO | NO | R1, R2, R3, R4, R5, R7 | SUPPLEMENT |
| P53 TRD-TRUST-RADAR | NO | NO | NO | R1, R2, R3, R4, R5, R6, R7 | SUPPLEMENT |
| P83 TRD-PROMOTION-ENGINE | PARTIAL | NO | NO | R1, R2, R3, R5, R6, R8, R9 | SUPPLEMENT |
| P81 TRD-REGIME-CLASSIFIER | PARTIAL | PARTIAL | NO | R7, R9 | SUPPLEMENT |

Verdict key:

* CONFIRMED: all requirements pass, DROP remains DROP.
* INCOMPLETE-DESIGN(Rn): structure exists but missing scenario coverage.
* INCOMPLETE-IMPL(Rn): wrong threshold, formula, data source, persistence, or algorithm.
* PARTIAL-RESPONSE(Rn): endpoint exists but response omits required fields.
* FULL: implementation absent or unrelated.

## Diagnostic Limitations

* This diagnostic does not run tests.
* This diagnostic does not validate live yfinance connectivity.
* This diagnostic does not validate frontend rendering.
* This diagnostic does not validate E2E behavior.
* CONFIRMED means source-level spec compliance, not live-stack validation.

## Recommended Next Step

Run targeted SUPPLEMENT implementation prompts in this order:

1. P53 TRD-TRUST-RADAR, because the current endpoint is most likely to create false confidence while returning non-PD semantics.
2. P82 TRD-REALTIME-SCORE, because request/response schema and conservation warnings are externally visible.
3. P84 and P83, because evolution/promotion need exact dimensions, thresholds, and persistence contracts.
4. P81 and P55 for stricter response shape and threshold/scenario alignment.
