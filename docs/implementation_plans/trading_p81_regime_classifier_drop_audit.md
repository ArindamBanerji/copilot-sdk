# P81 TRD-REGIME-CLASSIFIER DROP Verification Audit

Date: 2026-06-07
Model: gpt-5.5
Task Type: SPEC COVERAGE AUDIT ONLY. NO IMPLEMENTATION CHANGES.
Repo: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
Design Doc: docs\design\trading_copilot_product_definition_v1.md

## Executive Summary
- P81 verdict: DROP CONFIRMED
- DROP CONFIRMED or SUPPLEMENT: DROP CONFIRMED
- Failed requirements: None for audited requirements A-J.
- Highest-risk gap: No source/spec gap found. Residual risk is runtime-only: this audit did not call yfinance, run API routes, or execute tests.
- Recommended next prompt: Run targeted non-mutating unit/API tests for the regime service and router with mocked yfinance data.

## Path Resolution
- Repo path: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
- Design doc found: YES, docs\design\trading_copilot_product_definition_v1.md
- regime.py found: YES, apps\trading\backend\app\services\regime.py
- regime_recommender.py found: YES, apps\trading\backend\app\services\regime_recommender.py
- routers/regime.py found: YES, apps\trading\backend\app\routers\regime.py
- implementation_plans path: YES, docs\implementation_plans

## CLAUDE.md Relevant Notes
- CLAUDE.md says docs are aspirational until proven in source and actual source files must be checked: CLAUDE.md:5.
- CLAUDE.md requires file and line citations for behavioral claims: CLAUDE.md:6.
- CLAUDE.md says code and tests beat docs when there is a discrepancy: CLAUDE.md:7.
- CLAUDE.md says not to use git directly: CLAUDE.md:53.
- CLAUDE.md recommends pytest after changes, but this prompt forbids pytest and no source changes were made: CLAUDE.md:8, CLAUDE.md:58.

## PD Requirements
- Requirement: A. classify_regime(vix, trend_strength) returns exactly trending, ranging, volatile.
  PD evidence: docs\design\trading_copilot_product_definition_v1.md:1139 defines `def classify_regime(vix: float, trend_strength: float) -> str`; docs\design\trading_copilot_product_definition_v1.md:1146-1147 says returns `"trending", "ranging", or "volatile"`.
  Implementation evidence: apps\trading\backend\app\services\regime.py:25-32 returns only `"volatile"`, `"ranging"`, and `"trending"`.
  Status: PRESENT
  Notes: Labels match the PD return set.

- Requirement: B. VIX > 30 returns volatile.
  PD evidence: docs\design\trading_copilot_product_definition_v1.md:1153 says `VIX > 30 -> volatile`; docs\design\trading_copilot_product_definition_v1.md:1161-1162 returns `"volatile"` when `vix > 30`.
  Implementation evidence: apps\trading\backend\app\services\regime.py:18 sets `DEFAULT_VIX_VOLATILE = 30.0`; apps\trading\backend\app\services\regime.py:26-27 returns `"volatile"` when `float(vix) > DEFAULT_VIX_VOLATILE`.
  Status: PRESENT
  Notes: Threshold matches exactly.

- Requirement: C. 20 < VIX <= 30 returns ranging.
  PD evidence: docs\design\trading_copilot_product_definition_v1.md:1152 says `VIX 20-30 -> ranging`; docs\design\trading_copilot_product_definition_v1.md:1163-1164 returns `"ranging"` when `vix > 20` after the `vix > 30` branch.
  Implementation evidence: apps\trading\backend\app\services\regime.py:19 sets `DEFAULT_VIX_RANGING = 20.0`; apps\trading\backend\app\services\regime.py:28-29 returns `"ranging"` when `float(vix) > DEFAULT_VIX_RANGING` after the volatile branch.
  Status: PRESENT
  Notes: Boundary behavior matches the PD code path.

- Requirement: D. VIX <= 20 and trend_strength > 25 returns trending.
  PD evidence: docs\design\trading_copilot_product_definition_v1.md:1150 says `VIX < 20 + ADX > 25 -> trending`; docs\design\trading_copilot_product_definition_v1.md:1165-1166 returns `"trending"` when `trend_strength > 25` after VIX checks.
  Implementation evidence: apps\trading\backend\app\services\regime.py:20 sets `DEFAULT_ADX_TRENDING = 25.0`; apps\trading\backend\app\services\regime.py:30-31 returns `"trending"` when `float(trend_strength) > DEFAULT_ADX_TRENDING`.
  Status: PRESENT
  Notes: The implementation uses `<= 20` because the `> 20` ranging branch has already been skipped, matching the prompt requirement and PD code.

- Requirement: E. VIX <= 20 and trend_strength <= 25 returns ranging.
  PD evidence: docs\design\trading_copilot_product_definition_v1.md:1151 says `VIX < 20 + ADX <= 25 -> ranging`; docs\design\trading_copilot_product_definition_v1.md:1167 returns `"ranging"` after the trend branch.
  Implementation evidence: apps\trading\backend\app\services\regime.py:30-32 returns `"ranging"` when trend strength is not greater than 25 after VIX checks.
  Status: PRESENT
  Notes: Boundary behavior matches the prompt requirement and PD code.

- Requirement: F. VIX is sourced from live yfinance ^VIX with graceful fallback.
  PD evidence: docs\design\trading_copilot_product_definition_v1.md:765-770 requires regime detection from VIX and says engineering is `VIX + trend classifier + historical mapping`; docs\design\trading_copilot_product_definition_v1.md:1143 identifies VIX as the current VIX level.
  Implementation evidence: apps\trading\backend\app\services\regime.py:9-15 imports yfinance and records availability; apps\trading\backend\app\services\regime.py:67-70 returns `_default()` if yfinance is unavailable; apps\trading\backend\app\services\regime.py:73 reads `yf.Ticker("^VIX").history(period="5d")`; apps\trading\backend\app\services\regime.py:75-78 and 96-99 fall back to `_default()` on empty data or exceptions.
  Status: PRESENT
  Notes: This audit did not call yfinance; source inspection confirms live yfinance path plus fallback.

- Requirement: G. ADX is computed from live OHLCV price data, not hardcoded.
  PD evidence: docs\design\trading_copilot_product_definition_v1.md:1144 says `trend_strength: ADX(14) or equivalent. >25 = trending`; docs\design\trading_copilot_product_definition_v1.md:765-770 says regime detection is from VIX, price action, and breadth.
  Implementation evidence: apps\trading\backend\app\services\regime.py:35 defines `compute_adx(highs, lows, closes, period=14)`; apps\trading\backend\app\services\regime.py:42-48 builds a high/low/close DataFrame and computes `ta.adx`; apps\trading\backend\app\services\regime.py:74 reads live ticker history, apps\trading\backend\app\services\regime.py:81-84 passes High/Low/Close arrays into `compute_adx`.
  Status: PRESENT
  Notes: The service has fallback defaults for insufficient data/import errors at apps\trading\backend\app\services\regime.py:37-50, but the primary path computes ADX from OHLCV arrays.

- Requirement: H. /regime returns current regime label plus accuracy_by_category.
  PD evidence: docs\design\trading_copilot_product_definition_v1.md:1296 lists `/api/trading/regime | GET | Current regime + trader accuracy | v1.0`.
  Implementation evidence: apps\trading\backend\app\routers\regime.py:27-37 defines GET `/regime`, calls `service.get_current_regime()` and `service.get_regime_accuracy(trades)`, and returns `"current"` and `"accuracy_by_category"`.
  Status: PRESENT
  Notes: The current regime label is nested under `current["regime"]`, populated by apps\trading\backend\app\services\regime.py:86-92.

- Requirement: I. /regime/detail returns per-category recommendations with action, delta_pp, and conservation_safe if implemented by recommender output.
  PD evidence: docs\design\trading_copilot_product_definition_v1.md:386-396 defines RegimeRecommender using current regime and regime accuracy; docs\design\trading_copilot_product_definition_v1.md:407-411 says compare current-regime accuracy to baseline and only recommend increases when conservation is GREEN; docs\design\trading_copilot_product_definition_v1.md:416-421 defines StrategyShift fields including current and baseline accuracy plus conservation status.
  Implementation evidence: apps\trading\backend\app\routers\regime.py:39-50 defines GET `/regime/detail` and returns `RegimeRecommender().recommend(...)`; apps\trading\backend\app\services\regime_recommender.py:35-41 returns `"recommendations"` and top-level `"conservation_safe"`; apps\trading\backend\app\services\regime_recommender.py:73-82 returns per-category `"delta_pp"` and `"action"`.
  Status: PRESENT
  Notes: `conservation_safe` is top-level for the recommendation set, not repeated per category. The prompt allows it if implemented by recommender output, and it is present in the output.

- Requirement: J. Accuracy is computed from actual journal/trade records, not hardcoded.
  PD evidence: docs\design\trading_copilot_product_definition_v1.md:386-392 says RegimeRecommender uses verified trade history segmented by regime and category; docs\design\trading_copilot_product_definition_v1.md:767-769 says regime maps to trader per-regime performance.
  Implementation evidence: apps\trading\backend\app\routers\regime.py:30 and 42 read `trades = _journal_records(...)`; apps\trading\backend\app\routers\journal.py:120-146 builds journal records from the in-memory trade store and graph store decisions; apps\trading\backend\app\services\regime.py:101-122 computes per-category/per-regime win rates from passed trades; apps\trading\backend\app\services\regime.py:186-198 derives wins from trade P&L fields.
  Status: PRESENT
  Notes: Historical trades with no recorded regime can be classified from historical VIX and default ADX at apps\trading\backend\app\services\regime.py:127-169. That is a fallback path, not hardcoded accuracy.

## Service Review - regime.py
- classify_regime signature: `def classify_regime(vix: float, trend_strength: float) -> str` at apps\trading\backend\app\services\regime.py:25.
- threshold constants: VIX volatile 30.0, VIX ranging 20.0, ADX trending 25.0 at apps\trading\backend\app\services\regime.py:18-20.
- VIX source: `yf.Ticker("^VIX").history(period="5d")` at apps\trading\backend\app\services\regime.py:73.
- VIX fallback: `_default()` when yfinance is unavailable, data is empty, or exceptions occur at apps\trading\backend\app\services\regime.py:67-70, 75-78, and 96-99.
- ADX source: `compute_adx` builds High/Low/Close data and calls `ta.adx` at apps\trading\backend\app\services\regime.py:35-48; current ticker High/Low/Close arrays are passed at apps\trading\backend\app\services\regime.py:81-84.
- get_regime_accuracy data source: caller passes journal records from router; service buckets trade category/regime/outcomes at apps\trading\backend\app\services\regime.py:101-122.
- hardcoded/default values: fallback VIX 20.0, ADX 20.0, and default regime `ranging` are defined at apps\trading\backend\app\services\regime.py:21-22 and 152-159; they are fallback values, not primary classifier thresholds or hardcoded accuracy.
- verdict: PRESENT for P81 service requirements.

## Service Review - regime_recommender.py
- recommend() output shape: returns `regime`, `recommendations`, `regime_transitions`, `conservation_safe`, `conservation_status`, and `summary` at apps\trading\backend\app\services\regime_recommender.py:35-41.
- action field: per-category recommendation returns `"action"` at apps\trading\backend\app\services\regime_recommender.py:73-82.
- delta_pp field: per-category recommendation computes and returns `"delta_pp"` at apps\trading\backend\app\services\regime_recommender.py:56 and 78.
- conservation_safe field: top-level output includes `"conservation_safe"` at apps\trading\backend\app\services\regime_recommender.py:39, computed from conservation status at apps\trading\backend\app\services\regime_recommender.py:20 and 141-157.
- data sources: uses the `accuracy` argument provided by the router from `RegimeService.get_regime_accuracy`; see apps\trading\backend\app\routers\regime.py:42-50.
- verdict: PRESENT for audited `/regime/detail` output requirements.

## Router Review - routers/regime.py
- /regime response fields: returns `"current"`, `"accuracy_by_category"`, and `"recommendations"` at apps\trading\backend\app\routers\regime.py:33-37.
- /regime/detail response fields: delegates to `RegimeRecommender().recommend(...)` at apps\trading\backend\app\routers\regime.py:39-50, whose output includes recommendation action/delta_pp and top-level conservation_safe.
- service calls: `/regime` and `/regime/detail` both instantiate `RegimeService`, read `_journal_records`, call `get_current_regime`, and call `get_regime_accuracy` at apps\trading\backend\app\routers\regime.py:29-32 and 41-44.
- hardcoded/default values: router fallback regime string is `"ranging"` if current payload lacks `regime`, at apps\trading\backend\app\routers\regime.py:36 and 47.
- verdict: PRESENT for P81 router requirements.

## Final Decision Table
Requirement | Status | Evidence | Gap If Any
A classify_regime returns exact labels | PRESENT | apps\trading\backend\app\services\regime.py:25-32 | None
B VIX > 30 volatile | PRESENT | apps\trading\backend\app\services\regime.py:18, 26-27 | None
C 20 < VIX <= 30 ranging | PRESENT | apps\trading\backend\app\services\regime.py:19, 28-29 | None
D VIX <= 20 and trend > 25 trending | PRESENT | apps\trading\backend\app\services\regime.py:20, 30-31 | None
E VIX <= 20 and trend <= 25 ranging | PRESENT | apps\trading\backend\app\services\regime.py:30-32 | None
F VIX from yfinance ^VIX with fallback | PRESENT | apps\trading\backend\app\services\regime.py:67-78, 96-99 | None
G ADX from live OHLCV | PRESENT | apps\trading\backend\app\services\regime.py:35-48, 74, 81-84 | None
H /regime returns label + accuracy_by_category | PRESENT | apps\trading\backend\app\routers\regime.py:27-37 | None
I /regime/detail returns action + delta_pp recommendations | PRESENT | apps\trading\backend\app\routers\regime.py:39-50; apps\trading\backend\app\services\regime_recommender.py:35-41, 73-82 | None
J accuracy from journal trade records | PRESENT | apps\trading\backend\app\routers\regime.py:30, 42; apps\trading\backend\app\routers\journal.py:120-146; apps\trading\backend\app\services\regime.py:101-122 | None

## Final Verdict
P81 TRD-REGIME-CLASSIFIER:
- Decision: DROP CONFIRMED
- Gaps: None found in audited source/spec coverage.
- Recommended targeted supplement, if needed: None for source/spec coverage. Recommended validation prompt only: run targeted mocked-yfinance unit/API tests for `classify_regime`, `compute_adx`, `RegimeService.get_current_regime`, `RegimeService.get_regime_accuracy`, and `/api/trading/regime` plus `/api/trading/regime/detail`.

## Audit Limitations
- This audit does not run tests.
- This audit does not call yfinance.
- This audit does not validate runtime API behavior.
- This audit does not modify code.
- DROP CONFIRMED means source/spec coverage appears complete for audited requirements, not that E2E validation passed.
