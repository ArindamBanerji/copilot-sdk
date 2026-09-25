# Trading SAFE-2 Re-verification Report

**Date:** 2026-09-17  
**Tensor validated:** `(5, 4, 10) = 200`  
**Factor count:** 10  
**Scope:** Trading backend, scorer preset, bootstrap/checkpoint state, frontend, E2E, live API, and repository documentation.

## Canonical Trading shape

The canonical factor order is:

1. `signal_alignment`
2. `market_regime`
3. `position_sizing`
4. `timing_quality`
5. `risk_reward_actual`
6. `emotional_indicator`
7. `signal_confidence`
8. `options_delta_exposure`
9. `options_iv_percentile`
10. `options_gamma_risk`

The scorer preset reports five categories, four actions, and ten factors; its tensor shape is `(5, 4, 10)`.

## Cross-reference matrix

| Source | Location | C | A | d | Factor names match? | Status |
|---|---|---:|---:|---:|---|---|
| Domain configuration | `apps/trading/backend/app/domains/trading_config.py` | 5 | 4 | 10 | Yes | PASS |
| Scorer preset | `copilot_sdk/scoring/presets/trading.py:38-67` | 5 | 4 | 10 | Yes | PASS |
| Bootstrap centroids | `copilot_sdk/scoring/presets/trading_bootstrap.json` | 5 | 4 | 10 | N/A | PASS; direct array shape verified |
| App-local checkpoint | `apps/trading/backend/data/trading.db` | 5 | 4 | 10 | N/A | PASS; latest three checkpoints verified |
| Frontend types | `apps/trading/frontend/src/types.ts` | — | — | — | Compatible | PASS; factor maps are dynamic/generic and do not encode a stale dimension |
| Frontend components | `apps/trading/frontend/src/components/PreScorePanel.tsx`, `screens/DashboardScreen.tsx`, `screens/LogTradeScreen.tsx` | — | — | 10 | Yes | PASS; all ten appear in the canonical pre-score/dashboard views |
| E2E assertions | `e2e/trading/pre-score.spec.ts`, `trust-radar.spec.ts`, `options-factors.spec.ts` | — | — | 10 | Yes | PASS; ten-factor payload and names are exercised |
| Live API fingerprint | `http://127.0.0.1:8010/api/fingerprint` | — | — | 10 | Yes | PASS; ten names returned |
| Live API health | `http://127.0.0.1:8010/api/health` | — | — | — | N/A | PASS; phase/engine healthy; health does not expose tensor dimensions |
| Design documentation | `docs/` (479 Markdown files scanned) | — | — | 10 | Mixed historical/current | PASS after current-state corrections below |

## Backend and persisted geometry evidence

`TradingPreset().shape` produced:

- Categories: `trend_following`, `mean_reversion`, `event_driven`, `income_strategy`, `scalp_intraday` (5)
- Actions: `strong_execution`, `partial_execution`, `poor_execution`, `skip_recommended` (4)
- Factors: the canonical ten-factor list above (10)
- Tensor shape: `(5, 4, 10)`

The bootstrap array was independently loaded with NumPy and returned shape `(5, 4, 10)`. The latest three read-only SQLite checkpoint rows in `trading.db` also returned `(5, 4, 10)`.

## Frontend and E2E evidence

The frontend types use generic factor records for API responses and therefore do not hard-code a conflicting factor count. The canonical `PreScorePanel` declares all ten factor keys. Other panels intentionally render subsets or user-facing aliases for specialized views; these are presentation subsets, not tensor declarations.

The Trading E2E suite contains 55 spec files. The pre-score fixture posts all ten canonical factor keys; trust-radar and options-factor specs exercise the corresponding factor names. No E2E assertion was found that incorrectly asserts `(5,3,6)` or `(5,4,7)` as the live Trading tensor. The five-count `data-trust-factor` assertion is a UI trust-category count, not the tensor factor dimension.

## Live API evidence

All five configured backend health endpoints responded successfully during the audit, including Trading on port 8010.

Trading `/api/fingerprint` returned ten factor records in canonical order:

`signal_alignment`, `market_regime`, `position_sizing`, `timing_quality`, `risk_reward_actual`, `emotional_indicator`, `signal_confidence`, `options_delta_exposure`, `options_iv_percentile`, `options_gamma_risk`.

Trading `/api/health` returned phase `B`, alpha `0.9972`, and the expected `ProfileScorer`/`CompoundingScorer` engine entries. It does not publish tensor metadata, so shape evidence is taken from the preset, persisted centroids, and fingerprint endpoint.

## Documentation references audited

There are 479 Markdown files under `docs/`. Of these, 43 contain one or more explicit Trading/general shape tokens; 40 contain legacy `(5,3,6)` or `(5,4,7)` tokens. The legacy references fall into two classes:

1. Historical product plans, migration notes, dated diagnostics, and compatibility examples. These were retained as historical evidence and are not claims about the live runtime.
2. Current-state tables or unqualified runtime statements. These were corrected or annotated.

Corrections applied during this re-verification:

- `docs/bootstrap_shape_diagnostic.md`: added the superseding 2026-09-17 runtime result, changed the Trading bootstrap status to `(5,4,10)` PASS, and marked the May snapshot as historical.
- `docs/plan_sdk_apps_state.md`: corrected the Trading tensor row to `(5,4,10)`.
- `docs/design/product/trading_copilot_product_definition_v1_1_corrected.md`: clarified that `(5,3,6)` is historical migration context and the live runtime is `(5,4,10)=200`.
- `docs/design/ci_reviews_and_addenda/final_addenda/trading_copilot_addendum_FINAL_v1.md`: added the same runtime supersession note so its prototype reference is not confused with production.

## Test evidence

- Trading backend: **1,452 passed** (`python -m pytest apps/trading/backend/tests/ -q --timeout=120`).
- Trading frontend TypeScript: **PASS** (`npx tsc --noEmit`).
- Trading frontend production build: **PASS** (`npm run build`).
- E2E TypeScript compilation: **PASS** (`e2e`, `npx tsc --noEmit`).
- SDK root test suite: **3,503 passed** (`python -m pytest tests/ -q --timeout=120`).

## Mismatches found

Two unqualified current-state documentation claims were stale, and two current product documents needed explicit supersession annotations. No backend, scorer-preset, bootstrap, checkpoint, frontend type, E2E factor payload, or live API mismatch was found.

## Fixes applied

Four documentation-only corrections/annotations were applied. No source-of-truth Python file, Trading backend file, frontend TypeScript file, or E2E assertion required modification.

## Verdict

**Trading SAFE-2: VERIFIED against `(5,4,10)=200`; 10 factors confirmed across the backend preset, bootstrap/checkpoint state, frontend canonical views, E2E payloads, and live API.**

Evidence scope: 10 runtime/source cross-reference rows, 479 Markdown files scanned, 43 shape-reference documents inspected, 1,452 Trading backend tests passing, frontend TypeScript/build passing, and E2E TypeScript compilation passing. Historical `(5,3,6)` and `(5,4,7)` references remain only where they document prior product/migration states or compatibility behavior.
