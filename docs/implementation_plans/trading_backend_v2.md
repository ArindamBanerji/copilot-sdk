# Trading Backend v2 Implementation Plan

## Executive Summary

Enhance the existing Trading backend without rewriting its structure. Preserve all existing endpoints and add richer ticker data, a 40-trade `trading_seed_v2.json`, an analytics cache derived from that seed, a new analytics endpoint, a new similar-trades endpoint, richer trade metadata storage, and focused tests for the new behavior.

No SDK, scoring core, generic backend, frontend, purchasing, dataops, GAE, SOC, S2P, or ci-platform files should be changed. The existing `apps/trading/backend/app/main.py` already mounts the Trading context router under `/api/context`, so new context endpoints should be implemented in the existing context router or an app-local helper imported by it.

## Source Contracts from Prompt 0

### Existing Endpoint Shapes

Existing context endpoints are implemented in `apps/trading/backend/app/context_router.py`:

- `GET /api/context/market-snapshot` returns the contents of `market_snapshot.json`.
- `GET /api/context/ticker/{ticker}` uppercases the ticker and returns a cached ticker object. Unknown tickers return:

```json
{
  "ticker": "ZZZZ",
  "price": null,
  "change_30d_pct": null,
  "volume": null,
  "source": "unknown"
}
```

- `GET /api/context/portfolio-summary` currently returns `portfolio_summary.json`.
- `POST /api/context/trade-metadata` currently requires `decision_id`, stores a filtered metadata record keyed by string decision id, and returns:

```json
{
  "decision_id": "decision-1",
  "metadata": {}
}
```

- `GET /api/context/trade-metadata` returns the full metadata object.

Existing non-context endpoints that must continue working:

- `GET /health`
- `POST /api/score`
- `POST /api/learn`
- `GET /api/fingerprint`
- `GET /api/trajectory`
- `GET /api/history`

### Existing Data Loader and Writer Patterns

The context router uses `_DATA_DIR = Path(__file__).resolve().parents[1] / "data"`. `_load_json(filename)` reads UTF-8 JSON from `_DATA_DIR`. `_write_json(filename, payload)` writes UTF-8 JSON with `indent=2` and `sort_keys=True`, creating the parent directory if needed.

Keep this pattern for new data files unless an app-local helper needs to share the same directory through a passed-in path.

### Existing Test Pattern and Metadata Isolation

`apps/trading/backend/tests/conftest.py` copies backend data files into a temporary `tmp_path / "data"` directory and monkeypatches `context_router._DATA_DIR` to that temp directory. It also creates an empty isolated `trade_metadata.json`.

Any new tests that need `trading_seed_v2.json` or `analytics_cache.json` must update this fixture to copy those files into temp data. Metadata tests should continue using the isolated temp `trade_metadata.json`, so source data is not mutated.

### Trading Preset Categories, Actions, and Factors

The Trading preset contract from `copilot_sdk/scoring/presets/trading.py` is:

- Categories: `equity_long`, `equity_short`, `crypto_spot`, `options`, `etf`
- Actions: `buy`, `hold`, `sell`
- Factors: `conviction`, `research_depth`, `technical_signal`, `position_size`, `time_horizon`, `market_regime`

The v2 seed should only use Trading preset categories and actions. The requested category distribution does not require `equity_short`, so it can remain unused.

## Files to Modify

- `apps/trading/backend/app/context_router.py`
- `apps/trading/backend/data/ticker_cache.json`
- `apps/trading/backend/data/portfolio_summary.json`
- `apps/trading/backend/data/trade_metadata.json`, only if a richer default fixture is needed
- `apps/trading/backend/tests/test_trading_backend.py`
- `apps/trading/backend/tests/conftest.py`, if needed to copy new data files into test temp data

## Files to Create

- `apps/trading/backend/data/trading_seed_v2.json`
- `apps/trading/backend/data/analytics_cache.json`

Optional, only if it keeps the router small and makes analytics testable:

- `apps/trading/backend/app/analytics.py`

Do not create unrelated scripts. If a helper module is added, keep it app-local and pure Python.

## Forbidden Files

- `apps/trading/backend/app/main.py`, unless router mounting is proven to require a change. Prompt 0 found no such need.
- `copilot_sdk/scoring/**`
- `copilot_sdk/backend/**`
- `copilot_sdk/frontend/**`
- `apps/purchasing/**`
- `apps/dataops/**`
- `GAE/**`
- `SOC/**`
- `S2P/**`
- `ci-platform/**`
- `graph-attention-engine-v50/**`
- `gen-ai-roi-demo-v4-v50/**`
- `s2p-copilot/**`

Do not use git operations.

## Ticker Cache Contract

Enhance every existing ticker cache entry with:

- `name`
- `sector`
- `market_cap_b`
- `above_50ma`
- `rsi`
- `vol_rank_pctl`

Preserve existing fields:

- `ticker`
- `price`
- `change_30d_pct`
- `source`
- `volume`, if present
- `category_hint`, already present in the current cache

Include all tickers from the current cache and current trading seed:

- AAPL
- BTC
- COIN
- ETH
- IWM
- META
- MSFT
- NVDA
- QQQ
- SPY
- TLT
- TSLA

Keep the unknown ticker fallback backward-compatible with existing tests.

## trading_seed_v2 Contract

Create `apps/trading/backend/data/trading_seed_v2.json` with exactly 40 trades. Each trade must include:

- `trade_id`
- `ticker`
- `direction`
- `category`
- `thesis_type`
- `timeframe`
- `research_checklist`
- `research_depth`
- `conviction`
- `technical_signal`
- `position_size`
- `time_horizon`
- `market_regime`
- `shares`
- `entry_price`
- `portfolio_value`
- `stop_loss`
- `target`
- `rr_ratio`
- `exit_price`
- `pnl_pct`
- `pnl_dollars`
- `hold_days`
- `outcome`
- `is_correct`
- `day_of_week`
- `date`
- `action_taken`
- `vix_at_entry`

Required data properties:

- 40 total trades.
- 3 open positions with `exit_price: null`, `outcome: null`, `pnl_pct: null`, and `pnl_dollars: null`.
- 37 closed trades.
- Around 67% closed-trade win rate. A concrete target is 25 wins out of 37 closed trades, or 67.57%.
- Factor values must be in `[0, 1]`.
- `action_taken` must match Trading actions: `buy`, `hold`, or `sell`.
- `category` must come from the Trading preset.
- Category counts across all 40 should be approximately:
  - `equity_long`: 24
  - `crypto_spot`: 6
  - `options`: 4
  - `etf`: 6
- Include enough similar clusters for the similar endpoint. Target at least 4 clusters of 3 or more trades with near-identical factor vectors so cosine similarity is greater than `0.85`.

Required story behavior:

- High research performs better than low research.
- High conviction is weak or noisy, not reliably predictive.
- Crypto trades are weaker despite conviction.
- Monday trades are weaker.
- Thursday trades are stronger.
- Mean-reversion trades are weaker.
- Defined stops improve outcomes or reduce loss size.

Recommended implementation detail:

- Store the six Trading factors as both top-level scalar fields and, if useful for similarity code, as a nested `factors` object. If both are present, tests should verify they stay consistent.

## Analytics Contract

`apps/trading/backend/data/analytics_cache.json` must be derived from `trading_seed_v2.json`. It must not be an independent hand-authored fixture.

Include these top-level keys:

- `contrast_card`
- `counterfactual`
- `calendar_heatmap`
- `thesis_breakdown`
- `regime_analysis`
- `research_impact`
- `portfolio_concentration`
- `rolling_10`
- `risk_management`
- `portfolio_summary`

Testing should recompute key summaries from `trading_seed_v2.json` and compare them to `analytics_cache.json`, including:

- Total trade count.
- Closed and open counts.
- Closed-trade win rate.
- Category counts where represented.
- `portfolio_summary` values.
- `counterfactual.dollars_saved > 0`.
- Research impact improves as research depth increases if the seed supports that ordering.

Prefer implementing analytics computation as a pure Python helper that takes parsed seed trades and returns a dict. This makes endpoint behavior and cache consistency testable without external dependencies.

## Portfolio Summary Contract

Avoid dual-source drift:

- Prefer `/api/context/portfolio-summary` reading `analytics_cache["portfolio_summary"]` when `analytics_cache.json` exists and contains that key.
- Preserve fallback behavior by returning `portfolio_summary.json` if analytics cache is missing or malformed.
- Ensure `apps/trading/backend/data/portfolio_summary.json` matches `analytics_cache.portfolio_summary` if the file remains present.

The generated summary should preserve existing fields where possible:

- `total_trades`
- `win_rate`
- `best_category`
- `worst_category`
- `gross_exposure`
- `cash_buffer`
- `source`

Add useful v2 fields only if tests and consumers need them:

- `closed_trades`
- `open_positions`
- `total_pnl_dollars`
- `total_pnl_pct`

## Metadata v2 Contract

Keep existing `POST /api/context/trade-metadata` and `GET /api/context/trade-metadata` routes and response shape.

Change storage from a fixed allowlist to accepting and storing arbitrary JSON fields keyed by `decision_id`. The only schema restriction should be that `decision_id` is required.

New v2 metadata fields include:

- `thesis_type`
- `timeframe`
- `research_checklist`
- `shares`
- `entry_price`
- `portfolio_value`
- `exposure_pct`
- `stop_loss`
- `target`
- `rr_ratio`
- `exit_price`
- `pnl_pct`
- `pnl_dollars`
- `hold_days`
- `outcome`

Backward compatibility requirements:

- Existing v1 fields must still round-trip: `ticker`, `direction`, `thesis`, `research`, `conviction`, `horizon`.
- Missing `decision_id` must still return HTTP 400 with a message containing `decision_id`.
- Return shape remains `{"decision_id": str(decision_id), "metadata": record}`.

## New Endpoints

### GET /api/context/analytics

Return `analytics_cache.json`.

Preferred behavior:

- If `analytics_cache.json` exists, return it.
- If missing, return a safe object with all expected top-level keys and `source: "default"` rather than failing the whole context surface. This matches the cached-context style, but tests should primarily exercise the present-file path.

Safe default shape:

```json
{
  "source": "default",
  "contrast_card": {},
  "counterfactual": {},
  "calendar_heatmap": {},
  "thesis_breakdown": {},
  "regime_analysis": {},
  "research_impact": {},
  "portfolio_concentration": {},
  "rolling_10": [],
  "risk_management": {},
  "portfolio_summary": {}
}
```

### GET /api/context/similar

Required query params:

- `category`
- `conviction`
- `research_depth`
- `technical_signal`
- `position_size`
- `time_horizon`
- `market_regime`

Optional query param:

- `n`, default `5`

Implementation requirements:

- Use pure Python cosine similarity. Do not use numpy.
- Read from `trading_seed_v2.json`.
- Compare the query vector against each seed trade's six Trading factors.
- Filter to matching `category`.
- Filter to `similarity > 0.85`.
- Sort by similarity descending.
- Return at most `n` rows in `similar`.
- Return `count` as total matches above threshold before `n` limiting.
- Handle open trades with `pnl_pct: null` safely.

Return shape:

```json
{
  "similar": [
    {
      "trade_id": "V2-001",
      "ticker": "NVDA",
      "thesis_type": "breakout",
      "timeframe": "swing",
      "research_depth": 0.92,
      "pnl_pct": 4.2,
      "outcome": "win",
      "is_correct": true,
      "similarity": 0.97
    }
  ],
  "count": 1
}
```

## Tests

Add these tests to `apps/trading/backend/tests/test_trading_backend.py` while keeping all existing tests passing:

- `test_ticker_enhanced_fields`
- `test_analytics`
- `test_analytics_consistent_with_seed_v2`
- `test_similar_trades`
- `test_trade_metadata_v2_fields`
- `test_seed_v2_exists`
- `test_portfolio_summary_matches_analytics`

Test expectations:

- `test_ticker_enhanced_fields`: known ticker includes all enhanced fields and preserves existing fields.
- `test_seed_v2_exists`: fixture data includes 40 trades, 3 open positions, allowed categories/actions, factors in range, and required fields.
- `test_analytics`: endpoint returns all required top-level keys.
- `test_analytics_consistent_with_seed_v2`: recompute counts, closed/open counts, win rate, and selected summaries from seed and compare to cache.
- `test_similar_trades`: query a known cluster vector and assert descending similarities, threshold `> 0.85`, limited row count, and expected response fields.
- `test_trade_metadata_v2_fields`: POST richer metadata and assert every v2 field round-trips.
- `test_portfolio_summary_matches_analytics`: `/portfolio-summary` equals or matches key fields from `analytics_cache["portfolio_summary"]`.

Fixture update:

- Copy `trading_seed_v2.json` and `analytics_cache.json` into temp data.
- Continue creating isolated `trade_metadata.json`.
- Keep temp SQLite db behavior unchanged.

## Validation Commands

Run from repo root:

```powershell
python -m pytest apps/trading/backend/tests/ -v --timeout=120
python -m pytest tests/ -q --timeout=120
```

If `pytest-timeout` is not installed and `--timeout` is rejected, rerun without the timeout flag and record that the plugin is unavailable:

```powershell
python -m pytest apps/trading/backend/tests/ -v
python -m pytest tests/ -q
```

## Prompt Verification Pass

- Existing endpoints are preserved; new endpoints are added under the existing context router.
- Analytics/seed drift is avoided by deriving `analytics_cache.json` from `trading_seed_v2.json` and testing consistency.
- Portfolio summary drift is avoided by preferring `analytics_cache["portfolio_summary"]` and keeping `portfolio_summary.json` in sync as fallback.
- No SDK/core edits are required.
- New tests cover new endpoints, richer metadata, seed existence, and analytics consistency.
- The plan is self-contained and constrained to Trading backend files plus this plan document.

## Residual Risks

- The prompt names `trading_seed_v2.json` but forbids `copilot_sdk/scoring/**`; therefore the seed must live in `apps/trading/backend/data/`.
- Exact analytics field internals are not already defined by existing code. The implementation must define stable shapes and then test them.
- The analytics safe-default behavior should not hide fixture mistakes in tests; tests should verify the real cache path.
- If future consumers expect `/portfolio-summary` to read only `portfolio_summary.json`, switching to analytics-first could be observable. Keep fallback and preserve summary keys.
